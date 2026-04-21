from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import pandas as pd
from dagster import AssetExecutionContext, AssetIn, AssetKey, Output, asset

from src.linker.resources.llm_classifier_resource import (
    ClassificationResult,
    RateLimitError,
)
from src.services.python.db import get_db_cursor

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

# Parallelism & DLQ tuning (conservative — Mistral free tier tolerates ~5 concurrent)
_MAX_WORKERS = 5
_DLQ_MAX_ATTEMPTS = 5
_DLQ_BACKOFF_BASE_HOURS = 2  # exponential: 2h, 4h, 8h, 16h, 32h, capped at 7d
_DLQ_BACKOFF_CAP_HOURS = 24 * 7

# Rough Mistral Small pricing ($/1M tokens, as of 2026-04) — ballpark only.
_COST_INPUT_PER_M = 0.20
_COST_OUTPUT_PER_M = 0.60


def _compute_next_retry(attempts: int) -> datetime:
    hours = min(_DLQ_BACKOFF_BASE_HOURS * (2 ** (attempts - 1)), _DLQ_BACKOFF_CAP_HOURS)
    return datetime.now(UTC) + timedelta(hours=hours)


def _upsert_failure(cur: Any, project_id: str, error: str) -> None:
    truncated = error[:2000]
    cur.execute(
        """
        INSERT INTO match.project_classification_failure
            ("projectId", attempts, "lastError", "lastAttemptAt", "nextRetryAt")
        VALUES (%s, 1, %s, now(), %s)
        ON CONFLICT ("projectId") DO UPDATE SET
            attempts = match.project_classification_failure.attempts + 1,
            "lastError" = EXCLUDED."lastError",
            "lastAttemptAt" = now(),
            "nextRetryAt" = %s
        """,
        (project_id, truncated, _compute_next_retry(1), _compute_next_retry(2)),
    )


def _classify_one(
    llm: Any, project: dict[str, Any], cat_names: list[str], dom_names: list[str]
) -> tuple[dict[str, Any], ClassificationResult | None, Exception | None]:
    try:
        result = llm.classify_project(
            title=project["title"],
            project_context=project.get("context") or "",
            categories=cat_names,
            domains=dom_names,
        )
        return project, result, None
    except Exception as e:
        return project, None, e


