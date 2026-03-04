from dagster import (
    DagsterRunStatus,
    RunRequest,
    RunStatusSensorContext,
    run_status_sensor,
)

from ..jobs.project_classification_job import project_classification_job
from ..jobs.project_scraper_job import project_scraper_job


@run_status_sensor(
    run_status=DagsterRunStatus.SUCCESS,
    monitored_jobs=[project_scraper_job],
    request_job=project_classification_job,
)
def classification_sensor(context: RunStatusSensorContext):
    """Trigger classification job on scraper success."""
    return RunRequest(
        run_key=f"classification_run_{context.dagster_run.run_id}",
    )
