from dagster import (
    AssetSelection,
    Backoff,
    Jitter,
    RetryPolicy,
    define_asset_job,
)

run_all_job = define_asset_job(
    name="run_all_job",
    selection=AssetSelection.groups(
        "ingestion",
        "classification",
        "sync",
        "ml_project_preparation",
        "ml_user_preparation",
        "ml",
        "matching",
    ),
    op_retry_policy=RetryPolicy(
        max_retries=2,
        delay=30,
        backoff=Backoff.EXPONENTIAL,
        jitter=Jitter.FULL,
    ),
    tags={"dagster/max_concurrent_runs": "1"},
    description="Runs the full pipeline: ingestion, classification, sync, ML, and matching.",
)
