from dagster import DefaultScheduleStatus, ScheduleDefinition

from ..jobs.user_recommendation_job import user_recommendation_job

# Schedule: every 2 hours
user_recommendation_schedule = ScheduleDefinition(
    job=user_recommendation_job,
    cron_schedule="0 */2 * * *",
    execution_timezone="Europe/Paris",
    default_status=DefaultScheduleStatus.RUNNING,
)
