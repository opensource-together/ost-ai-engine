import pickle
from uuid import UUID

import numpy as np
from fastapi import Depends, FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.application.services.project_data_loader import ProjectDataLoadingService
from src.application.services.recommendation import RecommendationService
from src.application.services.user_interest_profile import UserInterestProfileService
from src.infrastructure.config import settings
from src.infrastructure.logger import log
from src.infrastructure.postgres.database import SessionLocal

# Global model storage (this persists across requests)
MODEL_STORE = {
    "similarity_matrix": None,
    "vectorizer": None,
    "projects": []
}

# Pydantic Models
class RecommendationResponse(BaseModel):
    """Response model for project recommendations."""

    user_id: UUID = Field(
        ..., description="The user ID for whom recommendations were generated"
    )
    recommended_projects: list[UUID] = Field(
        ..., description="List of recommended project IDs"
    )
    total_recommendations: int = Field(
        ..., description="Number of recommendations returned"
    )

    class Config:
        json_encoders = {UUID: str}


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="API status")


class ErrorResponse(BaseModel):
    """Response model for errors."""

    detail: str = Field(..., description="Error message")


# Database dependency
def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def startup_event():
    """Load models on startup."""
    log.info("Starting API and loading models...")

    try:
        # Load similarity matrix
        log.info("Loading similarity matrix...")
        similarity_matrix_path = settings.get_absolute_model_path(
            settings.SIMILARITY_MATRIX_PATH
        )
        MODEL_STORE["similarity_matrix"] = np.load(similarity_matrix_path)
        log.info(
            "✅ Successfully loaded similarity matrix: shape %s",
            MODEL_STORE["similarity_matrix"].shape,
        )

        # Load vectorizer
        log.info("Loading vectorizer...")
        vectorizer_path = settings.get_absolute_model_path(settings.VECTORIZER_PATH)
        with open(vectorizer_path, "rb") as f:
            MODEL_STORE["vectorizer"] = pickle.load(f)
        log.info("✅ Successfully loaded vectorizer")

        # Load projects
        log.info("Loading projects...")
        loader = ProjectDataLoadingService()
        MODEL_STORE["projects"] = loader.get_all_projects()
        log.info("✅ Successfully loaded %d projects", len(MODEL_STORE["projects"]))

        # Final verification
        if (MODEL_STORE["similarity_matrix"] is not None and
            MODEL_STORE["vectorizer"] is not None and
            MODEL_STORE["projects"] and len(MODEL_STORE["projects"]) > 0):
            log.info("🎉 All models loaded successfully!")
        else:
            log.warning("⚠️ Some models failed to load properly")

    except FileNotFoundError as e:
        log.warning("❌ Model artifacts not found: %s", str(e))
        MODEL_STORE["similarity_matrix"] = None
        MODEL_STORE["vectorizer"] = None
        MODEL_STORE["projects"] = []
    except Exception as e:
        log.error("❌ Error loading models or projects: %s", str(e))
        MODEL_STORE["similarity_matrix"] = None
        MODEL_STORE["vectorizer"] = None
        MODEL_STORE["projects"] = []


app = FastAPI(
    title="Data Engine API",
    description=(
        "API for the recommendation engine that suggests relevant projects "
        "to users based on their interests and activities."
    ),
    version="0.1.0",
)

# Register startup event
app.add_event_handler("startup", startup_event)


@app.get(
    "/health",
    tags=["Health"],
    response_model=HealthResponse,
    summary="Health Check",
    description="Check if the API is running and models are loaded",
)
async def health_check():
    """
    Health check endpoint to ensure the API is running.
    """
    return HealthResponse(status="ok")


@app.get(
    "/recommendations/{user_id}",
    tags=["Recommendations"],
    response_model=RecommendationResponse,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "User not found or no interest profile",
        },
        500: {
            "model": ErrorResponse,
            "description": "Model not available or internal error",
        },
    },
    summary="Get Project Recommendations",
    description=(
        "Get personalized project recommendations for a user based on their "
        "contributions, applications, and team memberships"
    ),
)
async def get_recommendations(
    user_id: UUID = Path(
        ..., description="The UUID of the user to get recommendations for"
    ),
    top_n: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Number of recommendations to return (1-50)",
    ),
    db: Session = Depends(get_db),
):
    """
    Get personalized project recommendations for a user.

    This endpoint analyzes the user's interest profile (based on their contributions,
    applications, and team memberships) and uses machine learning to find similar
    projects that the user might be interested in.

    Args:
        user_id: The UUID of the user to get recommendations for
        top_n: Number of recommendations to return (default: 10, max: 50)
        db: Database session (injected dependency)

    Returns:
        RecommendationResponse: List of recommended project IDs with metadata

    Raises:
        HTTPException: 404 if user has no interest profile or 500 if models unavailable
    """
    # Check if models are loaded from startup
    if (
        MODEL_STORE["similarity_matrix"] is None
        or MODEL_STORE["projects"] is None
        or len(MODEL_STORE["projects"]) == 0
    ):
        raise HTTPException(
            status_code=500,
            detail=(
                "Recommendation models are not available. "
                "Please run the training pipeline first."
            ),
        )

    # Use models from startup
    similarity_matrix = MODEL_STORE["similarity_matrix"]
    projects = MODEL_STORE["projects"]

    try:
        # Get user's interest profile
        profile_service = UserInterestProfileService(db)
        interested_project_ids = profile_service.get_user_interest_profile(user_id)

        if not interested_project_ids:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No interest profile found for user {user_id}. "
                    "User needs to interact with projects first."
                ),
            )

        # Generate recommendations
        recommendation_service = RecommendationService()
        recommended_project_ids = recommendation_service.get_recommendations(
            interested_project_ids=interested_project_ids,
            projects=projects,
            similarity_matrix=similarity_matrix,
            top_n=top_n,
        )

        return RecommendationResponse(
            user_id=user_id,
            recommended_projects=recommended_project_ids,
            total_recommendations=len(recommended_project_ids),
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        log.error(f"Error generating recommendations for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while generating recommendations.",
        )



