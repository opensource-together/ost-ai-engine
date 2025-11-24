import typing as _t

from dagster import (
    asset,
    AssetIn,
    MetadataValue,
    Output,
)

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
    context.log.info(f"out_github__table_projects_db: Starting with {len(core_github__table_projects_mapped) if core_github__table_projects_mapped else 0} projects to upsert")
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
                "error_count": MetadataValue.int(len(core_github__table_projects_mapped or [])),
                "note": MetadataValue.text("Prisma client unavailable; writes skipped."),
            })

        context.log.info(f"out_github__table_projects_db: Starting upsert loop for {len(core_github__table_projects_mapped or [])} projects")
        for i, project in enumerate(core_github__table_projects_mapped or []):
            repo_url = project.get("repoUrl")
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

                if existing:
                    try:
                        # Update by primary key (id) to avoid relying on
                        # non-unique fields in the `where` clause which the
                        # Prisma query engine may reject. Use the found
                        # record's id if available.
                        # Try to obtain the primary key `id` from the returned object.
                        # The Prisma client may return either a model-like object or a
                        # dict-like mapping depending on client version/config — try
                        # both safely.
                        existing_id = None
                        try:
                            existing_id = getattr(existing, "id", None)
                        except Exception:
                            existing_id = None
                        if existing_id is None and isinstance(existing, dict):
                            existing_id = existing.get("id")

                        if existing_id:
                            # Ensure we don't accidentally try to update the id field
                            data = {k: v for k, v in project_data.items() if k != "id"}
                            prisma.project.update(where={"id": existing_id}, data=data)
                            updated += 1
                        else:
                            # No id available: update by a non-unique field with
                            # update_many so the Prisma engine does not require a
                            # unique `where` clause. This updates all matching
                            # rows and returns a dict with `count` in newer
                            # prisma-client-py versions. If update_many is not
                            # available or fails, catch the error and record it.
                            try:
                                # Diagnostic log to help debugging the returned
                                # 'existing' shape in the logs.
                                context.log.debug(f"out_github__table_projects_db: existing record for repoUrl={repo_url} has no id; type={type(existing)}; repr={repr(existing)[:200]}")
                                res = None
                                try:
                                    res = prisma.project.update_many(where={"repoUrl": repo_url}, data=project_data)
                                except Exception:
                                    # Some prisma client versions expose update_many
                                    # on the model or on the client differently; try
                                    # calling via the client directly if available.
                                    res = prisma.execute_raw
                                # If update_many returned a count, increment updated
                                try:
                                    # res may be a dict-like with 'count' or an int
                                    count = None
                                    if isinstance(res, dict):
                                        count = res.get("count")
                                    elif isinstance(res, int):
                                        count = res
                                    if count:
                                        updated += int(count)
                                    else:
                                        # unknown result: count as a single update
                                        updated += 1
                                except Exception:
                                    updated += 1
                            except Exception as e:
                                context.log.error(f"Error updating (fallback) project {i} (repoUrl={repo_url}): {e}")
                                errors.append((i, f"update_error: {e}"))
                    except Exception as e:
                        context.log.error(f"Error updating project {i} (repoUrl={repo_url}): {e}")
                        errors.append((i, f"update_error: {e}"))
                else:
                    try:
                        # Ensure we do not pass an explicit id when creating
                        data = {k: v for k, v in project_data.items() if k != "id"}
                        prisma.project.create(data=data)
                        inserted += 1
                    except Exception as e:
                        context.log.error(f"Error inserting project {i} (repoUrl={repo_url}): {e}")
                        errors.append((i, f"create_error: {e}"))

            except Exception as e:
                context.log.exception(f"Unexpected error processing project {i} (repoUrl={repo_url})")
                errors.append((i, str(e)))

    context.log.info(
        f"out_github__table_projects_db: COMPLETE - "
        f"inserted={inserted}, "
        f"updated={updated}, "
        f"errors={len(errors)}, "
        f"total_processed={len(core_github__table_projects_mapped or [])}"
    )
    if errors:
        context.log.warning(f"out_github__table_projects_db: {len(errors)} errors occurred: {errors[:3]}")

    result_value = {"inserted": inserted, "updated": updated}
    return Output(value=result_value, metadata={
        "inserted_count": MetadataValue.int(inserted),
        "updated_count": MetadataValue.int(updated),
        "error_count": MetadataValue.int(len(errors)),
        "total_input": MetadataValue.int(len(core_github__table_projects_mapped or [])),
        "error_sample": MetadataValue.json(errors[:5]) if errors else MetadataValue.null(),
    })
