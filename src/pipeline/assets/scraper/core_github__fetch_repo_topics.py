import typing as _t
import os
import uuid
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from dagster import (
    asset,
    AssetIn,
    AssetKey,
    MetadataValue,
    Output,
)
from .utils import (
    _extract_owner_repo,
    _fetch_repo_topics,
    _make_serializable,
)
from src.services.python.db import get_db_cursor
import json

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

@asset(
    kinds={"python", "postgres"},
    owners=DEFAULT_OWNERS,
    # Depends on detection (to filter topics)
    ins={"core_github__detect_languages": AssetIn(key=AssetKey(["ost", "int_github_detection"]))},
    group_name="ingestion",
    key=AssetKey(["ost", "raw_github_topics"]), # Matches dbt source
    required_resource_keys={"config"},
)
def core_github__fetch_repo_topics(context, core_github__detect_languages: _t.List[_t.Dict]):
    """
    Fetch GitHub /topics for each project.

    **Description:**
    Retrieves the repository topics (tags) for each project from GitHub API.

    **Logic:**
    1. **Setup**: Configures GitHub token and thread pool.
    2. **Parallel Fetching**: Submits requests to GitHub API `topics` endpoint (mercy-preview).
    3. **Error Handling**: Returns empty list on failure.

    **Output:**
    List of dictionaries containing project metadata and list of topics.
    """
    context.log.info(f"core_github__fetch_repo_topics: Starting fetch for {len(core_github__detect_languages) if core_github__detect_languages else 0} projects")
    if not core_github__detect_languages:
        return Output(value=[], metadata={"count": MetadataValue.int(0)})

    token = getattr(context.resources.config, "github_token", None) or os.environ.get("GITHUB_ACCESS_TOKEN")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    results = []
    session = requests.Session()
    max_workers = int(getattr(context.resources.config, "github_fetch_workers", 8))
    # Cap concurrency to avoid SQLite locking in Dagster's event log.
    max_workers = max(1, min(max_workers, 4))

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {}
        for proj in core_github__detect_languages:
            repo_url = proj.get("url") or proj.get("repoUrl")
            owner_repo = _extract_owner_repo(repo_url) if repo_url else None
            if owner_repo:
                owner, repo = owner_repo
                futures[ex.submit(_fetch_repo_topics, owner, repo, headers, session)] = {"project": proj, "repoUrl": repo_url}
        for fut in as_completed(futures):
            meta = futures[fut]
            try:
                topics = fut.result()
            except Exception as e:
                context.log.warning(f"fetch topics failed: {e}")
                topics = []
            out = {"project": meta["project"], "repoUrl": meta["repoUrl"], "topics": topics}
            results.append(out)

    # Insert topics into raw_github_topics
    try:
        with get_db_cursor(commit=True) as cur:
            for item in results:
                proj_id = item["project"].get("id")
                if not proj_id: continue
                # Delete existing record first to simulate upsert without unique constraint
                cur.execute(
                    'DELETE FROM "github"."raw_github_topics" WHERE "project_id" = %s',
                    (proj_id,)
                )
                cur.execute(
                    """
                    INSERT INTO "github"."raw_github_topics" ("id", "project_id", "repo_url", "topics", "created_at")
                    VALUES (%s, %s, %s, %s, NOW())
                    """,
                    (str(uuid.uuid4()), proj_id, item["repoUrl"], json.dumps(item["topics"]))
                )
            context.log.info(f"Inserted {len(results)} topic records into raw_github_topics.")
    except Exception as e:
        context.log.error(f"Failed to insert topic records: {e}")
    sample = results[:3]
    sample_repo_urls = [r.get("repoUrl") for r in sample]
    sample_topics = [r.get("topics") for r in sample]
    meta = {
        "count": MetadataValue.int(len(results)),
        "sample": MetadataValue.json(_make_serializable(sample)),
        "sample_repo_urls": MetadataValue.json(_make_serializable(sample_repo_urls)),
        "sample_topics": MetadataValue.json(_make_serializable(sample_topics)),
    }
    return Output(value=results, metadata=meta)
