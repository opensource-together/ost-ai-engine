from dagster import run_status_sensor, RunStatusSensorContext, DagsterRunStatus, RunRequest
from ..jobs.github_scraper_job import github_scraper_job
from ..jobs.project_classification_job import project_classification_job

@run_status_sensor(
    run_status=DagsterRunStatus.SUCCESS,
    monitored_jobs=[github_scraper_job],
    request_job=project_classification_job,
)
def classification_sensor(context: RunStatusSensorContext):
    """
    Triggers the project classification job when the github scraper job completes successfully.
    """
    return RunRequest(
        run_key=f"classification_run_{context.dagster_run.run_id}",
    )
