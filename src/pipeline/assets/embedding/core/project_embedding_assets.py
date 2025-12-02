import typing as _t
from dagster import asset, Output, MetadataValue, AssetIn
from src.pipeline.resources.embedding_model_resource import BGEModelResource

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

@asset(
    kinds={"python"},
    owners=DEFAULT_OWNERS,
    group_name="projects_embedding",
    io_manager_key="io_manager",
    ins={"raw_project_data": AssetIn("raw_project_data")}
)
def core_project_embeddings(context: AssetExecutionContext, raw_project_data: list[dict]):
    """
    Computes vector embeddings for each project's context string.
    """
    context.log.info(f"core_project_embeddings: Starting with {len(raw_project_data) if raw_project_data else 0} items...")
    
    model_resource: EmbeddingModelResource = context.resources.embedding_model
    
    results = []
    total = len(raw_project_data) if raw_project_data else 0
    
    for i, item in enumerate(raw_project_data or []):
        if i % 10 == 0:
            context.log.info(f"Processing item {i+1}/{total}...")
            
        repo_url = item.get("repoUrl")
        context_str = item.get("context")
        
        if not repo_url or not context_str:
            continue
            
        try:
            vector = model_resource.compute_vector(context_str)
            # vector is likely a numpy array or list of floats. 
            # Prisma vector type expects a list of floats.
            if hasattr(vector, "tolist"):
                vector = vector.tolist()
                
            results.append({
                "repoUrl": repo_url,
                "vector": vector
            })
        except Exception as e:
            context.log.error(f"Failed to compute embedding for {repo_url}: {e}")

    context.log.info(f"core_project_embeddings: Computed {len(results)} embeddings.")

    return Output(
        value=results,
        metadata={
            "count": MetadataValue.int(len(results)),
            "sample": MetadataValue.json(results[:1] if results else []),
        }
    )
