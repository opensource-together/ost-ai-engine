import typing as _t
import json
from dagster import (
    AssetIn,
    AssetKey,
    MetadataValue,
    Output,
    asset,
)
from src.services.python.prisma_client import prisma_client
from src.pipeline.assets.scraper.core.utils import _find_model

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

    with prisma_client() as prisma:
        if prisma is None:
            context.log.error("Failed to connect to Prisma.")
            return Output(value=[], metadata={"error": MetadataValue.text("Prisma client unavailable")})

        project_model = _find_model(prisma, ["project", "Project"])
        embedding_model = _find_model(prisma, ["project_embedding", "ProjectEmbedding", "projectEmbedding", "projectembedding"])
        
        if not project_model or not embedding_model:
             context.log.error("Project or ProjectEmbedding model not found.")
             return Output(value=[], metadata={"error": MetadataValue.text("Models not found")})

        repo_urls = [item["repoUrl"] for item in core_projects__compute_embeddings]
        
        try:
            projects = project_model.find_many(
                where={
                    "repoUrl": {"in": repo_urls}
                }
            )
            repo_to_id = {p.repoUrl: p.id for p in projects}
        except Exception as e:
            context.log.error(f"Failed to fetch projects: {e}")
            return Output(value=[], metadata={"error": MetadataValue.text(f"Fetch failed: {e}")})

        upserted_count = 0
        
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
                prisma.execute_raw('DELETE FROM "int_github_project" WHERE "projectId" = $1::uuid', project_id)
                prisma.execute_raw(
                    """
                    INSERT INTO "int_github_project" ("id", "projectId", "enrichedData", "createdAt", "updatedAt")
                    VALUES (uuid_generate_v4(), $1::uuid, $2::jsonb, NOW(), NOW());
                    """,
                    project_id,
                    json.dumps(enriched_data)
                )

                # 2. Insert into embd_github_project (Embeddings)
                prisma.execute_raw('DELETE FROM "embd_github_project" WHERE "projectId" = $1::uuid', project_id)
                prisma.execute_raw(
                    """
                    INSERT INTO "embd_github_project" ("id", "projectId", "embeddingVector", "createdAt")
                    VALUES (uuid_generate_v4(), $1::uuid, $2::vector, NOW());
                    """,
                    project_id,
                    vector
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
