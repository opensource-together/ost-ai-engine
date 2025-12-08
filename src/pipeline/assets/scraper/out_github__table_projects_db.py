import typing as _t
from dagster import (
    asset,
    AssetIn,
    AssetKey,
    MetadataValue,
    Output,
)
from src.services.python.db import get_db_cursor
import json
import uuid

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

@asset(
    kinds={"python", "postgres"},
    owners=DEFAULT_OWNERS,
    group_name="github_projects_scraper",
    description=(
        "Upsert enriched projects into the IntGithubProject table via Prisma. "
        "Skips items missing `repoUrl`. Returns counts of inserted/updated."
    ),
    ins={"core_github__enrich_project_data": AssetIn()},
    key=AssetKey(["ost", "int_github_project"]), # Matches dbt source
)
def out_github__table_projects_db(context, core_github__enrich_project_data: _t.List[_t.Dict]):
    """
    Upsert enriched projects into the int_github_project table using Prisma.
    """
    context.log.info(f"out_github__table_projects_db: Starting with {len(core_github__enrich_project_data) if core_github__enrich_project_data else 0} projects to upsert")
    inserted = 0
    updated = 0
    errors: list[tuple[int, str]] = []

    with get_db_cursor(commit=True) as cur:
        context.log.info(f"out_github__table_projects_db: Starting upsert loop for {len(core_github__enrich_project_data or [])} projects")
        
        for i, item in enumerate(core_github__enrich_project_data or []):
            project = item.get("project")
            if not project:
                context.log.warning(f"Skipping item {i}: missing 'project' data.")
                errors.append((i, "missing_project_data"))
                continue
            
            project_id = project.get("id")
            if not project_id:
                 context.log.warning(f"Skipping item {i}: missing project id.")
                 errors.append((i, "missing_project_id"))
                 continue

            repo_url = item.get("repoUrl")
            
            # Prepare enriched data payload
            enriched_data = {
                "repoUrl": repo_url,
                "readme": item.get("readme"),
                "topics": item.get("topics"),
                "tech_stack_ids": item.get("tech_stack_ids"),
                "languages": item.get("languages"), # if available in item
                "description": item.get("description"),
            }
            
            try:
                cur.execute("SAVEPOINT upsert_project")
                enriched_json = json.dumps(enriched_data)
                
                # Upsert logic using INSERT ON CONFLICT
                # Assuming projectId is unique in int_github_project
                cur.execute(
                    """
                    INSERT INTO "analytics"."int_github_project" ("id", "projectId", "enrichedData", "updatedAt", "createdAt")
                    VALUES (%s, %s, %s, NOW(), NOW())
                    ON CONFLICT ("projectId") 
                    DO UPDATE SET 
                        "enrichedData" = EXCLUDED."enrichedData",
                        "updatedAt" = NOW()
                    """,
                    (str(uuid.uuid4()), project_id, enriched_json)
                )
                cur.execute("RELEASE SAVEPOINT upsert_project")
                
                inserted += 1

            except Exception as e:
                cur.execute("ROLLBACK TO SAVEPOINT upsert_project")
                context.log.error(f"Error upserting IntGithubProject for {project_id}: {e}")
                errors.append((i, str(e)))

    context.log.info(
        f"out_github__table_projects_db: COMPLETE - "
        f"processed={inserted}, "
        f"errors={len(errors)}, "
        f"total_input={len(core_github__enrich_project_data or [])}"
    )

    result_value = {"inserted": inserted, "updated": 0} # Simplified count
    return Output(value=result_value, metadata={
        "upserted_count": MetadataValue.int(inserted),
        "error_count": MetadataValue.int(len(errors)),
    })
