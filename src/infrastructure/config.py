from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Manages application-wide settings by loading them from environment variables.
    """

    # --- Database ---
    DATABASE_URL: str = "postgresql://user:password@localhost:5434/ost_db"

    # --- Celery ---
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # --- GitHub API ---
    GITHUB_ACCESS_TOKEN: str = "your_github_token_here"
    GITHUB_REPO_LIST: str | None = None

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    # --- Model Paths ---
    MODEL_DIR: str = "models"
    SIMILARITY_MATRIX_PATH: str = f"{MODEL_DIR}/similarity_matrix.npy"
    VECTORIZER_PATH: str = f"{MODEL_DIR}/tfidf_vectorizer.pkl"

    def get_absolute_model_path(self, relative_path: str) -> str:
        """Get absolute path for model files."""
        import os
        # Get the project root (data-engine directory)
        current_file = os.path.abspath(__file__)  # This file is in src/infrastructure/
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        return os.path.join(project_root, relative_path)

    class Config:
        # This tells Pydantic to load settings from a .env file
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """
    Get application settings with lazy loading.

    This function uses functools.lru_cache to ensure that the Settings
    object is created only once, providing a singleton pattern while
    allowing for lazy loading during testing or when configuration
    needs to be loaded at a specific time.

    Returns:
        Settings: The application settings instance
    """
    return Settings()


# Create a single, reusable instance of the settings for backward compatibility
settings = Settings()