@asset(
    kinds={"python"},
    owners=DEFAULT_OWNERS,
    ins={"projects_df": AssetIn(key=AssetKey(["github", "fct_github_project"]))},
    group_name="classification",
    required_resource_keys={"llm_classifier"},
    io_manager_key="fs_io_manager",
)
def core_match__classify_projects(
    context: AssetExecutionContext,
    projects_df: pd.DataFrame,
) -> Output[list[dict[str, Any]]]:
    """Classifies GitHub projects into Categories and Domains via LLM.

    Parallelizes LLM calls via ThreadPoolExecutor.
    Failures are routed to `match.project_classification_failure` with exponential
    backoff so we don't burn budget re-classifying the same broken projects forever.
    Asset metadata reports token usage and estimated cost per run.
    """
    llm = context.resources.llm_classifier

    with get_db_cursor() as cur:
        cur.execute('SELECT "id", "name" FROM "public"."Category"')
        categories_map = {row["name"]: row["id"] for row in cur.fetchall()}

        cur.execute('SELECT "id", "name" FROM "public"."Domain"')
        domains_map = {row["name"]: row["id"] for row in cur.fetchall()}

        cur.execute('SELECT "projectId" FROM "match"."project_classification"')
        classified_ids = {str(row["projectId"]) for row in cur.fetchall()}

        cur.execute(
            """SELECT "projectId", attempts
               FROM "match"."project_classification_failure"
               WHERE "nextRetryAt" > now() OR attempts >= %s""",
            (_DLQ_MAX_ATTEMPTS,),
        )
        dlq_skip = {str(row["projectId"]) for row in cur.fetchall()}

    projects: list[dict[str, Any]] = cast(
        list[dict[str, Any]], projects_df.to_dict("records")
    )
    for p in projects:
        if "name" in p and "title" not in p:
            p["title"] = p["name"]

    total_before = len(projects)
    projects = [
        p
        for p in projects
        if str(p.get("id")) not in classified_ids
        and str(p.get("id")) not in dlq_skip
        and p.get("title")
    ]
    context.log.info(
        f"Loaded {total_before} projects; "
        f"{total_before - len(projects)} skipped "
        f"(already classified or under DLQ cooldown); "
        f"{len(projects)} to classify."
    )

    if not projects:
        return Output(value=[], metadata={"count": 0})

    cat_names = list(categories_map.keys())
    dom_names = list(domains_map.keys())

    results_payload: list[dict[str, Any]] = []
    total_prompt_tokens = 0
    total_completion_tokens = 0
    failures: list[tuple[str, str]] = []
    unknown_labels = 0
    rate_limit_hits = 0

    total = len(projects)
    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
        futures = {
            pool.submit(_classify_one, llm, p, cat_names, dom_names): p
            for p in projects
        }
        for idx, future in enumerate(as_completed(futures), start=1):
            project, result, error = future.result()
            title = str(project.get("title", ""))[:60]

            if error is not None:
                if isinstance(error, RateLimitError):
                    rate_limit_hits += 1
                failures.append(
                    (str(project["id"]), f"{type(error).__name__}: {error}")
                )
                context.log.error(f"[{idx}/{total}] '{title}' failed: {error}")
                continue

            if result is None:
                failures.append((str(project["id"]), "no result and no error"))
                continue

            total_prompt_tokens += result.prompt_tokens
            total_completion_tokens += result.completion_tokens

            cat_id = categories_map.get(result.category or "")
            dom_id = domains_map.get(result.domain or "")
            if cat_id or dom_id:
                results_payload.append(
                    {
                        "project": project,
                        "classification": {
                            "categoryId": cat_id,
                            "domainId": dom_id,
                            "categoryName": result.category,
                            "domainName": result.domain,
                            "modelVersion": result.model,
                        },
                    }
                )
                if idx % 10 == 0 or idx == total:
                    context.log.info(
                        f"Progress: {idx}/{total} processed "
                        f"({len(results_payload)} classified, {len(failures)} failed)"
                    )
            else:
                unknown_labels += 1
                failures.append(
                    (
                        str(project["id"]),
                        f"unknown labels: cat='{result.category}' "
                        f"dom='{result.domain}'",
                    )
                )
                context.log.warning(
                    f"[{idx}/{total}] Unknown labels for '{title}': "
                    f"cat='{result.category}' dom='{result.domain}'"
                )

    if failures:
        with get_db_cursor() as cur:
            for project_id, error_msg in failures:
                _upsert_failure(cur, project_id, error_msg)

    estimated_cost_usd = round(
        (total_prompt_tokens / 1_000_000) * _COST_INPUT_PER_M
        + (total_completion_tokens / 1_000_000) * _COST_OUTPUT_PER_M,
        4,
    )

    context.log.info(
        f"Classified {len(results_payload)}/{total}. "
        f"Failures routed to DLQ: {len(failures)} "
        f"(rate-limited: {rate_limit_hits}, unknown labels: {unknown_labels}). "
        f"Tokens: in={total_prompt_tokens} out={total_completion_tokens} "
        f"est cost ~${estimated_cost_usd}."
    )

    return Output(
        value=results_payload,
        metadata={
            "count": len(results_payload),
            "failed": len(failures),
            "rate_limit_hits": rate_limit_hits,
            "unknown_labels": unknown_labels,
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens,
            "estimated_cost_usd": estimated_cost_usd,
            "model_version": llm.model_id,
            "max_workers": _MAX_WORKERS,
            "preview": [str(x["project"]["title"]) for x in results_payload[:10]],
        },
    )
