from dagster import DefaultScheduleStatus, ScheduleDefinition

from ..jobs.cleanup_dagster_job import cleanup_dagster_history_job

# 23:00 Europe/Paris on odd calendar days (cron day-of-month */2 = 1,3,5,...)
cleanup_dagster_history_schedule = ScheduleDefinition(
    name="cleanup_dagster_history_schedule",
    job=cleanup_dagster_history_job,
    cron_schedule="0 23 */2 * *",
    execution_timezone="Europe/Paris",
    default_status=DefaultScheduleStatus.RUNNING,
    run_config={},
)


__all__ = ["cleanup_dagster_history_schedule"]
