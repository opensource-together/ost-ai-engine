import os
import pickle
import numpy as np
import pandas as pd
from dagster import asset, Config
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from typing import List, Dict, Any

from src.infrastructure.postgres.database import get_db_session
from src.infrastructure.config import settings

from src.infrastructure.services.mlflow_model_persistence import mlflow_model_persistence
from src.infrastructure.logger import log

logger = log

class UserEmbeddingConfig(Config):
    model_name: str = settings.MODEL_NAME
    batch_size: int = 32
    save_embeddings: bool = True
    save_metadata: bool = True

@asset(
    description="Generate embeddings for users using sentence transformers",
    group_name="ml_pipeline",
    deps=["embed_USERS"]  # Depends on the dbt model
)
def user_embeddings(context, config: UserEmbeddingConfig) -> Dict[str, Any]:
    """
    Generate embeddings for users using the same model as projects.
    Reads from embed_USERS_temp (populated by dbt) and stores in embed_USERS.
    """
    logger.info("🚀 Starting user embeddings generation...")
    
    # Initialize the model
    model = SentenceTransformer(config.model_name)
    logger.info(f"✅ Loaded model: {config.model_name}")
    
    try:
        # Read user data from embed_USERS
        with get_db_session() as db:
            # Get user data with embedding text
            query = text("""
                SELECT user_id, username, embedding_text, bio, categories
                FROM "embed_USERS"
                WHERE embedding_text IS NOT NULL AND LENGTH(embedding_text) > 10
                ORDER BY username
            """)
            
            result = db.execute(query)
            users_data = result.fetchall()
            
            if not users_data:
                logger.warning("⚠️ No user data found for embedding generation")
                return {"status": "no_data", "count": 0}
            
            logger.info(f"📊 Found {len(users_data)} users to process")
            
            # Extract texts and metadata
            texts = [row.embedding_text for row in users_data]
            user_ids = [str(row.user_id) for row in users_data]
            usernames = [row.username for row in users_data]
            
            # Generate embeddings in batches
            all_embeddings = []
            for i in range(0, len(texts), config.batch_size):
                batch_texts = texts[i:i + config.batch_size]
                batch_embeddings = model.encode(batch_texts, show_progress_bar=False)
                all_embeddings.extend(batch_embeddings)
                logger.info(f"📈 Processed batch {i//config.batch_size + 1}/{(len(texts) + config.batch_size - 1)//config.batch_size}")
            
            embeddings_array = np.array(all_embeddings)
            logger.info(f"✅ Generated embeddings shape: {embeddings_array.shape}")
            
            # Update existing records with embeddings (like projects do)
            for user_id, embedding in zip(user_ids, all_embeddings):
                # Convertir numpy array en liste pour pgvector
                embedding_list = embedding.tolist()
                
                db.execute(text("""
                    UPDATE "embed_USERS" 
                    SET embedding_vector = :embedding
                    WHERE user_id = :user_id
                """), {
                    "embedding": embedding_list,
                    "user_id": user_id
                })
                
            logger.info(f"💾 Updated {len(all_embeddings)} user embeddings in embed_USERS with pgvector")
            
            # Prepare artifacts and metadata for MLflow
            artifacts = {
                "user_embeddings": embeddings_array,
                "user_ids": user_ids,
                "usernames": usernames,
            }
            
            metadata = {
                "user_ids": user_ids,
                "usernames": usernames,
                "model_name": settings.MODEL_DISPLAY_NAME,
                "embedding_dimension": embeddings_array.shape[1],
                "count": len(user_ids),
                "generation_time": 0  # TODO: Add actual generation time
            }
            

            
            # Save with MLflow model persistence
            if config.save_embeddings:
                model_uri = mlflow_model_persistence.save_embeddings("user_embeddings", artifacts)
                logger.info(f"💾 Saved user embeddings with MLflow: {model_uri}")
            
            return {
                "status": "success",
                "count": len(user_ids),
                "embedding_shape": embeddings_array.shape,
                "model_name": config.model_name
            }
            
    except Exception as e:
        logger.error(f"❌ Error generating user embeddings: {str(e)}")
        raise


