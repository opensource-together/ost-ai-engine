from dagster import (
    define_asset_job,
    multiprocess_executor,
    AssetSelection,
    RetryPolicy,
    Backoff,
    Jitter,
)


project_scraper_job = define_asset_job(
    name="project_scraper_job",
    selection=AssetSelection.groups("ingestion", "classification"),

    op_retry_policy=RetryPolicy(
        max_retries=2,
        delay=30,
        backoff=Backoff.EXPONENTIAL,
        jitter=Jitter.FULL,
    ),
    description="Scrape projects, classify them, and sync to public schema.",
)

__all__ = ["project_scraper_job"]
