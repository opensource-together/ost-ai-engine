from src.application.use_cases.run_training_pipeline import run_training_pipeline

from .celery_app import celery_app


@celery_app.task
def run_training_pipeline_task():
    """
    Celery task that runs the full model training pipeline.
    """
    print("Executing training pipeline via Celery...")
    try:
        run_training_pipeline()
        print("Celery task: Training pipeline finished successfully.")
    except Exception as e:
        # Proper logging should be added here in a real application
        print(f"Celery task: An error occurred during the training pipeline: {e}")
        # Optionally re-raise to have Celery mark the task as FAILED
        raise
