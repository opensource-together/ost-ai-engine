from dagster import (
    RunRequest,
    SensorEvaluationContext,
    sensor,
    DefaultSensorStatus,
    DagsterRunStatus,
    RunsFilter,
)


@sensor(
    name="embedding_job_sensor",
    job_name="project_embedding_job",
    default_status=DefaultSensorStatus.RUNNING,
    description=(
        "Triggers the project_embedding_job after github_scraper_job completes successfully. "
        "This sensor monitors the completion of the scraper job and automatically launches "
        "the embedding generation for newly scraped projects."
    ),
)
def embedding_job_sensor(context: SensorEvaluationContext):
    """
    Monitors the github_scraper_job and launches project_embedding_job when:
    - github_scraper_job completes with SUCCESS status
    - No embedding job is currently running for the same data
    """
    # Get the last run of github_scraper_job
    runs = context.instance.get_runs(
        filters=RunsFilter(
            job_name="github_scraper_job",
            statuses=[DagsterRunStatus.SUCCESS],
        ),
        limit=1,
    )
    
    if not runs:
        context.log.debug("embedding_job_sensor: No successful github_scraper_job runs found")
        return
    
    last_scraper_run = runs[0]
    
    # check if we've already triggered an embedding job for this scraper run
    cursor_key = f"last_processed_scraper_run_id"
    last_processed_run_id = context.cursor or None
    
    if last_processed_run_id == last_scraper_run.run_id:
        context.log.debug(
            f"embedding_job_sensor: Already processed scraper run {last_scraper_run.run_id}"
        )
        return
    
    # trigger
    context.log.info(
        f"embedding_job_sensor: Triggering project_embedding_job for scraper run {last_scraper_run.run_id}"
    )
    
    yield RunRequest(
        run_key=f"embedding_for_{last_scraper_run.run_id}",
        run_config={},
        tags={
            "triggered_by": "embedding_job_sensor",
            "source_scraper_run_id": last_scraper_run.run_id,
        },
    )
    
    context.update_cursor(last_scraper_run.run_id)


__all__ = ["embedding_job_sensor"]
