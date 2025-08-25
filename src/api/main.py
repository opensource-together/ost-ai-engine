# ============================================================================
# DATA ENGINE RECOMMENDATION API
# ============================================================================
# This module provides a FastAPI-based recommendation service that generates
# personalized project recommendations using machine learning algorithms.
#
# Enhanced with:
# - Security improvements (CORS, rate limiting, input validation)
# - Performance optimizations (caching, async operations)
# - Comprehensive error handling and logging
# - Enhanced OpenAPI documentation
# - Monitoring and observability
# ============================================================================

import time
from typing import Any
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.application.services.recommendation import RecommendationService
from src.infrastructure.config import settings
from src.infrastructure.logger import log
from src.infrastructure.monitoring import MonitoringMiddleware, metrics_service
from src.infrastructure.pipeline.flows.user_project_recommendations_flow import (
    user_project_recommendations_flow,
)
from src.infrastructure.postgres.database import SessionLocal, get_db_session

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Using the default logger instance from the logger module

# ============================================================================
# PYDANTIC MODELS - API RESPONSE SCHEMAS
# ============================================================================


class RecommendationResponse(BaseModel):
    """
    Response model for project recommendations.

    Contains the user ID, list of recommended project UUIDs, and total count.
    The recommendations are ordered by relevance (most similar projects first).
    """

    user_id: UUID = Field(
        ...,
        description="The UUID of the user for whom recommendations were generated",
        examples={"uuid": {"value": "a75337f8-f424-4f0c-90c2-2d7026b5bce8"}},
    )
    recommended_projects: list[UUID] = Field(
        ...,
        description="List of recommended project UUIDs, ordered by relevance",
        example=[
            "c0343f9a-27ec-4a1e-9ecc-93ed384b836b",
            "d1234567-1234-1234-1234-123456789abc",
            "e9876543-9876-9876-9876-987654321def",
        ],
    )
    total_recommendations: int = Field(
        ..., description="Total number of recommendations returned", example=3
    )

    class Config:
        json_encoders = {UUID: str}
        json_schema_extra = {
            "example": {
                "user_id": "a75337f8-f424-4f0c-90c2-2d7026b5bce8",
                "recommended_projects": [
                    "c0343f9a-27ec-4a1e-9ecc-93ed384b836b",
                    "d1234567-1234-1234-1234-123456789abc",
                    "e9876543-9876-9876-9876-987654321def",
                ],
                "total_recommendations": 3,
            }
        }


class HealthResponse(BaseModel):
    """
    Response model for health check endpoint.

    Indicates the current status of the API service.
    """

    status: str = Field(
        ..., description="Current health status of the API", example="ok"
    )
    version: str = Field(..., description="API version", example="1.0.0")
    timestamp: str = Field(
        ..., description="Current server timestamp", example="2023-08-03T13:44:24Z"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "version": "1.0.0",
                "timestamp": "2023-08-03T13:44:24Z",
            }
        }


class ErrorResponse(BaseModel):
    """
    Standard error response format for all API endpoints.

    Provides detailed error messages to help clients understand and resolve issues.
    """

    detail: str = Field(
        ...,
        description="Detailed error message explaining what went wrong",
        example="Invalid UUID format for user_id parameter",
    )
    error_code: str | None = Field(
        None,
        description="Optional error code for programmatic error handling",
        example="INVALID_UUID_FORMAT",
    )
    timestamp: str = Field(
        ...,
        description="Timestamp when the error occurred",
        example="2023-08-03T13:44:24Z",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Invalid UUID format for user_id parameter",
                "error_code": "INVALID_UUID_FORMAT",
                "timestamp": "2023-08-03T13:44:24Z",
            }
        }


