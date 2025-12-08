import typing as _t
import json
import uuid
from dagster import (
    asset,
    AssetIn,
    AssetKey,
    MetadataValue,
    Output,
)
from src.services.python.db import get_db_cursor

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

@asset(
    kinds={"python", "postgres"},
    owners=DEFAULT_OWNERS,
    ins={"projects": AssetIn("raw_github__extract_projects")},
    group_name="github_projects_scraper",
    key=AssetKey(["ost", "raw_github_project"]), # Matches dbt source
)
def raw_github__load_project(context, projects: _t.List[_t.Dict]):
    """
    Inserts raw project data (JSON) into the `analytics.raw_github_project` table.
    """
    context.log.info(f"raw_github__load_project: Loading {len(projects)} projects to Postgres...")
    
    count = 0
    with get_db_cursor(commit=True) as cur:
        for project in projects:
            try:
                # Generate a UUID for the ID since we are inserting raw SQL
                project_json = json.dumps(project)
                
                # Use SAVEPOINT to allow partial failures without aborting the transaction
                cur.execute("SAVEPOINT insert_project")
                cur.execute(
                    """
                    INSERT INTO "analytics"."raw_github_project" ("id", "data", "createdAt", "updatedAt")
                    VALUES (%s, %s, NOW(), NOW())
                    """,
                    (str(uuid.uuid4()), project_json)
                )
                cur.execute("RELEASE SAVEPOINT insert_project")
                count += 1
            except Exception as e:
                # Rollback to savepoint to restore transaction state
                cur.execute("ROLLBACK TO SAVEPOINT insert_project")
                context.log.warning(f"Failed to insert project {project.get('name', 'unknown')}: {e}")

    context.log.info(f"raw_github__load_project: Loaded {count} projects.")
    return Output(value=None, metadata={"loaded_count": MetadataValue.int(count)})
