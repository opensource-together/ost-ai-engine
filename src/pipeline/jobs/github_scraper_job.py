from dagster import (
    define_asset_job,
    in_process_executor,
    AssetSelection,
    RetryPolicy,
    Backoff,
    Jitter,
)


github_scraper_job = define_asset_job(
    name="github_scraper_job",
    selection=AssetSelection.groups("github_projects_scraper"),
    executor_def=in_process_executor,
    # default retry policy for ops computing assets in this job.
    op_retry_policy=RetryPolicy(
        max_retries=2,
        delay=30,
        backoff=Backoff.EXPONENTIAL,
        jitter=Jitter.FULL,
    ),
    description=(
        "Scrape trending repositories (GitHub and GitLab), filter and rank them, "
        "normalize to the Prisma Project schema, and upsert the results into the database. "
        "The job runs the Go scrapers, applies language detection and data-quality checks, "
        "maps fields to the Project model, and emits insert/update metrics. "
        "Configurable (scraper queries, top-N, fastText model path) and safe for repeated runs."
    ),
)

__all__ = ["github_scraper_job"]
