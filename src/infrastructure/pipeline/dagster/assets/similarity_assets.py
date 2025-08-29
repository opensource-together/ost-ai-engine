"""Dagster assets for calculating and storing User↔Project similarities."""

import time
import json
import numpy as np
from typing import List, Dict, Any
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict

from dagster import AssetIn, Nothing, Output, asset
from sqlalchemy import text

from src.infrastructure.config import settings
from src.infrastructure.logger import log
from src.infrastructure.postgres.database import get_db_session


@asset(
    name="user_project_similarities",
    description="Calculate and store similarity scores between all users and projects using hybrid embeddings",
    ins={
        "user_embeddings": AssetIn("user_embeddings", dagster_type=Nothing),
        "hybrid_embeddings": AssetIn("project_hybrid_embeddings", dagster_type=Nothing),
        "similarity_data": AssetIn("dbt_user_project_similarities", dagster_type=Nothing)
    },
    group_name="ml_similarities",
    compute_kind="ml",
)
def user_project_similarities_asset(context) -> Output[dict]:
    """Calculate similarity scores between all users and projects using hybrid approach."""
    
    start_time = time.time()
    
    log.info(f"🚀 Starting User↔Project similarity calculations")
    log.info(f"⚖️ Using weights - Semantic: {settings.RECOMMENDATION_SEMANTIC_WEIGHT}, "
            f"Category: {settings.RECOMMENDATION_CATEGORY_WEIGHT}, "
            f"Tech: {settings.RECOMMENDATION_TECH_WEIGHT}, "
            f"Popularity: {settings.RECOMMENDATION_POPULARITY_WEIGHT}")
    log.info(f"📊 Will store top {settings.RECOMMENDATION_TOP_N} projects per user")
    
    # Load user embeddings from embed_USERS
    with get_db_session() as db:
        user_embeddings_result = db.execute(text("""
            SELECT user_id, embedding_vector 
            FROM "embed_USERS" 
            WHERE embedding_vector IS NOT NULL
        """))
        user_embeddings_data = user_embeddings_result.fetchall()
    
    # Load project embeddings from embed_PROJECTS
    with get_db_session() as db:
        project_embeddings_result = db.execute(text("""
            SELECT project_id, embedding_vector 
            FROM "embed_PROJECTS" 
            WHERE embedding_vector IS NOT NULL
        """))
        project_embeddings_data = project_embeddings_result.fetchall()
    
    # Create lookup dictionaries for embeddings
    user_embeddings_dict = {}
    for user_id, embedding_vector in user_embeddings_data:
        if isinstance(embedding_vector, str):
            user_embeddings_dict[user_id] = np.array(json.loads(embedding_vector), dtype=np.float32)
        else:
            user_embeddings_dict[user_id] = np.array(embedding_vector, dtype=np.float32)
    
    project_embeddings_dict = {}
    for project_id, embedding_vector in project_embeddings_data:
        if isinstance(embedding_vector, str):
            project_embeddings_dict[project_id] = np.array(json.loads(embedding_vector), dtype=np.float32)
        else:
            project_embeddings_dict[project_id] = np.array(embedding_vector, dtype=np.float32)
    
    log.info(f"📊 Loaded {len(user_embeddings_dict)} user embeddings and {len(project_embeddings_dict)} project embeddings")
    
    # Load similarity data from dbt model (user_project_similarities_temp)
    with get_db_session() as db:
        similarity_data_result = db.execute(text("""
            SELECT 
                user_id,
                project_id,
                username,
                project_title,
                user_categories,
                project_categories,
                user_tech_stacks,
                project_tech_stacks,
                stargazers_count,
                primary_language
            FROM "user_project_similarities_temp"
        """))
        similarity_data = similarity_data_result.fetchall()
    
    if not similarity_data:
        raise Exception("No similarity data found from dbt model user_project_similarities_temp")
    
    log.info(f"📊 Processing {len(similarity_data)} user-project combinations from dbt model")
    
    # Clear existing similarities from final table (USER_PROJECT_SIMILARITY)
    with get_db_session() as db:
        db.execute(text("DELETE FROM \"USER_PROJECT_SIMILARITY\""))
        log.info("🗑️ Cleared existing similarity scores from USER_PROJECT_SIMILARITY")
    
    # Calculate similarities and store in memory for sorting
    user_similarities = defaultdict(list)  # user_id -> list of (project_id, score, metadata)
    
    for i, row in enumerate(similarity_data):
        try:
            user_id, project_id, username, project_title, user_categories, project_categories, user_tech_stacks, project_tech_stacks, stars, language = row
            
            # Progress update every 1000 combinations
            if (i + 1) % 1000 == 0:
                log.info(f"📈 Progress: {i+1}/{len(similarity_data)} combinations processed")
            
            # Get embeddings for this user-project pair
            user_embedding = user_embeddings_dict.get(user_id)
            project_embedding = project_embeddings_dict.get(project_id)
            
            if user_embedding is None or project_embedding is None:
                log.warning(f"⚠️ Missing embeddings for user {user_id} or project {project_id}")
                continue
            
            # Calculate semantic similarity using cosine similarity
            semantic_similarity = cosine_similarity(
                user_embedding.reshape(1, -1), 
                project_embedding.reshape(1, -1)
            )[0][0]
            
            # Ensure similarity is between 0 and 1 and convert to Python float
            semantic_similarity = float(max(0.0, min(1.0, semantic_similarity)))
            
            # Convert arrays to sets for overlap calculations
            user_categories_set = set(user_categories or [])
            project_categories_set = set(project_categories or [])
            user_tech_stacks_set = set(user_tech_stacks or [])
            project_tech_stacks_set = set(project_tech_stacks or [])
            
            # Calculate category overlap (Jaccard similarity)
            if user_categories_set and project_categories_set:
                category_overlap = len(user_categories_set.intersection(project_categories_set)) / len(user_categories_set.union(project_categories_set))
            else:
                category_overlap = 0.0
            
            # Calculate tech stack overlap (Jaccard similarity)
            if user_tech_stacks_set and project_tech_stacks_set:
                tech_overlap = len(user_tech_stacks_set.intersection(project_tech_stacks_set)) / len(user_tech_stacks_set.union(project_tech_stacks_set))
            else:
                tech_overlap = 0.0
            
            # Calculate popularity score (normalized)
            popularity_score = min((stars or 0) / settings.RECOMMENDATION_POPULARITY_THRESHOLD, 1.0)
            
            # Calculate combined score using environment weights
            combined_score = (
                semantic_similarity * settings.RECOMMENDATION_SEMANTIC_WEIGHT +
                category_overlap * settings.RECOMMENDATION_CATEGORY_WEIGHT +
                tech_overlap * settings.RECOMMENDATION_TECH_WEIGHT +
                popularity_score * settings.RECOMMENDATION_POPULARITY_WEIGHT
            )
            
            # Only consider if above minimum similarity threshold
            if combined_score >= settings.RECOMMENDATION_MIN_SIMILARITY:
                # Store in memory for sorting
                user_similarities[user_id].append({
                    'project_id': project_id,
                    'similarity_score': combined_score,
                    'semantic_similarity': semantic_similarity,
                    'category_similarity': category_overlap,
                    'tech_similarity': tech_overlap,
                    'popularity_score': popularity_score,
                    'username': username,
                    'project_title': project_title
                })
            
        except Exception as e:
            log.error(f"❌ Error processing row {i+1}: {e}")
            raise
    
    # Sort and store top N projects per user
    total_stored = 0
    users_processed = 0
    
    with get_db_session() as db:
        for user_id, similarities in user_similarities.items():
            # Sort by similarity score (descending) and take top N
            top_similarities = sorted(similarities, key=lambda x: x['similarity_score'], reverse=True)[:settings.RECOMMENDATION_TOP_N]
            
            # Insert top N projects for this user
            for similarity in top_similarities:
                db.execute(text("""
                    INSERT INTO "USER_PROJECT_SIMILARITY" 
                    (user_id, project_id, similarity_score, semantic_similarity, category_similarity, language_similarity, popularity_similarity)
                    VALUES (:user_id, :project_id, :similarity_score, :semantic_similarity, :category_similarity, :language_similarity, :popularity_similarity)
                """), {
                    "user_id": user_id,
                    "project_id": similarity['project_id'],
                    "similarity_score": similarity['similarity_score'],
                    "semantic_similarity": similarity['semantic_similarity'],
                    "category_similarity": similarity['category_similarity'],
                    "language_similarity": similarity['tech_similarity'],  # Using tech_overlap for language_similarity
                    "popularity_similarity": similarity['popularity_score']
                })
                total_stored += 1
            
            users_processed += 1
            log.info(f"✅ User {similarity['username']}: stored top {len(top_similarities)} projects (best score: {top_similarities[0]['similarity_score']:.3f}, semantic: {top_similarities[0]['semantic_similarity']:.3f})")
    
    # Final statistics from final table
    with get_db_session() as db:
        avg_score = db.execute(text("SELECT AVG(similarity_score) FROM \"USER_PROJECT_SIMILARITY\"")).scalar()
        avg_semantic = db.execute(text("SELECT AVG(semantic_similarity) FROM \"USER_PROJECT_SIMILARITY\"")).scalar()
    
    generation_time = time.time() - start_time
    
    log.info(f"✅ Similarity calculation completed!")
    log.info(f"📊 Total combinations processed: {len(similarity_data)}")
    log.info(f"👥 Users processed: {users_processed}")
    log.info(f"💾 Top {settings.RECOMMENDATION_TOP_N} projects stored per user: {total_stored}")
    log.info(f"📈 Average similarity score: {avg_score:.3f}")
    log.info(f"🧠 Average semantic similarity: {avg_semantic:.3f}")
    log.info(f"⏱️ Generation time: {generation_time:.2f}s")
    
    return Output(
        {
            "total_combinations": len(similarity_data),
            "users_processed": users_processed,
            "similarities_stored": total_stored,
            "average_score": avg_score,
            "average_semantic": avg_semantic,
            "generation_time": generation_time,
            "top_n_per_user": settings.RECOMMENDATION_TOP_N
        },
        metadata={
            "total_combinations": len(similarity_data),
            "users_processed": users_processed,
            "similarities_stored": total_stored,
            "average_score": avg_score,
            "average_semantic": avg_semantic,
            "generation_time": generation_time,
            "top_n_per_user": settings.RECOMMENDATION_TOP_N
        }
    )
