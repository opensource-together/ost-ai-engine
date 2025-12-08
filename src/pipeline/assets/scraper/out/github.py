import typing as _t

from dagster import (
    asset,
    AssetIn,
    AssetKey,
    MetadataValue,
    Output,
)

from src.pipeline.utils import prisma_client
from ..core.utils import _find_model

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

    with prisma_client() as prisma:
        if prisma is None:
            context.log.error("out_github__table_projects_db: Prisma client unavailable; skipping DB writes in this run.")
            result_value = {"inserted": 0, "updated": 0}
            return Output(value=result_value, metadata={
                "inserted_count": MetadataValue.int(0),
                "updated_count": MetadataValue.int(0),
                "error_count": MetadataValue.int(len(core_github__enrich_project_data or [])),
                "note": MetadataValue.text("Prisma client unavailable; writes skipped."),
            })

        context.log.info(f"out_github__table_projects_db: Starting upsert loop for {len(core_github__enrich_project_data or [])} projects")
        
        # Check if IntGithubProject model exists
        model = _find_model(prisma, ["intgithubproject", "int_github_project", "IntGithubProject", "intGithubProject"])
        if not model:
             context.log.error("IntGithubProject model not found in Prisma client.")
             return Output(value={"inserted": 0, "updated": 0}, metadata={"error": MetadataValue.text("Model not found")})

        for i, item in enumerate(core_github__enrich_project_data or []):
            project = item.get("project")
            if not project:
                context.log.warning(f"Skipping item {i}: missing 'project' data.")
                errors.append((i, "missing_project_data"))
                continue
            
            project_id = project.get("id")
            if not project_id:
                 # If we don't have ID from stg, we can't link.
                 # But wait, stg_github_project has 'id'.
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
                import json
                enriched_json = json.dumps(enriched_data)
                
                # Check existence
                existing = prisma.query_raw(
                    'SELECT id FROM "int_github_project" WHERE "projectId" = $1::uuid', 
                    project_id
                )
                
                if existing:
                    # Update
                    prisma.execute_raw(
                        'UPDATE "int_github_project" SET "enrichedData" = $1::jsonb, "updatedAt" = NOW() WHERE "projectId" = $2::uuid',
                        enriched_json, project_id
                    )
                    updated += 1
                else:
                    # Insert
                    # Try model.upsert first if possible
                    try:
                        model.upsert(
                            where={"projectId": project_id},
                            data={
                                "create": {
                                    "projectId": project_id,
                                    "enrichedData": enriched_data # Prisma client handles dict to json
                                },
                                "update": {
                                    "enrichedData": enriched_data
                                }
                            }
                        )
                        inserted += 1 # or updated, upsert counts as one
                    except Exception as upsert_err:
                        # Fallback to raw insert
                        import uuid
                        new_id = str(uuid.uuid4())
                        prisma.execute_raw(
                            'INSERT INTO "int_github_project" ("id", "projectId", "enrichedData", "updatedAt") VALUES ($1::uuid, $2::uuid, $3::jsonb, NOW())',
                            new_id, project_id, enriched_json
                        )
                        inserted += 1

            except Exception as e:
                context.log.error(f"Error upserting IntGithubProject for {project_id}: {e}")
                errors.append((i, str(e)))

    context.log.info(
        f"out_github__table_projects_db: COMPLETE - "
        f"upserted={inserted + updated}, "
        f"errors={len(errors)}, "
        f"total_processed={len(core_github__enrich_project_data or [])}"
    )

    result_value = {"inserted": inserted, "updated": updated}
    return Output(value=result_value, metadata={
        "upserted_count": MetadataValue.int(inserted + updated),
        "error_count": MetadataValue.int(len(errors)),
    })
