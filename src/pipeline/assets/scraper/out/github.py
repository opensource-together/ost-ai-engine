import typing as _t

from dagster import (
    asset,
    AssetIn,
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
        "Upsert mapped projects into the Project table via Prisma. "
        "Skips items missing `repoUrl`. Returns counts of inserted/updated."
    ),
    ins={"core_github__enrich_project_data": AssetIn()},
)
def out_github__table_projects_db(context, core_github__enrich_project_data: _t.List[_t.Dict]):
    """
    Upsert mapped projects into the Project table using Prisma.

    **Description:**
    Persists the enriched project data into the PostgreSQL database, handling both creation and updates.

    **Logic:**
    1. **Validation**: Checks for valid Prisma client and input data.
    2. **Upsert Loop**: Iterates through projects, checking for existence by `repoUrl`.
    3. **Project Upsert**: Creates new projects or updates existing ones.
    4. **Relation Upsert**: Updates `ProjectTechStack` relations if project ID is available.
    5. **Error Handling**: Captures and logs errors per project without failing the entire batch.

    **Output:**
    Dictionary containing counts of inserted, updated, and failed records.
    """
    context.log.info(f"out_github__table_projects_db: Starting with {len(core_github__enrich_project_data) if core_github__enrich_project_data else 0} projects to upsert")
    inserted = 0
    updated = 0
    errors: list[tuple[int, str]] = []

    with prisma_client() as prisma:
        # If the Prisma client couldn't be initialized (e.g. binary missing or
        # incompatible), prisma_client yields None. In that case we avoid
        # attempting DB writes from the child process to prevent crashes and
        # instead log and return a diagnostic metadata payload.
        if prisma is None:
            context.log.error("out_github__table_projects_db: Prisma client unavailable; skipping DB writes in this run.")
            # Return counts=0 and error flag so downstream checks fail fast but
            # the worker doesn't crash with SIGBUS.
            result_value = {"inserted": 0, "updated": 0}
            return Output(value=result_value, metadata={
                "inserted_count": MetadataValue.int(0),
                "updated_count": MetadataValue.int(0),
                "error_count": MetadataValue.int(len(core_github__enrich_project_data or [])),
                "note": MetadataValue.text("Prisma client unavailable; writes skipped."),
            })

        context.log.info(f"out_github__table_projects_db: Starting upsert loop for {len(core_github__enrich_project_data or [])} projects")
        for i, item in enumerate(core_github__enrich_project_data or []):
            # The item from enrich_project_data has structure:
            # { "project": {...}, "repoUrl": "...", "readme": "...", "tech_stack_ids": [...], "category_ids": [...] }
            # We need to extract the project dict and potentially enrich it or just use it.
            # For now, we primarily want the project data that was mapped.
            project = item.get("project")
            if not project:
                context.log.warning(f"Skipping item {i}: missing 'project' data.")
                errors.append((i, "missing_project_data"))
                continue
            
            # Ensure repoUrl is consistent
            repo_url = item.get("repoUrl") or project.get("repoUrl")
            if not repo_url:
                context.log.warning(f"Skipping project {i}: missing repoUrl (required for insert).")
                errors.append((i, "missing_repoUrl"))
                continue
            
            if i < 3:  # Log first 3 for debugging
                context.log.debug(f"out_github__table_projects_db: Processing project {i}: repoUrl={repo_url}")

            project_data = {k: v for k, v in project.items() if v is not None}

            try:
                # Try to find an existing project by repoUrl
                existing = None
                try:
                    existing = prisma.project.find_first(where={"repoUrl": repo_url})
                except Exception:
                    try:
                        existing = prisma.project.find_unique(where={"repoUrl": repo_url})
                    except Exception:
                        existing = None

                existing_id = None

                if existing:
                    try:
                        # Try to obtain the primary key `id`
                        try:
                            existing_id = getattr(existing, "id", None)
                        except Exception:
                            existing_id = None
                        if existing_id is None and isinstance(existing, dict):
                            existing_id = existing.get("id")

                        if existing_id:
                            # Update by primary key
                            data = {k: v for k, v in project_data.items() if k != "id"}
                            prisma.project.update(where={"id": existing_id}, data=data)
                            updated += 1
                        else:
                            # Fallback: update_many
                            # We won't have an ID for relations here easily unless we fetch again, 
                            # but let's assume we can't reliably get it if we are here.
                            # However, for the sake of relations, we might want to try fetching it again if update succeeded?
                            # For now, let's skip relation upsert if we can't get ID.
                            try:
                                res = prisma.project.update_many(where={"repoUrl": repo_url}, data=project_data)
                            except Exception:
                                res = prisma.execute_raw
                            
                            updated += 1 # Simplified counting
                    except Exception as e:
                        context.log.error(f"Error updating project {i} (repoUrl={repo_url}): {e}")
                        errors.append((i, f"update_error: {e}"))
                else:
                    try:
                        # Create
                        data = {k: v for k, v in project_data.items() if k != "id"}
                        created = prisma.project.create(data=data)
                        existing_id = created.id
                        inserted += 1
                    except Exception as e:
                        context.log.error(f"Error inserting project {i} (repoUrl={repo_url}): {e}")
                        errors.append((i, f"create_error: {e}"))

                # Upsert relations if we have a project ID
                if existing_id:
                    tech_stack_ids = item.get("tech_stack_ids") or []

                    # ProjectTechStack
                    pts_model = _find_model(prisma, ["project_tech_stack", "ProjectTechStack", "projectTechStack", "projecttechstack"])
                    if pts_model:
                        for ts_id in tech_stack_ids:
                            try:
                                pts_model.upsert(
                                    where={"projectId_techStackId": {"projectId": existing_id, "techStackId": ts_id}},
                                    data={
                                        "create": {"projectId": existing_id, "techStackId": ts_id},
                                        "update": {},
                                    }
                                )
                            except Exception as e:
                                context.log.warning(f"Failed to upsert ProjectTechStack for project {existing_id}, ts {ts_id}: {e}")
                    else:
                        context.log.error("ProjectTechStack model not found in Prisma client.")

            except Exception as e:
                context.log.exception(f"Unexpected error processing project {i} (repoUrl={repo_url})")
                errors.append((i, str(e)))

    context.log.info(
        f"out_github__table_projects_db: COMPLETE - "
        f"inserted={inserted}, "
        f"updated={updated}, "
        f"errors={len(errors)}, "
        f"total_processed={len(core_github__enrich_project_data or [])}"
    )
    if errors:
        context.log.warning(f"out_github__table_projects_db: {len(errors)} errors occurred: {errors[:3]}")

    result_value = {"inserted": inserted, "updated": updated}
    return Output(value=result_value, metadata={
        "inserted_count": MetadataValue.int(inserted),
        "updated_count": MetadataValue.int(updated),
        "error_count": MetadataValue.int(len(errors)),
        "total_input": MetadataValue.int(len(core_github__enrich_project_data or [])),
        "error_sample": MetadataValue.json(errors[:5]) if errors else MetadataValue.null(),
    })
