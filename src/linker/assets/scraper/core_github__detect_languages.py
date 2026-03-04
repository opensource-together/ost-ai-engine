import re
import uuid
from typing import Any

import pandas as pd

from dagster import (
    AssetExecutionContext,
    AssetIn,
    AssetKey,
    MetadataValue,
    Output,
    asset,
)
from src.services.python.db import get_db_cursor

DEFAULT_OWNERS = ["team:OST/spideyai-X"]


@asset(
    kinds={"python", "postgres"},
    owners=DEFAULT_OWNERS,
    # Read from dbt staging model
    ins={"stg_df": AssetIn(key=AssetKey(["github", "stg_github__project"]))},
    group_name="ingestion",
    key=AssetKey(["github", "int_github_detection"]),  # Matches dbt source
    required_resource_keys={"config", "fasttext_model"},
)
def core_github__detect_languages(
    context: AssetExecutionContext,
    stg_df: pd.DataFrame,
) -> Output[None]:
    """
    Detects and filters repositories based on language using fastText.
    Reads from dbt staging table `stg_github__project`.
    Output: List of repository dictionaries with added language metadata.
    """
    context.log.info("core_github__detect_languages: Starting language detection")

    # Use DataFrame from IO Manager
    projects = stg_df.to_dict("records")
    context.log.info(f"Fetched {len(projects)} projects from staging.")

    # Get the fastText model from Dagster resources (loaded once, reused across runs)
    context.log.info("core_github__detect_languages: Accessing fasttext model...")
    fasttext_resource = context.resources.fasttext_model
    model = fasttext_resource.model
    context.log.info("core_github__detect_languages: Fasttext model accessed.")

    # Blacklist of language codes using non-Latin scripts or languages the pipeline
    # should exclude (Arabic, CJK, Japanese, Korean, many Indic languages...)
    NON_LATIN_LANGS = {
        "ar",
        "zh",
        "ja",
        "ko",
        "hi",
        "bn",
        "ta",
        "te",
        "kn",
        "ml",
        "gu",
        "mr",
        "pa",
        "or",
        "si",
        "ne",
        "my",
        "ru",
    }

    # Regex to detect non-Latin script characters directly in text
    # (CJK, Arabic, Devanagari, Bengali, Tamil, Hangul, etc.)
    NON_LATIN_CHAR_RE = re.compile(
        r"[\u4E00-\u9FFF"  # CJK Unified Ideographs
        r"\u3040-\u30FF"  # Hiragana + Katakana
        r"\uAC00-\uD7AF"  # Hangul
        r"\u0590-\u05FF"  # Hebrew
        r"\u0600-\u06FF"  # Arabic
        r"\u0900-\u097F"  # Devanagari
        r"\u0980-\u09FF"  # Bengali
        r"\u0B80-\u0BFF"  # Tamil
        r"\u0C00-\u0C7F"  # Telugu
        r"\u0C80-\u0CFF"  # Kannada
        r"\u0D00-\u0D7F"  # Malayalam
        r"]"
    )

    accepted: list[dict] = []
    filtered_out_projects: list[dict] = []

    context.log.info("core_github__detect_languages: Starting loop...")
    for i, repo in enumerate(projects):
        if i % 100 == 0:
            context.log.info(f"core_github__detect_languages: Processing item {i}...")

        # Build text to detect language from several possible fields
        # Note: repo is a dict from query_raw, keys are column names
        text_parts = []
        for key in ("readme", "description", "name"):  # stg doesn't have combined_text
            v = repo.get(key)
            if isinstance(v, str) and v.strip():
                text_parts.append(v.strip())
        text = "\n".join(text_parts)[:20000]

        # Default annotations
        repo["language_detected"] = None
        repo["language_confidence"] = 0.0

        # If text contains non-Latin script characters -> immediate filter
        if text and NON_LATIN_CHAR_RE.search(text):
            filtered_out_projects.append(
                {
                    "id": repo.get("id"),
                    "name": repo.get("name"),
                    "reason": "non_latin_script",
                }
            )
            continue

        # If no text to analyze, keep but with null language
        if not text:
            accepted.append(repo)
            continue

        # Use fastText top-k predictions
        lang_code = None
        confidence = 0.0
        try:
            labels, probs = model.predict(text.replace("\n", " "), k=3)
            labels_list = list(labels) if labels is not None else []
            probs_list = list(probs) if probs is not None else []
            preds = []
            for label, pr in zip(labels_list, probs_list, strict=False):
                if isinstance(label, bytes):
                    try:
                        label = label.decode("utf-8")
                    except Exception:
                        label = str(label)
                if isinstance(label, str):
                    code = label.replace("__label__", "").strip()
                    try:
                        pr_val = float(pr)
                    except Exception:
                        pr_val = 0.0
                    preds.append((code, pr_val))

            if preds:
                lang_code, confidence = preds[0]

            # Check for blacklisted languages with significant confidence (> 30%)
            blacklisted_found = None
            for code, score in preds:
                if code in NON_LATIN_LANGS and score >= 0.3:
                    blacklisted_found = (code, score)
                    break

            if blacklisted_found:
                b_code, b_score = blacklisted_found
                filtered_out_projects.append(
                    {
                        "id": repo.get("id"),
                        "name": repo.get("name"),
                        "reason": "blacklisted_lang",
                        "lang": b_code,
                        "score": b_score,
                        "all_langs": preds,
                    }
                )
                continue
        except Exception as e:
            context.log.warning(f"fastText prediction failed for repo index {i}: {e}")

        # Annotate and accept
        repo["language_detected"] = lang_code
        repo["language_confidence"] = confidence

        accepted.append(repo)

    # Insert detection results into int_github_detection
    try:
        with get_db_cursor(commit=True) as cur:
            for repo in accepted:
                cur.execute(
                    """
                    INSERT INTO "github"."int_github_detection"
                    ("id", "project_id", "repo_url",
                     "language_detected", "language_confidence",
                     "created_at")
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    ON CONFLICT ("project_id") DO UPDATE
                    SET "language_detected" = EXCLUDED."language_detected",
                        "language_confidence" = EXCLUDED."language_confidence",
                        "repo_url" = EXCLUDED."repo_url",
                        "created_at" = NOW()
                    """,
                    (
                        str(uuid.uuid4()),
                        repo.get("id"),
                        repo.get("url"),
                        repo.get("language_detected"),
                        repo.get("language_confidence"),
                    ),
                )
            context.log.info(
                f"Inserted {len(accepted)} detection records into int_github_detection."
            )
    except Exception as e:
        context.log.error(f"Failed to insert detection records: {e}")

    # Build helpful metadata for debugging
    lang_counts: dict = {}
    for r in accepted:
        k = r.get("language_detected") or "<none>"
        lang_counts[k] = lang_counts.get(k, 0) + 1

    # Helper to serialize datetime objects for metadata
    def _make_serializable(obj: Any) -> Any:
        import datetime
        import uuid

        if isinstance(obj, datetime.date | datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, dict):
            return {k: _make_serializable(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_make_serializable(v) for v in obj]
        return obj

    # Create a clean sample with only requested fields
    raw_sample = accepted[:1]
    clean_sample = []
    for item in raw_sample:
        clean_item = {
            "id": item.get("id"),
            "name": item.get("name"),
            "lang_detected": item.get("language_detected"),
            "lang_confidence": item.get("language_confidence"),
            # Add description if useful, but user wanted minimal
            "description": (item.get("description") or "")[:50] + "..."
            if item.get("description")
            else None,
        }
        clean_sample.append(clean_item)

    sample = _make_serializable(clean_sample)
    filtered = _make_serializable(filtered_out_projects)
    meta = {
        "input_count": MetadataValue.int(len(projects)),
        "output_count": MetadataValue.int(len(accepted)),
        "filtered_out_count": MetadataValue.int(len(filtered_out_projects)),
        "filtered_out_percent": MetadataValue.float(
            round(100 * len(filtered_out_projects) / len(projects), 2)
            if projects
            else 0.0
        ),
        "filtered_projects": MetadataValue.json(filtered),
        "sample": MetadataValue.json(sample),
        "language_counts": MetadataValue.json(lang_counts),
    }
    context.log.info(
        f"detect_languages: kept {len(accepted)} / {len(projects)} projects"
    )
    return Output(value=None, metadata=meta)
