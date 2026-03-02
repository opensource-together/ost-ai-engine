
from dagster import asset, AssetExecutionContext, AssetIn, AssetKey

from ...resources.sentence_transformer_resource import SentenceTransformerResource
import pandas as pd
import os
import uuid
from sqlalchemy import create_engine, text

# Constant for the upsert query
UPSERT_EMBEDDING_QUERY = text("""
    INSERT INTO ml.embd_github_project ("id", "projectId", "vector", "createdAt")
    VALUES (:id, :projectId, :vector, NOW())
    ON CONFLICT ("projectId") 
    DO UPDATE SET 
        "vector" = EXCLUDED."vector",
        "createdAt" = NOW();
""")

@asset(
    compute_kind="python",
    group_name="ml",
    key=AssetKey(["ml", "embd_github_project"]), # Matches dbt source
    ins={"projects_df": AssetIn(key=AssetKey(["ml", "int_project_embedding_candidate"]))},
)
def core_ml__embed_projects(context: AssetExecutionContext, projects_df: pd.DataFrame, sentence_transformer: SentenceTransformerResource):
    """
    Reads rich context from ml.int_project_embedding_candidate, computes embeddings, and stores them in ml.embd_github_project.
    """
    db_url = os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    # 1. Fetch raw projects with context
    df = projects_df
    
    context.log.info(f"Fetched {len(df)} projects to embed.")

    if df.empty:
        return

    # 2. Compute embeddings
    embeddings = []
    
    # Process in batches if necessary, but for now simple loop
    for index, row in df.iterrows():
        # Adapter to int_project_embedding_candidate columns
        project_id = row['project_id']
        context_text = row['rich_context_string']
        
        if not context_text:
            continue
            
        vector = sentence_transformer.encode(context_text)
        embeddings.append({
            "id": str(uuid.uuid4()),
            "projectId": project_id,
            "vector": vector 
        })
        
        if len(embeddings) % 100 == 0:
             context.log.info(f"Computed {len(embeddings)} embeddings...")

    context.log.info(f"Total embeddings computed: {len(embeddings)}")

    if not embeddings:
        return

    # 3. Store in DB (Upsert logic)
    context.log.info(f"Upserting {len(embeddings)} embeddings...")
    
    with engine.connect() as conn:
        with conn.begin():
            for item in embeddings:
                # Convert list to string representation for postgres vector constraint
                vector_str = str(item['vector'])
                
                conn.execute(UPSERT_EMBEDDING_QUERY, {
                    "id": item['id'],
                    "projectId": item['projectId'],
                    "vector": vector_str 
                })
                
    context.log.info("Successfully upserted embeddings to ml.embd_github_project.")
