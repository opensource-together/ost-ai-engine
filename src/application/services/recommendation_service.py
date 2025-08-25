"""
Recommendation service using configurable parameters from environment variables.
"""

import numpy as np
from sqlalchemy import create_engine, text
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Optional
from src.infrastructure.config import settings
from src.infrastructure.logger import log

logger = log


class RecommendationService:
    """Service for generating user-project recommendations with configurable parameters."""
    
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.logger = logger
        
        # Load configurable parameters
        self.semantic_weight = settings.RECOMMENDATION_SEMANTIC_WEIGHT
        self.category_weight = settings.RECOMMENDATION_CATEGORY_WEIGHT
        self.tech_weight = settings.RECOMMENDATION_TECH_WEIGHT
        self.popularity_weight = settings.RECOMMENDATION_POPULARITY_WEIGHT
        self.top_n = settings.RECOMMENDATION_TOP_N
        self.min_similarity = settings.RECOMMENDATION_MIN_SIMILARITY
        self.max_projects = settings.RECOMMENDATION_MAX_PROJECTS
        self.popularity_threshold = settings.RECOMMENDATION_POPULARITY_THRESHOLD
        
        self.logger.info(f"RecommendationService initialized with weights: "
                        f"semantic={self.semantic_weight}, category={self.category_weight}, "
                        f"tech={self.tech_weight}, popularity={self.popularity_weight}")

    def parse_vector_string(self, vector_str: Optional[str]) -> Optional[np.ndarray]:
        """Parse vector string from PostgreSQL to numpy array."""
        if vector_str is None:
            return None
        
        # Handle both formats: {0.1,0.2,...} and [0.1,0.2,...]
        vector_str = vector_str.strip('{}[]')
        values = vector_str.split(',')
        
        try:
            return np.array([float(x) for x in values])
        except (ValueError, TypeError):
            return None

    def get_user_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user profile with embeddings and metadata."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        u.id,
                        u.username,
                        u.bio,
                        u.location,
                        u.company,
                        eu.embedding_vector,
                        eu.categories,
                        array_agg(ts.name) as tech_stacks
                    FROM "USER" u
                    JOIN "embed_USERS" eu ON u.id = eu.user_id
                    LEFT JOIN "USER_TECH_STACK" uts ON u.id = uts.user_id
                    LEFT JOIN "TECH_STACK" ts ON uts.tech_stack_id = ts.id
                    WHERE u.username = :username
                    GROUP BY u.id, u.username, u.bio, u.location, u.company, eu.embedding_vector, eu.categories
                """), {"username": username})
                
                user_data = result.fetchone()
                if not user_data:
                    return None
                
                user_id, username, bio, location, company, embedding_vector, categories, tech_stacks = user_data
                
                # Parse embedding
                embedding_array = self.parse_vector_string(embedding_vector)
                if embedding_array is None:
                    return None
                
                return {
                    "user_id": str(user_id),
                    "username": username,
                    "bio": bio,
                    "location": location,
                    "company": company,
                    "embedding": embedding_array,
                    "categories": categories or [],
                    "tech_stacks": tech_stacks or []
                }
                
        except Exception as e:
            self.logger.error(f"Error getting user profile for {username}: {e}")
            return None

    def get_projects_with_metadata(self) -> List[Dict[str, Any]]:
        """Get projects with rich metadata for recommendations."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        p.id,
                        p.full_name,
                        p.title,
                        p.description,
                        p.primary_language,
                        p.stargazers_count,
                        p.topics,
                        ep.embedding_vector,
                        array_agg(DISTINCT c.name) as categories,
                        array_agg(DISTINCT ts.name) as tech_stacks
                    FROM "PROJECT" p
                    JOIN "embed_PROJECTS" ep ON p.id = ep.project_id
                    LEFT JOIN "PROJECT_CATEGORY" pc ON p.id = pc.project_id
                    LEFT JOIN "CATEGORY" c ON pc.category_id = c.id
                    LEFT JOIN "PROJECT_TECH_STACK" pts ON p.id = pts.project_id
                    LEFT JOIN "TECH_STACK" ts ON pts.tech_stack_id = ts.id
                    WHERE ep.embedding_vector IS NOT NULL
                    GROUP BY p.id, p.full_name, p.title, p.description, p.primary_language, p.stargazers_count, p.topics, ep.embedding_vector
                    ORDER BY p.stargazers_count DESC
                    LIMIT :max_projects
                """), {"max_projects": self.max_projects})
                
                projects = []
                for row in result.fetchall():
                    project_id, full_name, title, description, language, stars, topics, embedding_vector, categories, tech_stacks = row
                    
                    # Parse embedding
                    embedding_array = self.parse_vector_string(embedding_vector)
                    if embedding_array is None:
                        continue
                    
                    projects.append({
                        "project_id": str(project_id),
                        "full_name": full_name,
                        "title": title,
                        "description": description,
                        "language": language,
                        "stars": stars or 0,
                        "topics": topics or [],
                        "embedding": embedding_array,
                        "categories": categories or [],
                        "tech_stacks": tech_stacks or []
                    })
                
                return projects
                
        except Exception as e:
            self.logger.error(f"Error getting projects: {e}")
            return []

    def calculate_similarity_scores(self, user_profile: Dict[str, Any], projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate similarity scores for all projects."""
        user_embedding = user_profile["embedding"].reshape(1, -1)
        user_categories = set(user_profile["categories"])
        user_tech_stacks = set(user_profile["tech_stacks"])
        
        scored_projects = []
        
        for project in projects:
            # Semantic similarity
            semantic_similarity = cosine_similarity(user_embedding, project["embedding"].reshape(1, -1))[0][0]
            
            # Category overlap (Jaccard similarity)
            category_overlap = 0
            if user_categories and project["categories"]:
                project_categories = set(project["categories"])
                if user_categories and project_categories:
                    intersection = user_categories.intersection(project_categories)
                    union = user_categories.union(project_categories)
                    category_overlap = len(intersection) / len(union) if union else 0
            
            # Tech stack overlap (Jaccard similarity)
            tech_overlap = 0
            if user_tech_stacks and project["tech_stacks"]:
                project_tech_stacks = set(project["tech_stacks"])
                if user_tech_stacks and project_tech_stacks:
                    intersection = user_tech_stacks.intersection(project_tech_stacks)
                    union = user_tech_stacks.union(project_tech_stacks)
                    tech_overlap = len(intersection) / len(union) if union else 0
            
            # Popularity score (normalized)
            popularity_score = min(project["stars"] / self.popularity_threshold, 1.0)
            
            # Combined score
            combined_score = (
                semantic_similarity * self.semantic_weight +
                category_overlap * self.category_weight +
                tech_overlap * self.tech_weight +
                popularity_score * self.popularity_weight
            )
            
            # Only include if above minimum similarity
            if combined_score >= self.min_similarity:
                scored_projects.append({
                    **project,
                    "semantic_similarity": semantic_similarity,
                    "category_overlap": category_overlap,
                    "tech_overlap": tech_overlap,
                    "popularity_score": popularity_score,
                    "combined_score": combined_score
                })
        
        # Sort by combined score
        scored_projects.sort(key=lambda x: x["combined_score"], reverse=True)
        return scored_projects

    def get_recommendations(self, username: str, top_n: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get personalized recommendations for a user."""
        if top_n is None:
            top_n = self.top_n
            
        self.logger.info(f"Getting recommendations for user: {username}")
        
        # Get user profile
        user_profile = self.get_user_profile(username)
        if not user_profile:
            self.logger.warning(f"User {username} not found or has no valid embedding")
            return None
        
        # Get projects
        projects = self.get_projects_with_metadata()
        if not projects:
            self.logger.warning("No projects found with embeddings")
            return None
        
        self.logger.info(f"Found {len(projects)} projects for recommendations")
        
        # Calculate scores
        scored_projects = self.calculate_similarity_scores(user_profile, projects)
        
        # Get top recommendations
        top_recommendations = scored_projects[:top_n]
        
        return {
            "user": {
                "username": user_profile["username"],
                "bio": user_profile["bio"],
                "location": user_profile["location"],
                "company": user_profile["company"],
                "categories": user_profile["categories"],
                "tech_stacks": user_profile["tech_stacks"]
            },
            "recommendations": top_recommendations,
            "total_projects_considered": len(projects),
            "total_projects_scored": len(scored_projects),
            "model_parameters": {
                "semantic_weight": self.semantic_weight,
                "category_weight": self.category_weight,
                "tech_weight": self.tech_weight,
                "popularity_weight": self.popularity_weight,
                "min_similarity": self.min_similarity,
                "popularity_threshold": self.popularity_threshold
            }
        }

    def update_model_parameters(self, **kwargs):
        """Update model parameters dynamically."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                self.logger.info(f"Updated {key} to {value}")
            else:
                self.logger.warning(f"Unknown parameter: {key}")


# Global service instance
recommendation_service = RecommendationService()
