import uuid
from typing import Any

from dagster import AssetExecutionContext, AssetKey, asset

from src.services.python.db import get_db_cursor

DEFAULT_OWNERS = ["team:OST/spideyai-X"]


class _CriticalSyncError(Exception):
    """Raised for DB errors that must propagate and not be swallowed."""


@asset(
    kinds={"python", "postgres"},
    owners=DEFAULT_OWNERS,
    group_name="sync",
    key=AssetKey(["public", "Project"]),  # Explicitly match DBT Source
    required_resource_keys={"io_manager"},
)
def core_public__sync_projects(
    context: AssetExecutionContext,
    core_match__classify_projects: list[dict[str, Any]],
) -> None:
    """
    Persist classified projects to public.Project and related match/public tables.
    """
    data = core_match__classify_projects

    if not data:
        context.log.info("No data to sync.")
        return

    with get_db_cursor() as cur:
        # Load TechStack Map (Name -> ID)
        cur.execute('SELECT "id", "name" FROM "public"."tech_stack"')
        tech_stack_map = {row["name"].lower(): row["id"] for row in cur.fetchall()}

    synced_count = 0

    for item in data:
        p = item["project"]
        classification = item["classification"]

        cat_id = (
            str(classification["categoryId"]) if classification["categoryId"] else None
        )
        dom_id = str(classification["domainId"]) if classification["domainId"] else None

        # Combine languages (dict keys) and topics (list)
        # languages is typically JSON like {"Python": 1000, "Rust": 500}
        # topics is JSON list ["machine-learning", "python"]

        project_tech_names: set[str] = set()

        langs = p.get("languages")
        if langs:
            if isinstance(langs, dict):
                project_tech_names.update(k.lower() for k in langs)
            elif isinstance(langs, list) and langs and isinstance(langs[0], str):
                project_tech_names.update(lang.lower() for lang in langs)

        if p.get("topics"):
            project_tech_names.update(t.lower() for t in p["topics"])

        try:
            # Use a separate transaction per project to isolate failures
            with get_db_cursor(commit=True) as cur:
                # A. Upsert public.Project
                # Force trending = True
                cur.execute(
                    """
                    INSERT INTO "public"."Project" (
                        "id",
                        "title",
                        "description",
                        "repoUrl",
                        "provider",
                        "githubUrl",
                        "published",
                        "trending",
                        "createdAt",
                        "updatedAt"
                    )
                    VALUES (
                        %s, %s, %s, %s,
                        'GITHUB', %s, true, true, %s, NOW()
                    )
                    ON CONFLICT ("id") DO UPDATE SET
                        "title" = EXCLUDED."title",
                        "description" = EXCLUDED."description",
                        "repoUrl" = EXCLUDED."repoUrl",
                        "githubUrl" = EXCLUDED."githubUrl",
                        "trending" = true,
                        "updatedAt" = NOW();
                """,
                    (
                        str(p["id"]),
                        p["title"],
                        p["description"],
                        p["url"],
                        p["url"],  # githubUrl
                        p["created_at"],
                    ),
                )

                # B. Upsert match.project_classification
                match_id = str(uuid.uuid4())
                model_version = classification.get("modelVersion")
                prompt_version = classification.get("promptVersion")
                try:
                    cur.execute(
                        """
                        INSERT INTO "match"."project_classification" (
                            "id", "projectId", "categoryId",
                            "domainId", "modelVersion", "promptVersion",
                            "createdAt", "updatedAt"
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                        ON CONFLICT ("projectId") DO UPDATE SET
                            "categoryId" = EXCLUDED."categoryId",
                            "domainId" = EXCLUDED."domainId",
                            "modelVersion" = EXCLUDED."modelVersion",
                            "promptVersion" = EXCLUDED."promptVersion",
                            "updatedAt" = NOW();
                    """,
                        (
                            match_id,
                            str(p["id"]),
                            cat_id,
                            dom_id,
                            model_version,
                            prompt_version,
                        ),
                    )
                except Exception as db_err:
                    context.log.error(
                        f"DB Error upserting classification for {p['id']}: {db_err}"
                    )
                    raise _CriticalSyncError(str(db_err)) from db_err

                # C. Relations

                # 1. Category -> public.project_category
                if cat_id:
                    cur.execute(
                        """
                        INSERT INTO "public"."project_category"
                        ("id", "projectId", "categoryId", "createdAt")
                        VALUES (%s, %s, %s, NOW())
                        ON CONFLICT ("projectId", "categoryId") DO NOTHING;
                    """,
                        (str(uuid.uuid4()), str(p["id"]), cat_id),
                    )

                # 2. Domain -> public.project_domain
                if dom_id:
                    cur.execute(
                        """
                        INSERT INTO "public"."project_domain"
                        ("id", "projectId", "domainId", "createdAt")
                        VALUES (%s, %s, %s, NOW())
                        ON CONFLICT ("projectId", "domainId") DO NOTHING;
                    """,
                        (str(uuid.uuid4()), str(p["id"]), dom_id),
                    )

                # 3. Tech Stacks -> public.project_tech_stack
                for name in project_tech_names:
                    ts_id = tech_stack_map.get(name)
                    if ts_id:
                        cur.execute(
                            """
                            INSERT INTO "public"."project_tech_stack"
                            ("id", "projectId", "techStackId", "createdAt")
                            VALUES (%s, %s, %s, NOW())
                            ON CONFLICT ("projectId", "techStackId") DO NOTHING;
                        """,
                            (str(uuid.uuid4()), str(p["id"]), str(ts_id)),
                        )

            synced_count += 1

        except _CriticalSyncError:
            raise
        except Exception as e:
            context.log.error(f"Failed to sync '{p.get('title')}': {e}")

    context.log.info(
        f"Sync Complete. Persisted {synced_count} projects, "
        "classifications, and tech stacks."
    )
    return None  # Return None as we used explicit key but yield nothing dynamic
