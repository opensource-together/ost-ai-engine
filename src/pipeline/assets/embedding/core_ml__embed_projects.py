
from dagster import asset, AssetExecutionContext, AssetIn, AssetKey

from src.pipeline.resources.sentence_transformer_resource import SentenceTransformerResource
import pandas as pd
import os
import uuid
from sqlalchemy import create_engine, text

@asset(
    compute_kind="python",
    group_name="embedding",
    key=AssetKey(["ml", "embd_github_project"]), # Matches dbt source
    ins={"projects_df": AssetIn(key=AssetKey(["ml", "pvt_public_project"]))},
)
def core_ml__embed_projects(context: AssetExecutionContext, projects_df: pd.DataFrame, sentence_transformer: SentenceTransformerResource):
    """
    Reads context from ml.pvt_public_project, computes embeddings, and stores them in ml.embd_github_project.
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
        project_id = row['id']
        context_text = row['context']
        
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

    # 3. Store in DB (Upsert logic)
    # Prisma doesn't support vector insert easily via pandas to_sql if using pgvector specifically without handling
    # But here we are using a direct SQL insert for vector type.
    # We need to construct the INSERT statement carefully for pgvector.
    
    # We will use a raw connection execution for upsert
    # Table: ml.embd_github_project (id, projectId, embeddingVector)
    # Constraint: projectId is unique
    
    with engine.connect() as conn:
        with conn.begin():
            # Prepare statement
            # Note: vector string format is '[1.0, 2.0, ...]'
            
            for item in embeddings:
                # Convert list to string representation for postgres vector constraint
                vector_str = str(item['vector'])
                
                stmt = text("""
                    INSERT INTO ml.embd_github_project ("id", "projectId", "vector", "createdAt")
                    VALUES (:id, :projectId, :vector, NOW())
                    ON CONFLICT ("projectId") 
                    DO UPDATE SET 
                        "vector" = EXCLUDED."vector",
                        "createdAt" = NOW();
                """)
                
                conn.execute(stmt, {
                    "id": item['id'],
                    "projectId": item['projectId'],
                    "vector": vector_str 
                })
                
    context.log.info("Successfully upserted embeddings to ml.embd_github_project.")
