from dagster import (
    AssetSelection,
    Backoff,
    Jitter,
    RetryPolicy,
    define_asset_job,
)

project_scraper_job = define_asset_job(
    name="project_scraper_job",
    selection=AssetSelection.groups("ingestion"),
    op_retry_policy=RetryPolicy(
        max_retries=2,
        delay=30,
        backoff=Backoff.EXPONENTIAL,
        jitter=Jitter.FULL,
    ),
    tags={"dagster/max_concurrent_runs": "1"},
    description="Ingests raw GitHub data and detects languages.",
)

__all__ = ["project_scraper_job"]
