from dagster import ScheduleDefinition, DefaultScheduleStatus
from ..jobs.run_all_job import run_all_job

# Schedule: 5x per day
run_all_schedule = ScheduleDefinition(
    job=run_all_job,
    cron_schedule="0 5,10,15,20 * * *",
    execution_timezone="Europe/Paris",
    default_status=DefaultScheduleStatus.RUNNING,
)