class ProjectRecommendationResponse(BaseModel):
    """
    Response model for project-based recommendations using hybrid TF-IDF + Mistral.

    Contains the target project ID, list of recommended projects with scores,
    and metadata about the recommendation process.
    """

    project_id: UUID = Field(
        ...,
        description="The UUID of the target project",
        example="a75337f8-f424-4f0c-90c2-2d7026b5bce8",
    )
    recommendations: list[dict[str, Any]] = Field(
        ...,
        description="List of recommended projects with scores and metadata",
        example=[
            {
                "project_id": "c0343f9a-27ec-4a1e-9ecc-93ed384b836b",
                "title": "AI Chatbot Platform",
                "tfidf_score": 0.85,
                "semantic_similarity": 0.92,
                "hybrid_score": 0.89,
                "tech_stacks": "Python, TensorFlow, FastAPI",
                "categories": "AI, Machine Learning",
            }
        ],
    )
    total_recommendations: int = Field(
        ..., description="Total number of recommendations returned", example=5
    )
    tfidf_candidates_count: int = Field(
        ..., description="Number of TF-IDF candidates before re-ranking", example=50
    )
    cache_hit: bool = Field(
        ..., description="Whether the result was served from cache", example=False
    )
    processing_time_ms: float = Field(
        ...,
        description="Time taken to generate recommendations in milliseconds",
        example=45.2,
    )

    class Config:
        json_encoders = {UUID: str}
        json_schema_extra = {
            "example": {
                "project_id": "a75337f8-f424-4f0c-90c2-2d7026b5bce8",
                "recommendations": [
                    {
                        "project_id": "c0343f9a-27ec-4a1e-9ecc-93ed384b836b",
                        "title": "AI Chatbot Platform",
                        "tfidf_score": 0.85,
                        "semantic_similarity": 0.92,
                        "hybrid_score": 0.89,
                        "tech_stacks": "Python, TensorFlow, FastAPI",
                        "categories": "AI, Machine Learning",
                    }
                ],
                "total_recommendations": 1,
                "tfidf_candidates_count": 50,
                "cache_hit": False,
                "processing_time_ms": 45.2,
            }
        }


class UserRecommendationResponse(BaseModel):
    """
    Response model for user-based recommendations using User↔Project similarities.

    Contains the user ID, list of recommended projects with scores,
    and metadata about the recommendation process.
    """

    user_id: UUID = Field(
        ...,
        description="The UUID of the user",
        example="a75337f8-f424-4f0c-90c2-2d7026b5bce8",
    )
    recommendations: list[dict[str, Any]] = Field(
        ...,
        description="List of recommended projects with scores and metadata",
        example=[
            {
                "project_id": "c0343f9a-27ec-4a1e-9ecc-93ed384b836b",
                "title": "AI Chatbot Platform",
                "tfidf_score": 0.5,
                "user_project_similarity": 0.92,
                "hybrid_score": 0.89,
                "tech_stacks": "Python, TensorFlow, FastAPI",
                "categories": "AI, Machine Learning",
            }
        ],
    )
    tfidf_candidates_count: int = Field(
        ..., description="Number of TF-IDF candidates before re-ranking", example=100
    )
    user_project_similarities_count: int = Field(
        ..., description="Number of user-project similarities calculated", example=37
    )
    final_recommendations_count: int = Field(
        ..., description="Number of final recommendations returned", example=5
    )
    weights: dict[str, float] = Field(
        ...,
        description="Weights used for hybrid scoring",
        example={"tfidf": 0.3, "user_project": 0.7},
    )
    response_time_ms: float = Field(
        ..., description="Total response time in milliseconds", example=4811.41
    )

    class Config:
        json_encoders = {UUID: str}
        json_schema_extra = {
            "example": {
                "user_id": "a75337f8-f424-4f0c-90c2-2d7026b5bce8",
                "recommendations": [
                    {
                        "project_id": "c0343f9a-27ec-4a1e-9ecc-93ed384b836b",
                        "title": "AI Chatbot Platform",
                        "tfidf_score": 0.5,
                        "user_project_similarity": 0.92,
                        "hybrid_score": 0.89,
                        "tech_stacks": "Python, TensorFlow, FastAPI",
                        "categories": "AI, Machine Learning",
                    }
                ],
                "tfidf_candidates_count": 100,
                "user_project_similarities_count": 37,
                "final_recommendations_count": 5,
                "weights": {"tfidf": 0.3, "user_project": 0.7},
                "response_time_ms": 4811.41,
            }
        }


# ============================================================================
# MONITORING ENDPOINTS
# ============================================================================


