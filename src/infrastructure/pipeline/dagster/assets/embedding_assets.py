"""Dagster assets for project embeddings with pgvector storage."""

import time
from typing import List
import json
import numpy as np

# Model configuration constants
MINILM_DIMENSIONS = 384  # Fixed dimension for all-MiniLM-L6-v2 model

from dagster import AssetIn, Nothing, Output, asset
from sqlalchemy import text

from src.infrastructure.services.mlflow_model_persistence import mlflow_model_persistence
from src.infrastructure.config import settings
from src.infrastructure.logger import log
from src.infrastructure.postgres.database import get_db_session


@asset(
    name="project_embeddings",
    description="Generate embeddings for all projects using all-MiniLM-L6-v2",
    ins={"embeddings_data": AssetIn("ml_project_embeddings", dagster_type=Nothing)},
    group_name="ml_embeddings",
    compute_kind="ml",
    required_resource_keys={"embedding_service"},
)
def project_embeddings_asset(context) -> Output[dict]:
    """Generate embeddings for all projects from dbt ml_project_embeddings table."""
    
    start_time = time.time()
    embedding_service = context.resources.embedding_service
    

    with get_db_session() as db:
        result = db.execute(text("""
            SELECT project_id, embedding_text 
            FROM "embed_PROJECTS_temp" 
            WHERE embedding_text IS NOT NULL 
            AND LENGTH(TRIM(embedding_text)) > 20
            ORDER BY created_at DESC
        """))
        embedding_data = result.fetchall()
    
    if not embedding_data:
        raise Exception("No embedding data found from dbt model")
    
    log.info(f"📊 Generating embeddings for {len(embedding_data)} projects from dbt")
    

    with get_db_session() as db:
        db.execute(text("""
            INSERT INTO "embed_PROJECTS" (project_id, embedding_text, last_ingested_at, created_at)
            SELECT project_id, embedding_text, last_ingested_at, created_at
            FROM "embed_PROJECTS_temp"
            ON CONFLICT (project_id) DO UPDATE SET
                embedding_text = EXCLUDED.embedding_text,
                last_ingested_at = EXCLUDED.last_ingested_at,
                created_at = EXCLUDED.created_at
        """))
        log.info(f"📋 Copied data from embed_PROJECTS_temp to embed_PROJECTS")
    
    # Extract texts and IDs (dbt has already done the enrichment)
    project_ids = [str(row[0]) for row in embedding_data]
    texts = [row[1] for row in embedding_data]
    
    log.info(f"📝 Using pre-processed embedding texts from dbt model")
    
    # Generate embeddings
    embeddings = embedding_service.encode_batch(texts)

    # Stocker embeddings dans embed_PROJECTS avec pgvector
    with get_db_session() as db:
        for project_id, embedding in zip(project_ids, embeddings):
            # Convertir numpy array en liste pour pgvector
            embedding_list = embedding.tolist()
            
            db.execute(text("""
                UPDATE "embed_PROJECTS" 
                SET embedding_vector = :embedding
                WHERE project_id = :project_id
            """), {
                "embedding": embedding_list,
                "project_id": project_id
            })
            
        log.info(f"💾 Stored {len(embeddings)} embeddings in embed_PROJECTS with pgvector")

    # Prepare artifacts and metadata
    artifacts = {
        "project_embeddings": embeddings,
        "project_ids": project_ids,
        "metadata": {
            "count": len(embeddings),
            "model": "all-MiniLM-L6-v2",
            "dimensions": MINILM_DIMENSIONS,
            "generation_time": time.time() - start_time,
        }
    }
    

    
    # Save with MLflow model persistence
    model_uri = mlflow_model_persistence.save_embeddings("project_embeddings", artifacts)
    log.info(f"💾 Saved project embeddings artifacts with MLflow: {model_uri}")

    return Output(
        artifacts,
        metadata={
            "count": len(embeddings),
            "model": "all-MiniLM-L6-v2",
            "dimensions": MINILM_DIMENSIONS,
            "generation_time": time.time() - start_time,
        }
    )


