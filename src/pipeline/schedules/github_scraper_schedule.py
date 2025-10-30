from dagster import ScheduleDefinition, DefaultScheduleStatus


def make_github_scraper_schedule(job):
    """Return the ScheduleDefinition for the GitHub scraper job.

    Cron is defined here directly (no longer read from centralized config).
    Keep the previous default of every-6-hours: "0 */6 * * *".
    """
    return ScheduleDefinition(
        name="github_scraper_schedule",
        job=job,
        cron_schedule="0 */6 * * *",
        default_status=DefaultScheduleStatus.RUNNING,
    )
