from dagster import (
    define_asset_job,
    in_process_executor,
    multiprocess_executor,
    AssetSelection,
    RetryPolicy,
    Backoff,
    Jitter,
)


github_scraper_job = define_asset_job(
    name="github_scraper_job",
    selection=AssetSelection.groups("github_projects_scraper", "fetch_projects_metadatas", "map_repos_metadatas", "default"),
    executor_def=in_process_executor,  # Avoid SIGBUS with multiprocessing
    op_retry_policy=RetryPolicy( # default retry policy for ops computing assets in this job.
        max_retries=2,
        delay=30,
        backoff=Backoff.EXPONENTIAL,
        jitter=Jitter.FULL,
    ),
    description="Scrape trending repositories, filter, normalize, and upsert to database.",
)

__all__ = ["github_scraper_job"]