@asset(
    name="hybrid_project_embeddings",
    description="Generate hybrid embeddings combining semantic embeddings with structured features for better User↔Project similarity",
    ins={"semantic_embeddings": AssetIn("project_embeddings", dagster_type=Nothing)},
    group_name="ml_embeddings",
    compute_kind="ml",
    required_resource_keys={"embedding_service"},
)
def hybrid_project_embeddings_asset(context) -> Output[dict]:
    """Generate hybrid vectors combining semantic embeddings with structured features."""
    
    start_time = time.time()
    
            # Load enriched data from dbt with structured features
    with get_db_session() as db:
        result = db.execute(text("""
            SELECT 
                project_id, 
                embedding_text,
                structured_categories,
                structured_tech_stacks,
                structured_language,
                structured_stars,
                structured_forks
            FROM "embed_PROJECTS_temp" 
            WHERE embedding_text IS NOT NULL 
            AND LENGTH(TRIM(embedding_text)) > 20
            ORDER BY created_at DESC
        """))
        hybrid_data = result.fetchall()
    
    if not hybrid_data:
        raise Exception("No hybrid embedding data found from dbt model")
    
    log.info(f"🔬 Generating hybrid embeddings for {len(hybrid_data)} projects")
    
            # Extract data
    project_ids = [str(row[0]) for row in hybrid_data]
    texts = [row[1] for row in hybrid_data]
    categories_list = [row[2] for row in hybrid_data]
    tech_stacks_list = [row[3] for row in hybrid_data]
    languages = [row[4] for row in hybrid_data]
    stars = [row[5] for row in hybrid_data]
    forks = [row[6] for row in hybrid_data]
    
            # Generate semantic embeddings
    embedding_service = context.resources.embedding_service
    semantic_embeddings = embedding_service.encode_batch(texts)
    
            # Create normalized structured features (16 dimensions)
    structured_features = []
    for i in range(len(project_ids)):
        # Encode categories (simplified one-hot)
        category_features = [0.0] * 8  # 8 main categories
        if categories_list[i]:
            for cat in categories_list[i]:
                if "ia" in cat.lower() or "machine" in cat.lower():
                    category_features[0] = 1.0
                elif "web" in cat.lower() or "frontend" in cat.lower():
                    category_features[1] = 1.0
                elif "mobile" in cat.lower() or "app" in cat.lower():
                    category_features[2] = 1.0
                elif "data" in cat.lower() or "analytics" in cat.lower():
                    category_features[3] = 1.0
                elif "security" in cat.lower() or "crypto" in cat.lower():
                    category_features[4] = 1.0
                elif "game" in cat.lower() or "gaming" in cat.lower():
                    category_features[5] = 1.0
                elif "blockchain" in cat.lower() or "crypto" in cat.lower():
                    category_features[6] = 1.0
                else:
                    category_features[7] = 1.0  # Autres
        
        # Encode tech stacks (one-hot based on TECH_STACKS from reference_assets.py)
        tech_features = [0.0] * 30  # 30 tech stacks (16 langages + 14 techs)
        if tech_stacks_list[i]:
            for tech in tech_stacks_list[i]:
                tech_lower = tech.lower()
                # Mapping based on TECH_STACKS
                tech_mapping = {
                    "python": 0, "javascript": 1, "typescript": 2, "java": 3, "go": 4, "rust": 5,
                    "c++": 6, "c#": 7, "php": 8, "c": 9, "kotlin": 10, "swift": 11, "ruby": 12,
                    "dart": 13, "html": 14, "css": 15, "react": 16, "node.js": 17, "next.js": 18,
                    "angular": 19, "vue.js": 20, "django": 21, "flask": 22, "express": 23,
                    "nest.js": 24, "spring boot": 25, "laravel": 26, "docker": 27, "kubernetes": 28,
                    "postgresql": 29
                }
                for tech_name, idx in tech_mapping.items():
                    if tech_name in tech_lower:
                        tech_features[idx] = 1.0
                        break
        
        # Combine all structured features (38 dimensions)
        structured_feature_vector = category_features + tech_features
        structured_features.append(structured_feature_vector)
    
            # Create hybrid vectors (MINILM_DIMENSIONS + 38 = 422 dimensions)
    hybrid_vectors = []
    for i in range(len(semantic_embeddings)):
        semantic_vec = semantic_embeddings[i]
        structured_vec = np.array(structured_features[i], dtype=np.float32)
        hybrid_vec = np.concatenate([semantic_vec, structured_vec])
        hybrid_vectors.append(hybrid_vec)
    
    # Stocker dans la nouvelle table hybrid_PROJECT_embeddings
    with get_db_session() as db:
        for i, project_id in enumerate(project_ids):
            semantic_list = semantic_embeddings[i].tolist()
            structured_dict = {
                "categories": categories_list[i] or [],
                "tech_stacks": tech_stacks_list[i] or [],
                "language": languages[i]
            }
            hybrid_list = hybrid_vectors[i].tolist()
            weights_dict = {
                "tech_stacks": settings.RECOMMENDATION_TECH_WEIGHT,
                "categories": settings.RECOMMENDATION_CATEGORY_WEIGHT,
                "semantic": settings.RECOMMENDATION_SEMANTIC_WEIGHT
            }
            
            db.execute(text("""
                INSERT INTO "hybrid_PROJECT_embeddings" 
                (project_id, semantic_embedding, structured_features, hybrid_vector, similarity_weights, last_ingested_at, created_at)
                VALUES (:project_id, :semantic, :structured, :hybrid, :weights, NOW(), NOW())
                ON CONFLICT (project_id) DO UPDATE SET
                    semantic_embedding = EXCLUDED.semantic_embedding,
                    structured_features = EXCLUDED.structured_features,
                    hybrid_vector = EXCLUDED.hybrid_vector,
                    similarity_weights = EXCLUDED.similarity_weights,
                    last_ingested_at = NOW()
            """), {
                "project_id": project_id,
                "semantic": semantic_list,
                "structured": json.dumps(structured_dict),
                "hybrid": hybrid_list,
                "weights": json.dumps(weights_dict)
            })
    
    log.info(f"💾 Stored {len(hybrid_vectors)} hybrid embeddings in hybrid_PROJECT_embeddings")
    
    # Prepare artifacts for MLflow persistence
    artifacts = {
        "hybrid_embeddings": np.array(hybrid_vectors),
        "project_ids": project_ids,
        "semantic_embeddings": semantic_embeddings,
        "structured_features": structured_features,
        "metadata": {
            "count": len(hybrid_vectors),
            "semantic_dimensions": MINILM_DIMENSIONS,
            "structured_dimensions": 38,
            "hybrid_dimensions": MINILM_DIMENSIONS + 38,
            "generation_time": time.time() - start_time,
        },
        "weights": {
            "tech_stacks": settings.RECOMMENDATION_TECH_WEIGHT,
            "categories": settings.RECOMMENDATION_CATEGORY_WEIGHT,
            "semantic": settings.RECOMMENDATION_SEMANTIC_WEIGHT
        }
    }
    
    # Save with MLflow model persistence
    model_uri = mlflow_model_persistence.save_embeddings("hybrid_project_embeddings", artifacts)
    log.info(f"💾 Saved hybrid project embeddings artifacts with MLflow: {model_uri}")
    
    return Output(
        artifacts,
        metadata=artifacts["metadata"]
    )



