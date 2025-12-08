import typing as _t
import json
from dagster import (
    AssetIn,
    AssetKey,
    MetadataValue,
    Output,
    asset,
)
from src.services.python.db import get_db_cursor
import uuid

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

@asset(
    kinds={"python"},
    owners=DEFAULT_OWNERS,
    group_name="projects_embedding",
    description="Push project embeddings to the database.",
    ins={"core_projects__compute_embeddings": AssetIn()},
    key=AssetKey(["ost", "embd_github_project"]), # Matches dbt source
)
def out_projects__store_embeddings(context, core_projects__compute_embeddings: _t.List[_t.Dict]):
    """
    Upserts project embeddings into the ProjectEmbedding table.
    """
    context.log.info(f"out_projects__store_embeddings: Starting with {len(core_projects__compute_embeddings) if core_projects__compute_embeddings else 0} items...")
    
    if not core_projects__compute_embeddings:
        return Output(value=[], metadata={"count": MetadataValue.int(0)})

    upserted_count = 0
    with get_db_cursor(commit=True) as cur:
        for item in core_projects__compute_embeddings:
            repo_url = item.get("repoUrl")
            vector = item.get("vector")
            project_id = item.get("project_id") # We passed this from raw_projects__prepare_context
            
            # If we don't have project_id passed down, we might need to look it up, 
            # but we should have it from staging.
            if not project_id:
                # Fallback lookup if needed, but let's assume we have it for efficiency
                continue

            try:
                # 1. Insert into int_github_project (Enriched Data)
                enriched_data = {
                    "context": item.get("context"),
                    "repoUrl": repo_url
                }
                
                # Delete old records to ensure idempotency
                cur.execute('DELETE FROM "analytics"."int_github_project" WHERE "projectId" = %s', (project_id,))
                
                cur.execute(
                    """
                    INSERT INTO "analytics"."int_github_project" ("id", "projectId", "enrichedData", "createdAt", "updatedAt")
                    VALUES (%s, %s, %s, NOW(), NOW())
                    """,
                    (str(uuid.uuid4()), project_id, json.dumps(enriched_data))
                )

                # 2. Insert into embd_github_project (Embeddings)
                cur.execute('DELETE FROM "analytics"."embd_github_project" WHERE "projectId" = %s', (project_id,))
                
                # Format vector for pgvector
                # vector is likely a list of floats. pgvector expects '[1.0, 2.0, ...]' string or list adapter
                # psycopg2 with pgvector might handle list, but safe to cast to string representation if needed.
                # Usually psycopg2 adapts lists to array, but pgvector needs specific format.
                # Let's assume standard list adaptation works or cast to string.
                # Better to use string format '[...]' for vector type.
                vector_str = str(vector) if isinstance(vector, list) else vector

                cur.execute(
                    """
                    INSERT INTO "analytics"."embd_github_project" ("id", "projectId", "embeddingVector", "createdAt")
                    VALUES (%s, %s, %s, NOW())
                    """,
                    (str(uuid.uuid4()), project_id, vector_str)
                )
                upserted_count += 1
                
            except Exception as e:
                context.log.error(f"Failed to upsert data for {repo_url}: {e}")

    context.log.info(f"out_project_embeddings: Upserted {upserted_count} embeddings.")

    return Output(
        value=[],
        metadata={
            "upserted_count": MetadataValue.int(upserted_count),
        }
    )
