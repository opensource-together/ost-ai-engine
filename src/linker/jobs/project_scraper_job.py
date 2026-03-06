from dagster import (
    AssetSelection,
    Backoff,
    Jitter,
    RetryPolicy,
    define_asset_job,
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
    description=(
        "Ingests raw GitHub data, detects languages, "
        "and executes initial classification pipeline."
    ),
)

__all__ = ["project_scraper_job"]
