from dagster import schedule

from src.pipeline.jobs.cleanup_dagster_job import cleanup_dagster_history_job


@schedule(cron_schedule="0 23 */2 * *", job=cleanup_dagster_history_job)
def cleanup_dagster_history_schedule():
    """Run every 2 days at 23:00 to purge old Dagster history/logs (keep 2 days)."""
    return {}


__all__ = ["cleanup_dagster_history_schedule"]