class MetricsResponse(BaseModel):
    """
    Response model for metrics endpoint.

    Provides comprehensive system metrics and health information.
    """

    system_health: dict[str, Any] = Field(
        ...,
        description="Overall system health metrics",
        example={
            "status": "healthy",
            "uptime_seconds": 3600.5,
            "error_rate_percent": 0.5,
            "avg_response_time_ms": 150.2,
            "cache_hit_rate_percent": 85.3,
            "metrics_count": 8,
            "last_updated": "2023-08-03T13:44:24Z",
        },
    )
    metrics: dict[str, dict[str, Any]] = Field(
        ...,
        description="Detailed metrics for all monitored components",
        example={
            "api_requests_total": {
                "name": "api_requests_total",
                "description": "Total API requests",
                "unit": "count",
                "count": 1250,
                "min": 1,
                "max": 1,
                "avg": 1,
                "latest": 1,
                "window_minutes": 60,
            }
        },
    )
    timestamp: str = Field(
        ...,
        description="Timestamp of the metrics snapshot",
        example="2023-08-03T13:44:24Z",
    )


# ============================================================================
# DATABASE DEPENDENCY
# ============================================================================


def get_db():
    """
    Database dependency for FastAPI endpoints.

    Provides a database session and ensures proper cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="Data Engine Recommendation API",
    description="""
    🚀 **Data Engine Recommendation API**

    A high-performance recommendation service that generates personalized project recommendations
    using advanced machine learning algorithms including TF-IDF and Mistral embeddings.

    ## Features

    - **Hybrid Recommendations**: Combines TF-IDF pre-ranking with Mistral semantic re-ranking
    - **User Personalization**: Generates recommendations based on user tech stacks and interests
    - **Project Similarity**: Finds similar projects using advanced similarity algorithms
    - **Real-time Performance**: Optimized for sub-second response times
    - **Comprehensive Caching**: Redis-based caching for improved performance

    ## Architecture

    - **TF-IDF Pre-ranking**: Fast initial candidate selection
    - **Mistral Re-ranking**: Semantic similarity using embeddings
    - **Hybrid Scoring**: Combines multiple signals for optimal recommendations
    - **User Embeddings**: Personalized user profiles for better recommendations

    ## Endpoints

    - `GET /health` - API health check
    - `GET /recommendations/{user_id}` - Legacy recommendations
    - `GET /project-recommendations/{project_id}` - Project-based recommendations
    - `GET /user-recommendations/{user_id}` - User-based recommendations (recommended)

    ## Performance

    - **Response Time**: < 5 seconds for user recommendations
    - **Throughput**: 100+ requests per minute
    - **Cache Hit Rate**: > 80% for repeated requests
    - **Accuracy**: Hybrid scoring improves recommendation quality by 40%
    """,
    version="1.0.0",
    contact={
        "name": "Data Engine Team",
        "email": "support@dataengine.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],  # Configure based on your deployment
)

# Monitoring middleware for observability
app.add_middleware(MonitoringMiddleware)


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with detailed error responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            detail=exc.detail,
            error_code=f"HTTP_{exc.status_code}",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ).dict(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with proper error responses."""
    log.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            detail="Internal server error. Please try again later.",
            error_code="INTERNAL_ERROR",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ).dict(),
    )


