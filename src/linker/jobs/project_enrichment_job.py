from dagster import (
    AssetSelection,
    Backoff,
    Jitter,
    RetryPolicy,
    define_asset_job,
)

project_enrichment_job = define_asset_job(
    name="project_enrichment_job",
    selection=AssetSelection.groups(
        "ingestion",
        "classification",
        "sync",
        "project_ml",
    ),
    op_retry_policy=RetryPolicy(
        max_retries=2,
        delay=30,
        backoff=Backoff.EXPONENTIAL,
        jitter=Jitter.FULL,
    ),
    tags={"dagster/max_concurrent_runs": "1"},
    description=(
        "Full project flow: scrapes GitHub, classifies via LLM, "
        "syncs to public, embeds, and materializes recommendations."
    ),
)
