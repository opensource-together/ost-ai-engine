import os

from celery import Celery
from celery.schedules import crontab

from src.infrastructure.config import settings

# Get Redis URL from environment variables
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# --- Celery Application Instance ---
celery_app = Celery(
    "tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["src.infrastructure.celery.tasks"],
)

# --- Celery Beat Schedule ---
# This is where we define our periodic tasks.
celery_app.conf.beat_schedule = {
    "run-training-pipeline-daily": {
        "task": "src.infrastructure.celery.tasks.run_training_pipeline_task",
        # Runs every day at midnight UTC
        "schedule": crontab(hour=0, minute=0),
    },
}

# --- Optional Celery Configuration ---
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)
 