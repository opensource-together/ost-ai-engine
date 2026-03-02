from dagster import ScheduleDefinition, DefaultScheduleStatus

from ..jobs.cleanup_dagster_job import cleanup_dagster_history_job


# Enable by default at Dagster start, like the GitHub scraper schedule
cleanup_dagster_history_schedule = ScheduleDefinition(
    name="cleanup_dagster_history_schedule",
    job=cleanup_dagster_history_job,
    cron_schedule="0 23 */2 * *",
    default_status=DefaultScheduleStatus.RUNNING,
    run_config={},
)


__all__ = ["cleanup_dagster_history_schedule"]
