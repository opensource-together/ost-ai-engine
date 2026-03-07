from dagster import DefaultScheduleStatus, ScheduleDefinition

from ..jobs.project_enrichment_job import project_enrichment_job

# Schedule: 1x per day at 3 AM
project_enrichment_schedule = ScheduleDefinition(
    job=project_enrichment_job,
    cron_schedule="0 3 * * *",
    execution_timezone="Europe/Paris",
    default_status=DefaultScheduleStatus.RUNNING,
)
