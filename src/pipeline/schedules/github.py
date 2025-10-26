from dagster import ScheduleDefinition, DefaultScheduleStatus
from src.services.python.load_cfg import PipelineConfig


def make_github_scraper_schedule(job):
    """Return the ScheduleDefinition for the github scraper job.

    Accepts the job object to avoid circular imports between definitions and schedules.
    The schedule's cron expression is read from PipelineConfig (same source as before).
    """
    return ScheduleDefinition(
        name="github_scraper_schedule",
        job=job,
        cron_schedule=PipelineConfig().github_scraper_cron,
        default_status=DefaultScheduleStatus.RUNNING,
    )
