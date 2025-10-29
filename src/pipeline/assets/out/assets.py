import typing as _t

from dagster import asset, AssetIn, MetadataValue, Output

from src.pipeline.utils import prisma_client

DEFAULT_OWNERS = ["team:OST/spideyai-X"]


@asset(
    kinds={"python", "postgres"},
    owners=DEFAULT_OWNERS,
    group_name="github_projects_scraper",
    description=(
        "Upsert mapped projects into the Project table via Prisma. "
        "Skips items missing `repoUrl`. Returns counts of inserted/updated."
    ),
    ins={"core_github__table_projects_mapped": AssetIn()},
)
def out_github__table_projects_db(context, core_github__table_projects_mapped: _t.List[_t.Dict]):
    """Upsert mapped projects into the Project table using Prisma.

    - Skips items missing `repoUrl`.
    - Updates when a matching `repoUrl` exists, otherwise creates.
    - Returns a dict with inserted/updated counters and metadata.
    """
    inserted = 0
    updated = 0
    errors: list[tuple[int, str]] = []

    with prisma_client() as prisma:
        for i, project in enumerate(core_github__table_projects_mapped or []):
            repo_url = project.get("repoUrl")
            if not repo_url:
                context.log.warning(f"Skipping project {i}: missing repoUrl (required for insert).")
                errors.append((i, "missing_repoUrl"))
                continue

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

                if existing:
                    try:
                        prisma.project.update(where={"repoUrl": repo_url}, data=project_data)
                        updated += 1
                    except Exception as e:
                        context.log.error(f"Error updating project {i} (repoUrl={repo_url}): {e}")
                        errors.append((i, f"update_error: {e}"))
                else:
                    try:
                        prisma.project.create(data=project_data)
                        inserted += 1
                    except Exception as e:
                        context.log.error(f"Error inserting project {i} (repoUrl={repo_url}): {e}")
                        errors.append((i, f"create_error: {e}"))

            except Exception as e:
                context.log.exception(f"Unexpected error processing project {i} (repoUrl={repo_url})")
                errors.append((i, str(e)))

    context.log.info(f"{inserted} projects inserted, {updated} projects updated into the Project table.")
    if errors:
        context.log.warning(f"{len(errors)} insert/update errors: {errors[:3]}")

    result_value = {"inserted": inserted, "updated": updated}
    return Output(value=result_value, metadata={
        "inserted_count": MetadataValue.int(inserted),
        "updated_count": MetadataValue.int(updated),
        "error_count": MetadataValue.int(len(errors)),
        "first_error": MetadataValue.text(errors[0][1]) if errors else MetadataValue.null(),
    })


__all__ = ["out_github__table_projects_db"]
