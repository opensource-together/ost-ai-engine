import typing as _t
import os
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
    _fetch_readme,
    _make_serializable,
)
from src.services.python.db import get_db_cursor

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

@asset(
    kinds={"python", "postgres"},
    owners=DEFAULT_OWNERS,
    ins={"core_github__detect_languages": AssetIn(key=AssetKey(["ost", "raw_github_detection"]))},
    group_name="fetch_projects_metadatas",
    key=AssetKey(["ost", "raw_github_readme"]), # Matches dbt source
    required_resource_keys={"config"},
)
def core_github__fetch_readme(context, core_github__detect_languages: _t.List[_t.Dict]):
    """
    Fetch GitHub /readme for each project.

    **Description:**
    Retrieves the README content for each mapped project to be used for embedding generation.

    **Logic:**
    1. **Setup**: Configures GitHub token and thread pool.
    2. **Parallel Fetching**: Submits requests to GitHub API for each project.
    3. **Error Handling**: Captures failures and returns empty string for missing READMEs.

    **Output:**
    List of dictionaries containing project metadata and README content.
    """
    context.log.info(f"core_github__fetch_readme: Starting fetch for {len(core_github__detect_languages) if core_github__detect_languages else 0} projects")
    if not core_github__detect_languages:
        return Output(value=[], metadata={"count": MetadataValue.int(0)})

    token = getattr(context.resources.config, "github_token", None) or os.environ.get("GITHUB_ACCESS_TOKEN")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    results = []
    session = requests.Session()
    max_workers = int(getattr(context.resources.config, "github_fetch_workers", 8))
    # Limit the number of concurrent threads to reduce contention on Dagster's
    # SQLite event log (concurrent thread logging can cause sqlite locking
    # errors). Keep at least 1 worker but cap to a conservative value.
    max_workers = max(1, min(max_workers, 4))

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {}
        for proj in core_github__detect_languages:
            repo_url = proj.get("url") or proj.get("repoUrl")
            if not repo_url:
                context.log.warning(f"Project missing URL: {proj.keys()}")
            owner_repo = _extract_owner_repo(repo_url) if repo_url else None
            if not owner_repo and repo_url:
                context.log.warning(f"Failed to extract owner/repo from: {repo_url}")
            if owner_repo:
                owner, repo = owner_repo
                futures[ex.submit(_fetch_readme, owner, repo, headers, session)] = {"project": proj, "repoUrl": repo_url}
        for fut in as_completed(futures):
            meta = futures[fut]
            try:
                readme = fut.result()
            except Exception as e:
                context.log.warning(f"fetch readme failed: {e}")
                readme = ""
            # Truncate readme to avoid OOM/SIGBUS on large files (limit to 50KB)
            if len(readme) > 50000:
                readme = readme[:50000]
            out = {"project": meta["project"], "repoUrl": meta["repoUrl"], "readme": readme}
            results.append(out)

    # Insert readmes into raw_github_readme
    try:
        with get_db_cursor(commit=True) as cur:
            for item in results:
                proj_id = item["project"].get("id")
                if not proj_id: continue
                cur.execute(
                    """
                    INSERT INTO "github"."raw_github_readme" ("project_id", "repo_url", "content", "created_at")
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT ("project_id") DO UPDATE
                    SET "content" = EXCLUDED."content",
                        "repo_url" = EXCLUDED."repo_url",
                        "created_at" = NOW()
                    """,
                    (proj_id, item["repoUrl"], item["readme"])
                )
            context.log.info(f"Inserted {len(results)} readme records into raw_github_readme.")
    except Exception as e:
        context.log.error(f"Failed to insert readme records: {e}")

    sample = results[:3]
    sample_repo_urls = [r.get("repoUrl") for r in sample]
    meta = {
        "count": MetadataValue.int(len(results)),
        "sample": MetadataValue.json(_make_serializable(sample)),
        "sample_repo_urls": MetadataValue.json(_make_serializable(sample_repo_urls)),
    }
    return Output(value=results, metadata=meta)
