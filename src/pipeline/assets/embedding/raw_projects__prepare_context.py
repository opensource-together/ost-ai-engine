import typing as _t
from dagster import asset, Output, MetadataValue, AssetIn, AssetKey

from src.services.python.db import get_db_cursor
import json

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

@asset(
    kinds={"python", "postgres"},
    owners=DEFAULT_OWNERS,
    group_name="projects_embedding",
    description="Format project data from enriched metadata into a context string for embedding.",

    deps=[AssetKey(["github", "pvt_github_project"])],
)
def raw_projects__prepare_context(context):
    """
    Formats the data into a single context string for each project.
    Reads from `pvt_github_project` table.
    """
    context.log.info("raw_projects__prepare_context: Reading from IntGithubProject...")

    results = []
    try:
        with get_db_cursor() as cur:
            # Read from pvt_github_project table (created by dbt)
            # This table now contains the pre-computed context column
            cur.execute('SELECT id as "projectId", url as "repoUrl", context FROM "github"."pvt_github_project"')
            records = cur.fetchall()
            context.log.info(f"Fetched {len(records)} projects from pivot_github_project.")
    except Exception as e:
        context.log.error(f"Failed to query pivot_github_project table: {e}")
        return Output(value=[], metadata={"error": MetadataValue.text(str(e))})

    for record in records:
        project_id = record.get("projectId")
        repo_url = record.get("repoUrl")
        context_str = record.get("context")
        
        if not repo_url or not context_str:
            continue

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
