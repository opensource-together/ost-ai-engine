from dagster import DefaultScheduleStatus, ScheduleDefinition

from ..jobs.user_recommendation_job import user_recommendation_job

# Schedule: every 10 minutes
user_recommendation_schedule = ScheduleDefinition(
    job=user_recommendation_job,
    cron_schedule="*/10 * * * *",
    execution_timezone="Europe/Paris",
    default_status=DefaultScheduleStatus.RUNNING,
)
