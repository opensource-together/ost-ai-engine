from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Manages application-wide settings by loading them from environment variables.
    """

    # --- Database ---
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/db"

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
    VECTORIZER_PATH: str = f"{MODEL_DIR}/vectorizer.pkl"

    class Config:
        # This tells Pydantic to load settings from a .env file
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create a single, reusable instance of the settings
settings = Settings()
