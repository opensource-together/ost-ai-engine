from dagster import asset, AssetExecutionContext, AssetKey, Output, AssetIn
from src.services.python.db import get_db_cursor
import pandas as pd
import json

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

@asset(
    kinds={"python", "pgvector"},
    owners=DEFAULT_OWNERS,
    key=AssetKey(["ml", "embd_user"]), # Matches dbt source
    ins={"user_df": AssetIn(key=AssetKey(["ml", "pvt_public_user"]))}, # Matches dbt model
    group_name="embedding",
    required_resource_keys={"sentence_transformer", "io_manager"},
)
def core_ml__embed_users(context, user_df):
    """
    Step 3: User Embedding.
    
    1. Reads user context from `ml.pvt_public_user`.
    2. Generates embeddings using SentenceTransformer.
    3. Writes to `ml.embd_user` (or `public.user_embedding`).
    """
    model = context.resources.sentence_transformer
    
    users = user_df.to_dict('records')
    context.log.info(f"Loaded {len(users)} users for embedding.")
    
    if not users:
        return Output(value=None, metadata={"count": 0})

    results = []
    
    # 1. Embed
    texts = [u['user_context'] for u in users]
    embeddings = model.encode(texts) # Returns numpy array
    
    context.log.info(f"Generated embeddings for {len(embeddings)} users.")

    # 2. Persist
    synced_count = 0
    with get_db_cursor(commit=True) as cur:
        for i, user in enumerate(users):
            user_id = user['user_id']
            vector = embeddings[i] # Already a list if model.encode returned list-of-lists
            
            try:
                # Upsert into ml.embd_user
                cur.execute("""
                    INSERT INTO "ml"."embd_user" ("id", "userId", "vector", "createdAt", "updatedAt")
                    VALUES (uuid_generate_v4(), %s, %s, NOW(), NOW())
                    ON CONFLICT ("userId") DO UPDATE SET
                        "vector" = EXCLUDED."vector",
                        "updatedAt" = NOW();
                """, (str(user_id), str(vector)))
                
                synced_count += 1
            except Exception as e:
                context.log.error(f"Failed to save embedding for user {user_id}: {e}")

    return Output(
        value=None, 
        metadata={
            "count": synced_count,
            "preview": [u['user_context'][:50] for u in users[:5]]
        }
    )
