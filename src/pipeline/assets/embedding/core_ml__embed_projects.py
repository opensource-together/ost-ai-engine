
from dagster import asset, AssetExecutionContext, AssetIn
from dagster_dbt import get_asset_key_for_model
from src.pipeline.definitions import dbt_project_assets
from src.pipeline.resources.sentence_transformer_resource import SentenceTransformerResource
import pandas as pd
import os
import uuid
from sqlalchemy import create_engine, text

@asset(
    compute_kind="python",
    group_name="ml",
    deps=[get_asset_key_for_model([dbt_project_assets], "raw_public_project")]
)
def core_ml__embed_projects(context: AssetExecutionContext, sentence_transformer: SentenceTransformerResource):
    """
    Reads context from ml.raw_public_project, computes embeddings, and stores them in ml.embd_github_project.
    """
    db_url = os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    # 1. Fetch raw projects with context
    query = "SELECT id, context FROM ml.raw_public_project"
    df = pd.read_sql(query, engine)
    
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
                    INSERT INTO ml.embd_github_project ("id", "projectId", "embeddingVector", "createdAt")
                    VALUES (:id, :projectId, :vector, NOW())
                    ON CONFLICT ("projectId") 
                    DO UPDATE SET 
                        "embeddingVector" = EXCLUDED."embeddingVector",
                        "createdAt" = NOW();
                """)
                
                conn.execute(stmt, {
                    "id": item['id'],
                    "projectId": item['projectId'],
                    "vector": vector_str 
                })
                
    context.log.info("Successfully upserted embeddings to ml.embd_github_project.")
