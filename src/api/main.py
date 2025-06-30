import pickle
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI

from src.infrastructure.config import settings
from src.infrastructure.logger import log


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
        log.info(
            "Successfully loaded TF-IDF vectorizer from %s", settings.VECTORIZER_PATH
        )

    except FileNotFoundError:
        log.warning(
            "Model artifacts not found. API is starting without models. "
            "Run the training pipeline to generate them."
        )
        app.state.similarity_matrix = None
        app.state.vectorizer = None

    yield
    # Cleanup logic can go here if needed on shutdown
    log.info("API shutting down.")


app = FastAPI(
    title="Data Engine API",
    description="API for the recommendation engine.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to ensure the API is running.
    """
    return {"status": "ok"}
