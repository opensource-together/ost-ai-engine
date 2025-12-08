import typing as _t
from dagster import (
    asset,
    AssetIn,
    MetadataValue,
    Output,
)

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

@asset(
    kinds={"python"},
    owners=DEFAULT_OWNERS,
    ins={
        "langs": AssetIn("core_github__fetch_repo_languages"),
        "topics": AssetIn("core_github__fetch_repo_topics"),
        "readmes": AssetIn("core_github__fetch_readme"),
    },
    group_name="fetch_projects_metadatas",
    required_resource_keys={"config"},
)
def core_github__merge_repo_meta(context, langs, topics, readmes):
    """
    Merge languages, topics and readme by repoUrl into a single repo_meta structure.

    **Description:**
    Aggregates the results from parallel metadata fetching steps into a single unified structure per repository.

    **Logic:**
    1. **Aggregation**: Iterates through languages, topics, and readmes results.
    2. **Indexing**: Groups data by `repoUrl`.
    3. **Merging**: Combines all metadata fields into a single dictionary for each project.

    **Output:**
    List of fully enriched repository metadata dictionaries.
    """
    # langs and topics are lists of {project, repoUrl, languages} / {project, repoUrl, topics}
    context.log.info(f"core_github__merge_repo_meta: Merging metadata (langs={len(langs) if langs else 0}, topics={len(topics) if topics else 0}, readmes={len(readmes) if readmes else 0})")
    if not langs and not topics:
        return Output(value=[], metadata={"count": MetadataValue.int(0)})

    by_url = {}
    for item in (langs or []):
        url = item.get("repoUrl")
        if not url:
            continue
        by_url.setdefault(url, {})
        by_url[url].setdefault("project", item.get("project"))
        by_url[url]["languages"] = item.get("languages") or []
        # also preserve any description present on the mapped project dict
        try:
            proj = by_url[url].get("project") or {}
            if isinstance(proj, dict):
                desc = proj.get("description")
                if desc:
                    by_url[url]["description"] = desc
        except Exception:
            pass

    for item in (topics or []):
        url = item.get("repoUrl")
        if not url:
            continue
        by_url.setdefault(url, {})
        # prefer existing project record from langs, else take from topics
        if "project" not in by_url[url]:
            by_url[url]["project"] = item.get("project")
        by_url[url]["topics"] = item.get("topics") or []

    # incorporate readme fetch results (separate asset)
    for item in (readmes or []):
        url = item.get("repoUrl")
        if not url:
            continue
        by_url.setdefault(url, {})
        # attach raw readme text for use in embeddings/context
        by_url[url]["readme"] = item.get("readme") or ""

    results = []
    for url, data in by_url.items():
        results.append({
            "project": data.get("project"),
            "repoUrl": url,
            "languages": data.get("languages") or [],
            "topics": data.get("topics") or [],
            "description": data.get("description") or (data.get("project") or {}).get("description"),
            "readme": data.get("readme") or (data.get("project") or {}).get("readme"),
        })

    # include small samples and counts in metadata for easier debugging in the Dagster UI
    sample = results[:3]
    sample_repo_urls = [r.get("repoUrl") for r in sample]
    sample_languages = [r.get("languages") for r in sample]
    sample_topics = [r.get("topics") for r in sample]
    meta = {
        "count": MetadataValue.int(len(results)),
        "sample": MetadataValue.json(sample),
        "sample_repo_urls": MetadataValue.json(sample_repo_urls),
        "sample_languages": MetadataValue.json(sample_languages),
        "sample_topics": MetadataValue.json(sample_topics),
    }
    context.log.info(f"core_github__merge_repo_meta: merged {len(results)} repos; sample_urls={sample_repo_urls}")
    return Output(value=results, metadata=meta)
