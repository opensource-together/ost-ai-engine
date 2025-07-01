import pickle
from contextlib import asynccontextmanager
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


# Pydantic Models
class RecommendationResponse(BaseModel):
    """Response model for project recommendations."""

    user_id: int = Field(
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application's lifespan events for model loading.
    """
    log.info("Starting API and loading models...")
    try:
        app.state.similarity_matrix = np.load(settings.SIMILARITY_MATRIX_PATH)
        log.info(
            "Successfully loaded similarity matrix from %s",
            settings.SIMILARITY_MATRIX_PATH,
        )

        with open(settings.VECTORIZER_PATH, "rb") as f:
            app.state.vectorizer = pickle.load(f)
        log.info("Successfully loaded vectorizer from %s", settings.VECTORIZER_PATH)

        # Load the projects list (needed for recommendations)
        loader = ProjectDataLoadingService()
        app.state.projects = loader.get_all_projects()
        log.info("Successfully loaded %d projects", len(app.state.projects))

    except FileNotFoundError:
        log.warning(
            "Model artifacts not found. API is starting without models. "
            "Run the training pipeline to generate them."
        )
        app.state.similarity_matrix = None
        app.state.vectorizer = None
        app.state.projects = []

    yield
    # Cleanup logic can go here if needed on shutdown
    log.info("API shutting down.")


app = FastAPI(
    title="Data Engine API",
    description=(
        "API for the recommendation engine that suggests relevant projects "
        "to users based on their interests and activities."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


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
    user_id: int = Path(
        ..., description="The ID of the user to get recommendations for"
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
        user_id: The ID of the user to get recommendations for
        top_n: Number of recommendations to return (default: 10, max: 50)
        db: Database session (injected dependency)

    Returns:
        RecommendationResponse: List of recommended project IDs with metadata

    Raises:
        HTTPException: 404 if user has no interest profile or 500 if models unavailable
    """
    # Check if models are loaded
    if (
        app.state.similarity_matrix is None
        or app.state.projects is None
        or len(app.state.projects) == 0
    ):
        raise HTTPException(
            status_code=500,
            detail=(
                "Recommendation models are not available. "
                "Please run the training pipeline first."
            ),
        )

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
            projects=app.state.projects,
            similarity_matrix=app.state.similarity_matrix,
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
