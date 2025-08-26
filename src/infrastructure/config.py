from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Manages application-wide settings by loading them from environment variables.
    Enhanced with security validation and performance optimizations.
    """

    # --- Database ---
    DATABASE_URL: str = Field(
        default="",
        description="PostgreSQL database connection URL (use environment variable for production)",
    )
    DATABASE_POOL_SIZE: int = Field(
        default=10, description="Database connection pool size"
    )
    DATABASE_MAX_OVERFLOW: int = Field(default=20, description="Database max overflow")
    DATABASE_POOL_TIMEOUT: int = Field(
        default=30, description="Database pool timeout in seconds"
    )
    DATABASE_POOL_RECYCLE: int = Field(
        default=3600, description="Database pool recycle time"
    )

    # --- Celery ---
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/0", description="Celery broker URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/0", description="Celery result backend URL"
    )
    CELERY_TASK_TIMEOUT: int = Field(
        default=300, description="Celery task timeout in seconds"
    )
    CELERY_MAX_RETRIES: int = Field(default=3, description="Celery max retries")

    # --- Redis ---
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )
    REDIS_CACHE_URL: str = Field(
        default="redis://localhost:6380", description="Separate Redis for caching"
    )
    REDIS_CACHE_TTL: int = Field(default=3600, description="Cache TTL in seconds")
    REDIS_CONNECT_TIMEOUT: int = Field(
        default=5, description="Redis connection timeout"
    )
    REDIS_READ_TIMEOUT: int = Field(default=5, description="Redis read timeout")

    # --- GitHub API ---
    GITHUB_ACCESS_TOKEN: str = Field(
        default="your_github_token_here", description="GitHub API access token"
    )
    GITHUB_REPO_LIST: str | None = Field(
        default=None, description="Comma-separated list of GitHub repositories"
    )
    GITHUB_RATE_LIMIT: int = Field(
        default=5000, description="GitHub API rate limit per hour"
    )
    GITHUB_REQUEST_TIMEOUT: int = Field(
        default=30, description="GitHub API request timeout"
    )
    GITHUB_SCRAPING_QUERY: str = Field(
        default="language:python stars:>100 language:javascript stars:>100 language:go stars:>100",
        description="GitHub search query for scraping repositories"
    )
    GITHUB_MAX_REPOSITORIES: int = Field(
        default=500, description="Maximum number of repositories to scrape from GitHub"
    )
    GITHUB_MIN_STARS: int = Field(
        default=100, description="Minimum number of stars for repositories to scrape"
    )
    GITHUB_LANGUAGES: str = Field(
        default="python,javascript,go,java,rust,typescript",
        description="Comma-separated list of programming languages to scrape"
    )

    # --- Mistral API ---
    MISTRAL_API_KEY: str = Field(
        default="your_mistral_api_key_here", description="Mistral API key"
    )
    MISTRAL_REQUEST_TIMEOUT: int = Field(
        default=60, description="Mistral API request timeout"
    )
    MISTRAL_MAX_RETRIES: int = Field(default=3, description="Mistral API max retries")
    MISTRAL_BATCH_SIZE: int = Field(default=10, description="Mistral API batch size")

    # --- Logging ---
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format",
    )

    # --- Application Configuration ---
    PROJECT_ROOT: str = Field(
        default="", description="Project root directory path"
    )

    # --- dbt Configuration ---
    DBT_PROJECT_DIR: str = Field(
        default="src/dbt", description="dbt project directory path"
    )

    # --- Go Scraper Configuration ---
    GO_SCRAPER_PATH: str = Field(
        default="./src/infrastructure/services/go/github-scraper/main",
        description="Path to the Go scraper executable"
    )

    # --- Model Paths ---
    MODEL_DIR: str = Field(default="models", description="Model directory")
    MODEL_CACHE_PATH: str = Field(
        default="models/sentence-transformers",
        description="Path for sentence transformers model cache"
    )
    SIMILARITY_MATRIX_PATH: str = Field(
        default="models/similarity_matrix.npy",
        description="Similarity matrix file path",
    )
    VECTORIZER_PATH: str = Field(
        default="models/tfidf_vectorizer.pkl", description="TF-IDF vectorizer file path"
    )

    # --- MLflow Configuration ---
    MLFLOW_TRACKING_URI: str = Field(
        default="sqlite:///logs/mlflow.db",
        description="MLflow tracking URI for model persistence"
    )
    MLFLOW_ARTIFACT_ROOT: str = Field(
        default="models/mlruns",
        description="MLflow artifact root directory"
    )
    MLFLOW_MODEL_REGISTRY_NAME: str = Field(
        default="ost-models",
        description="MLflow model registry name"
    )
    MLFLOW_UI_PORT: int = Field(
        default=5050,
        description="MLflow UI port"
    )
    MLFLOW_UI_HOST: str = Field(
        default="0.0.0.0",
        description="MLflow UI host"
    )

    # --- Security ---
    API_RATE_LIMIT: int = Field(default=100, description="API rate limit per minute")
    API_TIMEOUT: int = Field(default=30, description="API request timeout")
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="CORS allowed origins",
    )

    # --- Performance ---
    CACHE_ENABLED: bool = Field(default=True, description="Enable caching")
    CACHE_TTL: int = Field(default=3600, description="Cache TTL in seconds")
    BATCH_SIZE: int = Field(
        default=100, description="Default batch size for operations"
    )

    # --- ML Model Configuration ---
    MODEL_NAME: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Hugging Face model name for sentence embeddings"
    )
    MODEL_DISPLAY_NAME: str = Field(
        default="all-MiniLM-L6-v2",
        description="Display name for the embedding model"
    )
    MODEL_DIMENSIONS: int = Field(
        default=384,
        description="Output dimensions of the embedding model"
    )
    
    # --- Recommendation Model Parameters ---
    RECOMMENDATION_SEMANTIC_WEIGHT: float = Field(
        default=0.4, description="Weight for semantic similarity in recommendations"
    )
    RECOMMENDATION_CATEGORY_WEIGHT: float = Field(
        default=0.3, description="Weight for category overlap in recommendations"
    )
    RECOMMENDATION_TECH_WEIGHT: float = Field(
        default=0.2, description="Weight for tech stack overlap in recommendations"
    )
    RECOMMENDATION_POPULARITY_WEIGHT: float = Field(
        default=0.1, description="Weight for popularity in recommendations"
    )
    RECOMMENDATION_TOP_N: int = Field(
        default=10, description="Number of top recommendations to return"
    )
    RECOMMENDATION_MIN_SIMILARITY: float = Field(
        default=0.1, description="Minimum similarity threshold for recommendations"
    )
    RECOMMENDATION_MAX_PROJECTS: int = Field(
        default=50, description="Maximum number of projects to consider"
    )
    RECOMMENDATION_POPULARITY_THRESHOLD: int = Field(
        default=100000, description="Popularity threshold for normalization"
    )

    # --- Validation Methods (Pydantic V2) ---
    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if v and not v.startswith("postgresql://"):
            raise ValueError("DATABASE_URL must start with postgresql://")
        return v

    @field_validator(
        "CELERY_BROKER_URL", "CELERY_RESULT_BACKEND", "REDIS_URL", "REDIS_CACHE_URL"
    )
    @classmethod
    def validate_redis_url(cls, v):
        """Validate Redis URL format."""
        if not v.startswith("redis://"):
            raise ValueError("Redis URLs must start with redis://")
        return v

    @field_validator("GITHUB_ACCESS_TOKEN")
    @classmethod
    def validate_github_token(cls, v):
        """Validate GitHub token security."""
        if v == "your_github_token_here":
            # In production, this should be a real token
            return v
        if len(v) < 10:
            raise ValueError("GitHub token too short")
        return v

    @field_validator("MISTRAL_API_KEY")
    @classmethod
    def validate_mistral_key(cls, v):
        """Validate Mistral API key security."""
        if v == "your_mistral_api_key_here":
            # In production, this should be a real key
            return v
        if len(v) < 10:
            raise ValueError("Mistral API key too short")
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()

    # --- Utility Methods ---
    def get_absolute_model_path(self, relative_path: str) -> str:
        """Get absolute path for model files."""
        import os

        return os.path.join(os.getcwd(), relative_path)

    def get_cors_origins(self) -> list[str]:
        """Get CORS origins as list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",  # Ignore extra env vars not declared in this model
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
