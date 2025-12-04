import typing as _t
from dagster import asset, Output, MetadataValue, AssetIn
from src.services.python.prisma_client import prisma_client
from src.pipeline.assets.scraper.core.utils import _find_model

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

@asset(
    kinds={"python"},
    owners=DEFAULT_OWNERS,
    group_name="projects_embedding",
    description="Push project embeddings to the database.",
    ins={"core_projects__compute_embeddings": AssetIn()},
)
def out_projects__store_embeddings(context, core_projects__compute_embeddings: _t.List[_t.Dict]):
    """
    Upserts project embeddings into the ProjectEmbedding table.
    Matches projects by repoUrl to get projectId.
    """
    context.log.info(f"out_project_embeddings: Starting with {len(core_project_embeddings) if core_project_embeddings else 0} items...")
    
    if not core_project_embeddings:
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

        repo_urls = [item["repoUrl"] for item in core_project_embeddings]
        
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
        missing_projects_count = 0
        total = len(core_project_embeddings)
        
        for i, item in enumerate(core_project_embeddings):
            if i % 50 == 0:
                context.log.info(f"Upserting item {i+1}/{total}...")
                
            repo_url = item["repoUrl"]
            vector = item["vector"]
            project_id = repo_to_id.get(repo_url)
            
            if not project_id:
                missing_projects_count += 1
                if missing_projects_count <= 10:
                    context.log.warning(f"Project not found for repoUrl: {repo_url}")
                elif missing_projects_count == 11:
                    context.log.warning("More projects not found... suppressing further warnings.")
                continue
                
            try:
                # Delete existing embeddings for this project to avoid duplicates
                # (Since there is no unique constraint on projectId)
                embedding_model.delete_many(where={"projectId": project_id})
                
                # Insert new embedding using raw query because vector type is Unsupported
                # We cast the parameter to vector: $2::vector
                prisma.execute_raw(
                    """
                    INSERT INTO "project_embedding" ("id", "projectId", "vector", "createdAt")
                    VALUES (uuid_generate_v4(), $1::uuid, $2::vector, NOW());
                    """,
                    project_id,
                    vector
                )
                upserted_count += 1
                
            except Exception as e:
                context.log.error(f"Failed to upsert embedding for {repo_url}: {e}")

    context.log.info(f"out_project_embeddings: Upserted {upserted_count} embeddings.")

    return Output(
        value=[],
        metadata={
            "upserted_count": MetadataValue.int(upserted_count),
        }
    )