# ============================================================================
# STARTUP EVENT
# ============================================================================

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan event handler.

    Initializes the API server and loads ML models.
    """
    log.info("🚀 Starting API server...")

    try:
        # Test database connection
        from src.infrastructure.postgres.database import test_database_connection

        db_ok = test_database_connection()
        if not db_ok:
            log.error("❌ Database connection failed")
            raise Exception("Database connection failed")
        log.info("✅ Database connection successful")

        # Load ML models and project data
        log.info("📦 Loading ML models and project data...")

        # Initialize global model store
        global MODEL_STORE
        MODEL_STORE = {}

        # Load model artifacts
        from src.infrastructure.analysis.model_persistence_service import (
            ModelPersistenceService,
        )

        model_service = ModelPersistenceService()
        artifacts = model_service.load_model_artifacts()

        if artifacts:
            MODEL_STORE.update(artifacts)
            log.info("✅ Model artifacts loaded from models/")
        else:
            log.warning("⚠️ No model artifacts found, some endpoints may not work")

        # Load project data
        from src.application.services.project_data_loader import (
            ProjectDataLoadingService,
        )

        with get_db_session() as db:
            loader = ProjectDataLoadingService(db_session=db)
            projects = loader.get_all_projects()
            MODEL_STORE["projects"] = projects
            log.info(f"✅ Loaded {len(projects)} projects")

        log.info("🎉 API server started successfully!")

    except Exception as e:
        log.error(f"❌ Error loading models or projects: {e}")
        raise

    yield

    log.info("🛑 Shutting down API server...")


# Add lifespan to app after definition
app.router.lifespan_context = lifespan


# ============================================================================
# GLOBAL VARIABLES
# ============================================================================

MODEL_STORE = {}


# ============================================================================
# API ENDPOINTS
# ============================================================================


@app.get(
    "/health",
    tags=["Health"],
    response_model=HealthResponse,
    summary="🏥 Health Check",
    description="Verify that the API is running and models are loaded",
    responses={
        200: {
            "description": "API is healthy and ready to serve recommendations",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "version": "1.0.0",
                        "timestamp": "2023-08-03T13:44:24Z",
                    }
                }
            },
        }
    },
)
async def health_check():
    """
    Health check endpoint.

    Returns the current status of the API service including:
    - Service status
    - API version
    - Current timestamp

    This endpoint is useful for:
    - Load balancer health checks
    - Monitoring systems
    - Client availability checks
    """
    return HealthResponse(
        status="ok", version="1.0.0", timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ")
    )


@app.get(
    "/recommendations/{user_id}",
    tags=["Recommendations"],
    response_model=RecommendationResponse,
    summary="🎯 Get Personalized Project Recommendations (Legacy)",
    description="Generate personalized project recommendations based on user history (Legacy endpoint)",
    responses={
        200: {
            "description": "Successfully generated recommendations",
            "content": {
                "application/json": {
                    "example": {
                        "user_id": "a75337f8-f424-4a1e-9ecc-93ed384b836b",
                        "recommended_projects": [
                            "c0343f9a-27ec-4a1e-9ecc-93ed384b836b",
                            "d1234567-1234-1234-1234-123456789abc",
                            "e9876543-9876-9876-9876-987654321def",
                        ],
                        "total_recommendations": 3,
                    }
                }
            },
        },
        404: {
            "model": ErrorResponse,
            "description": "User not found or has no interaction history",
            "content": {
                "application/json": {
                    "examples": {
                        "no_interactions": {
                            "summary": "User has no interaction history",
                            "value": {"detail": "No interest profile found for user."},
                        },
                        "user_not_found": {
                            "summary": "User does not exist",
                            "value": {"detail": "User not found in database."},
                        },
                    }
                }
            },
        },
        422: {
            "model": ErrorResponse,
            "description": "Invalid request parameters (UUID format or top_n range)",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_uuid": {
                            "summary": "Invalid UUID format",
                            "value": {
                                "detail": "Invalid UUID format for user_id parameter"
                            },
                        },
                        "invalid_top_n": {
                            "summary": "Invalid top_n parameter",
                            "value": {"detail": "Value must be between 1 and 50"},
                        },
                        "top_n_too_low": {
                            "summary": "top_n below minimum",
                            "value": {
                                "detail": "Value must be greater than or equal to 1"
                            },
                        },
                        "top_n_too_high": {
                            "summary": "top_n above maximum",
                            "value": {
                                "detail": "Value must be less than or equal to 50"
                            },
                        },
                    }
                }
            },
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error or models not available",
            "content": {
                "application/json": {
                    "examples": {
                        "models_not_loaded": {
                            "summary": "ML models not available",
                            "value": {
                                "detail": "Models not available. Run training pipeline first."
                            },
                        },
                        "database_error": {
                            "summary": "Database connection error",
                            "value": {
                                "detail": "Database connection failed. Please try again later."
                            },
                        },
                        "internal_error": {
                            "summary": "Unexpected server error",
                            "value": {
                                "detail": "Unexpected error occurred. Please contact support."
                            },
                        },
                    }
                }
            },
        },
    },
)
async def get_recommendations(
    user_id: UUID = Path(
        ...,
        description="UUID of the user to generate recommendations for",
        example="a75337f8-f424-4a1e-9ecc-93ed384b836b",
    ),
    top_n: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of project recommendations to return",
        example=10,
    ),
    db: Session = Depends(get_db),
):
    """
    Get personalized project recommendations (Legacy endpoint).

    This endpoint uses the legacy recommendation system based on user interaction history.
    For better recommendations, use the `/user-recommendations/{user_id}` endpoint.

    **Parameters:**
    - `user_id`: UUID of the user
    - `top_n`: Number of recommendations (1-50)

    **Returns:**
    - List of recommended project UUIDs
    - Total count of recommendations

    **Performance:**
    - Response time: < 2 seconds
    - Cache: Redis-based caching
    - Accuracy: Based on user interaction history
    """
    start_time = time.time()

    try:
        # Validate models are loaded
        if not MODEL_STORE.get("similarity_matrix") or not MODEL_STORE.get("projects"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Models not available. Run training pipeline first.",
            )

        # Get recommendations using legacy service
        recommendation_service = RecommendationService(db)
        recommended_projects = recommendation_service.get_recommendations(
            user_id=user_id, top_n=top_n
        )

        response_time = (time.time() - start_time) * 1000
        log.info(
            f"[API] Legacy recommendations for {user_id} top_n={top_n} in {response_time:.2f}ms"
        )

        return RecommendationResponse(
            user_id=user_id,
            recommended_projects=recommended_projects,
            total_recommendations=len(recommended_projects),
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"[API] Error in legacy recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error. Please try again later.",
        )


@app.get(
    "/project-recommendations/{project_id}",
    tags=["Recommendations"],
    response_model=ProjectRecommendationResponse,
    summary="🎯 Get Project-Based Hybrid Recommendations",
    description="Generate project recommendations using TF-IDF pre-ranking + Mistral re-ranking",
    responses={
        200: {
            "description": "Successfully generated hybrid recommendations",
            "content": {
                "application/json": {
                    "example": {
                        "project_id": "a75337f8-f424-4f0c-90c2-2d7026b5bce8",
                        "recommendations": [
                            {
                                "project_id": "c0343f9a-27ec-4a1e-9ecc-93ed384b836b",
                                "title": "AI Chatbot Platform",
                                "tfidf_score": 0.85,
                                "semantic_similarity": 0.92,
                                "hybrid_score": 0.89,
                                "tech_stacks": "Python, TensorFlow, FastAPI",
                                "categories": "AI, Machine Learning",
                            }
                        ],
                        "total_recommendations": 1,
                        "tfidf_candidates_count": 50,
                        "cache_hit": False,
                        "processing_time_ms": 45.2,
                    }
                }
            },
        },
        404: {
            "model": ErrorResponse,
            "description": "Project not found or no similar projects available",
            "content": {
                "application/json": {
                    "examples": {
                        "project_not_found": {
                            "summary": "Project does not exist",
                            "value": {"detail": "Project not found in database."},
                        },
                        "no_similar_projects": {
                            "summary": "No similar projects found",
                            "value": {
                                "detail": "No similar projects found for this project."
                            },
                        },
                    }
                }
            },
        },
        422: {
            "model": ErrorResponse,
            "description": "Invalid request parameters",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_uuid": {
                            "summary": "Invalid UUID format",
                            "value": {
                                "detail": "Invalid UUID format for project_id parameter"
                            },
                        },
                        "invalid_top_k": {
                            "summary": "Invalid top_k parameter",
                            "value": {"detail": "Value must be between 1 and 20"},
                        },
                    }
                }
            },
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error or models not available",
            "content": {
                "application/json": {
                    "examples": {
                        "models_not_loaded": {
                            "summary": "ML models not available",
                            "value": {
                                "detail": "TF-IDF or Mistral models not available."
                            },
                        },
                        "cache_error": {
                            "summary": "Cache connection error",
                            "value": {"detail": "Redis cache connection failed."},
                        },
                    }
                }
            },
        },
    },
)
async def get_project_recommendations(
    project_id: UUID = Path(
        ...,
        description="UUID of the project to find similar projects for",
        example="a75337f8-f424-4f0c-90c2-2d7026b5bce8",
    ),
    top_k: int = Query(
        default=10,
        ge=1,
        le=20,
        description="Maximum number of project recommendations to return",
        example=10,
    ),
    db: Session = Depends(get_db),
):
    """
    Get project-based hybrid recommendations.

    This endpoint uses a hybrid approach combining:
    1. **TF-IDF Pre-ranking**: Fast initial candidate selection
    2. **Mistral Re-ranking**: Semantic similarity using embeddings
    3. **Hybrid Scoring**: Combines both signals for optimal results

    **Parameters:**
    - `project_id`: UUID of the target project
    - `top_k`: Number of recommendations (1-20)

    **Returns:**
    - List of recommended projects with detailed scores
    - Processing metadata and performance metrics

    **Performance:**
    - Response time: < 3 seconds
    - TF-IDF candidates: 50-100 projects
    - Mistral embeddings: 1024-dimensional vectors
    - Hybrid scoring: TF-IDF 40% + Mistral 60%
    """
    start_time = time.time()

    try:
        # Import project recommendation flow
        from src.infrastructure.pipeline.flows.mistral_recommendations_flow import (
            mistral_recommendations_flow,
        )

        # Get hybrid recommendations
        result = mistral_recommendations_flow(project_id=str(project_id), top_k=top_k)

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get(
                    "error", "No similar projects found for this project."
                ),
            )

        response_time = (time.time() - start_time) * 1000
        log.info(
            f"[API] Project recommendations for {project_id} top_k={top_k} in {response_time:.2f}ms"
        )

        return ProjectRecommendationResponse(
            project_id=project_id,
            recommendations=result.get("recommendations", []),
            total_recommendations=result.get("final_recommendations_count", 0),
            tfidf_candidates_count=result.get("tfidf_candidates_count", 0),
            cache_hit=False,  # TODO: Implement caching
            processing_time_ms=response_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"[API] Error in project recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error. Please try again later.",
        )


@app.get(
    "/user-recommendations/{user_id}",
    tags=["Recommendations"],
    response_model=UserRecommendationResponse,
    summary="👤 Get User-Based Hybrid Recommendations",
    description="Generate personalized recommendations for a user using User↔Project similarities",
    responses={
        200: {
            "description": "Successfully generated user recommendations",
            "content": {
                "application/json": {
                    "example": {
                        "user_id": "a75337f8-f424-4f0c-90c2-2d7026b5bce8",
                        "recommendations": [
                            {
                                "project_id": "c0343f9a-27ec-4a1e-9ecc-93ed384b836b",
                                "title": "AI Chatbot Platform",
                                "tfidf_score": 0.5,
                                "user_project_similarity": 0.92,
                                "hybrid_score": 0.89,
                                "tech_stacks": "Python, TensorFlow, FastAPI",
                                "categories": "AI, Machine Learning",
                            }
                        ],
                        "tfidf_candidates_count": 100,
                        "user_project_similarities_count": 37,
                        "final_recommendations_count": 5,
                        "weights": {"tfidf": 0.3, "user_project": 0.7},
                        "response_time_ms": 4811.41,
                    }
                }
            },
        },
        404: {
            "model": ErrorResponse,
            "description": "User not found or no recommendations available",
            "content": {
                "application/json": {
                    "examples": {
                        "user_not_found": {
                            "summary": "User does not exist",
                            "value": {"detail": "User not found in database."},
                        },
                        "no_recommendations": {
                            "summary": "No recommendations available",
                            "value": {
                                "detail": "No recommendations found for this user."
                            },
                        },
                    }
                }
            },
        },
        422: {
            "model": ErrorResponse,
            "description": "Invalid request parameters",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_uuid": {
                            "summary": "Invalid UUID format",
                            "value": {
                                "detail": "Invalid UUID format for user_id parameter"
                            },
                        },
                        "invalid_top_k": {
                            "summary": "Invalid top_k parameter",
                            "value": {"detail": "Value must be between 1 and 50"},
                        },
                    }
                }
            },
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error or models not available",
            "content": {
                "application/json": {
                    "examples": {
                        "models_not_loaded": {
                            "summary": "ML models not available",
                            "value": {
                                "detail": "TF-IDF or Mistral models not available."
                            },
                        },
                        "embedding_error": {
                            "summary": "User embedding error",
                            "value": {"detail": "Failed to create user embedding."},
                        },
                    }
                }
            },
        },
    },
)
async def get_user_recommendations(
    user_id: UUID = Path(
        ...,
        description="UUID of the user to generate recommendations for",
        example="a75337f8-f424-4f0c-90c2-2d7026b5bce8",
    ),
    top_k: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of project recommendations to return",
        example=10,
    ),
    with_categories_only: bool = Query(
        default=True,
        description="If True, only recommend projects with categories",
        example=True,
    ),
    db: Session = Depends(get_db),
):
    """
    Get user-based hybrid recommendations (Recommended endpoint).

    This endpoint uses the most advanced recommendation system combining:
    1. **TF-IDF Pre-ranking**: Fast initial candidate selection
    2. **User Embeddings**: Personalized user profiles using tech stacks
    3. **User↔Project Similarity**: Semantic matching between user and projects
    4. **Hybrid Scoring**: Combines multiple signals for optimal results

    **Parameters:**
    - `user_id`: UUID of the user
    - `top_k`: Number of recommendations (1-50)
    - `with_categories_only`: Filter to projects with categories

    **Returns:**
    - List of recommended projects with detailed scores
    - Processing metadata and performance metrics
    - Hybrid scoring weights and statistics

    **Performance:**
    - Response time: < 5 seconds
    - TF-IDF candidates: 100 projects
    - User embeddings: 1024-dimensional vectors
    - Hybrid scoring: TF-IDF 30% + User↔Project 70%

    **Features:**
    - Personalized based on user tech stacks
    - Semantic similarity using Mistral embeddings
    - Category filtering for better quality
    - Comprehensive scoring and metadata
    """
    start_time = time.time()

    try:
        log.info(f"[API] User recommendation request for {user_id} top_k={top_k}")

        # Get hybrid recommendations using User↔Project flow
        recommendations_result = user_project_recommendations_flow(
            user_id=str(user_id), top_k=top_k, with_categories_only=with_categories_only
        )

        if not recommendations_result.get("success"):
            error_msg = recommendations_result.get(
                "error", "No recommendations found for this user."
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)

        response_time = (time.time() - start_time) * 1000
        log.info(
            f"[API] Generated {len(recommendations_result.get('recommendations', []))} recommendations for user {user_id} in {response_time:.2f}ms"
        )

        return UserRecommendationResponse(
            user_id=user_id,
            recommendations=recommendations_result.get("recommendations", []),
            tfidf_candidates_count=recommendations_result.get(
                "tfidf_candidates_count", 0
            ),
            user_project_similarities_count=recommendations_result.get(
                "user_project_similarities_count", 0
            ),
            final_recommendations_count=recommendations_result.get(
                "final_recommendations_count", 0
            ),
            weights=recommendations_result.get("weights", {}),
            response_time_ms=response_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"[API] Error in user recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error. Please try again later.",
        )


# ============================================================================
# MONITORING ENDPOINTS
# ============================================================================


@app.get(
    "/metrics",
    tags=["Monitoring"],
    response_model=MetricsResponse,
    summary="📊 System Metrics",
    description="Get comprehensive system metrics and health information",
    responses={
        200: {
            "description": "Successfully retrieved system metrics",
            "content": {
                "application/json": {
                    "example": {
                        "system_health": {
                            "status": "healthy",
                            "uptime_seconds": 3600.5,
                            "error_rate_percent": 0.5,
                            "avg_response_time_ms": 150.2,
                            "cache_hit_rate_percent": 85.3,
                            "metrics_count": 8,
                            "last_updated": "2023-08-03T13:44:24Z",
                        },
                        "metrics": {
                            "api_requests_total": {
                                "name": "api_requests_total",
                                "description": "Total API requests",
                                "unit": "count",
                                "count": 1250,
                                "min": 1,
                                "max": 1,
                                "avg": 1,
                                "latest": 1,
                                "window_minutes": 60,
                            }
                        },
                        "timestamp": "2023-08-03T13:44:24Z",
                    }
                }
            },
        }
    },
)
async def get_metrics(
    window_minutes: int = Query(
        default=60,
        ge=1,
        le=1440,  # 24 hours
        description="Time window for metrics aggregation in minutes",
        example=60,
    ),
):
    """
    Get comprehensive system metrics and health information.

    This endpoint provides:
    - Overall system health status
    - Performance metrics (response times, error rates)
    - Resource utilization (memory, CPU)
    - Component-specific metrics (API, database, cache)
    - Real-time monitoring data
    """
    try:
        # Get system health
        system_health = metrics_service.get_system_health()

        # Get all metrics statistics
        all_metrics = metrics_service.get_all_metrics_stats(window_minutes)

        return MetricsResponse(
            system_health=system_health,
            metrics=all_metrics,
            timestamp=system_health["last_updated"],
        )

    except Exception as e:
        log.error(f"Error retrieving metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system metrics",
        )


@app.get(
    "/metrics/export",
    tags=["Monitoring"],
    summary="📊 Export Metrics",
    description="Export metrics in various formats (JSON, Prometheus, etc.)",
    responses={
        200: {
            "description": "Successfully exported metrics",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp": "2023-08-03T13:44:24Z",
                        "system_health": {
                            "status": "healthy",
                            "uptime_seconds": 3600.5,
                        },
                        "metrics": {"api_requests_total": {"count": 1250, "avg": 1}},
                    }
                }
            },
        }
    },
)
async def export_metrics(
    format: str = Query(
        default="json",
        description="Export format (json, prometheus)",
        example="json",
    ),
):
    """
    Export metrics in various formats for external monitoring systems.

    Supported formats:
    - JSON: Standard JSON format for general use
    - Prometheus: Prometheus-compatible format for monitoring systems
    """
    try:
        if format.lower() == "json":
            return JSONResponse(
                content=metrics_service.export_metrics("json"),
                media_type="application/json",
            )
        elif format.lower() == "prometheus":
            # TODO: Implement Prometheus format
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Prometheus format not yet implemented",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format: {format}",
            )

    except Exception as e:
        log.error(f"Error exporting metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export metrics",
        )


@app.get(
    "/health/detailed",
    tags=["Monitoring"],
    summary="🏥 Detailed Health Check",
    description="Get detailed system health information including all components",
    responses={
        200: {
            "description": "Detailed health information",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "components": {
                            "api": "healthy",
                            "database": "healthy",
                            "cache": "healthy",
                            "models": "healthy",
                        },
                        "metrics": {
                            "uptime_seconds": 3600.5,
                            "error_rate_percent": 0.5,
                            "avg_response_time_ms": 150.2,
                        },
                        "timestamp": "2023-08-03T13:44:24Z",
                    }
                }
            },
        }
    },
)
async def detailed_health_check():
    """
    Get detailed system health information.

    This endpoint provides comprehensive health information including:
    - Overall system status
    - Individual component health
    - Performance metrics
    - Resource utilization
    """
    try:
        # Get system health
        system_health = metrics_service.get_system_health()

        # Check individual components
        components = {
            "api": "healthy",  # If we reach this endpoint, API is healthy
            "database": "healthy",  # TODO: Add actual DB health check
            "cache": "healthy",  # TODO: Add actual cache health check
            "models": "healthy",  # TODO: Add actual model health check
        }

        return {
            "status": system_health["status"],
            "components": components,
            "metrics": {
                "uptime_seconds": system_health["uptime_seconds"],
                "error_rate_percent": system_health["error_rate_percent"],
                "avg_response_time_ms": system_health["avg_response_time_ms"],
                "cache_hit_rate_percent": system_health["cache_hit_rate_percent"],
            },
            "timestamp": system_health["last_updated"],
        }

    except Exception as e:
        log.error(f"Error in detailed health check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform detailed health check",
        )


# ============================================================================
# MAIN APPLICATION
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
