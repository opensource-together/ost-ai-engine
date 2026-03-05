from dagster import DefaultScheduleStatus, ScheduleDefinition

from ..jobs.run_all_job import run_all_job

# Schedule: 1x per day at 3 AM
run_all_schedule = ScheduleDefinition(
    job=run_all_job,
    cron_schedule="0 3 * * *",
    execution_timezone="Europe/Paris",
    default_status=DefaultScheduleStatus.RUNNING,
)
