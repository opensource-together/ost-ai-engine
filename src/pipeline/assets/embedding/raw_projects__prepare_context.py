import typing as _t
from dagster import asset, Output, MetadataValue, AssetIn, AssetKey

from src.services.python.db import get_db_cursor
import json

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

@asset(
    kinds={"python"},
    owners=DEFAULT_OWNERS,
    group_name="projects_embedding",
    description="Format project data from enriched metadata into a context string for embedding.",

    deps=[AssetKey(["ost", "pivot_github_project"])],
)
def raw_projects__prepare_context(context):
    """
    Formats the data into a single context string for each project.
    Reads from `pivot_github_project` table.
    """
    context.log.info("raw_projects__prepare_context: Reading from IntGithubProject...")

    results = []
    try:
        with get_db_cursor() as cur:
            # Read from pivot_github_project table (created by dbt)
            # This table contains joined data from staging and intermediate
            # Note: Schema is 'analytics' due to dbt custom schema config
            cur.execute('SELECT id as "projectId", "enrichedData", url as "repoUrl", description, name, topics as "stg_topics" FROM "analytics"."pivot_github_project"')
            records = cur.fetchall()
            context.log.info(f"Fetched {len(records)} projects from pivot_github_project.")
    except Exception as e:
        context.log.error(f"Failed to query pivot_github_project table: {e}")
        return Output(value=[], metadata={"error": MetadataValue.text(str(e))})

    for record in records:
        project_id = record.get("projectId")
        enriched_data = record.get("enrichedData")
        
        if isinstance(enriched_data, str):
            try:
                enriched_data = json.loads(enriched_data)
            except Exception:
                enriched_data = {}
        elif not isinstance(enriched_data, dict):
            enriched_data = {}

        # Use data from pivot table directly if available, fallback to enrichedData
        repo_url = record.get("repoUrl") or enriched_data.get("repoUrl")
        if not repo_url:
            continue

        description = record.get("description") or enriched_data.get("description") or ""
        name = record.get("name") or (repo_url.split("/")[-1] if repo_url else "Unknown")
        
        readme = enriched_data.get("readme") or ""
        
        # Combine topics from stg and enriched
        stg_topics = record.get("stg_topics") or []
        enriched_topics = enriched_data.get("topics") or []
        
        # Merge unique topics
        all_topics = list(set((stg_topics if isinstance(stg_topics, list) else []) + (enriched_topics if isinstance(enriched_topics, list) else [])))
        topics_str = ", ".join(all_topics)
        
        context_str = f"""
Title: {name}
Description: {description}
Topics: {topics_str}
Readme: {readme[:5000]} 
""".strip()
# Truncate readme to avoid huge context

        results.append({
            "repoUrl": repo_url,
            "context": context_str,
            "project_id": project_id
        })

    context.log.info(f"raw_projects__prepare_context: Formatted {len(results)} project contexts.")

    return Output(
        value=results,
        metadata={
            "project_count": MetadataValue.int(len(results)),
            "status": MetadataValue.text("success"),
            "sample_output": MetadataValue.json(results[0]) if results else MetadataValue.null(),
        }
    )
