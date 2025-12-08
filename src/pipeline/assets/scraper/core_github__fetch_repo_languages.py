import typing as _t
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from dagster import (
    asset,
    AssetIn,
    MetadataValue,
    Output,
)
from .utils import (
    _extract_owner_repo,
    _fetch_repo_languages,
)

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

@asset(
    kinds={"python"},
    owners=DEFAULT_OWNERS,
    ins={"core_github__detect_languages": AssetIn()},
    group_name="fetch_projects_metadatas",
    required_resource_keys={"config"},
)
def core_github__fetch_repo_languages(context, core_github__detect_languages: _t.List[_t.Dict]):
    """
    Fetch GitHub /languages for each project.

    **Description:**
    Retrieves the language breakdown for each project from GitHub API.

    **Logic:**
    1. **Setup**: Configures GitHub token and thread pool.
    2. **Parallel Fetching**: Submits requests to GitHub API `languages` endpoint.
    3. **Error Handling**: Returns empty list on failure.

    **Output:**
    List of dictionaries containing project metadata and list of languages.
    """
    context.log.info(f"core_github__fetch_repo_languages: Starting fetch for {len(core_github__detect_languages) if core_github__detect_languages else 0} projects")
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
                futures[ex.submit(_fetch_repo_languages, owner, repo, headers, session)] = {"project": proj, "repoUrl": repo_url}
        for fut in as_completed(futures):
            meta = futures[fut]
            try:
                langs = fut.result()
            except Exception as e:
                context.log.warning(f"fetch languages failed: {e}")
                langs = []
            out = {"project": meta["project"], "repoUrl": meta["repoUrl"], "languages": langs}
            results.append(out)
    # include small samples in metadata for debugging
    sample = results[:3]
    sample_repo_urls = [r.get("repoUrl") for r in sample]
    sample_languages = [r.get("languages") for r in sample]
    meta = {
        "count": MetadataValue.int(len(results)),
        "sample": MetadataValue.json(sample),
        "sample_repo_urls": MetadataValue.json(sample_repo_urls),
        "sample_languages": MetadataValue.json(sample_languages),
    }
    return Output(value=results, metadata=meta)
