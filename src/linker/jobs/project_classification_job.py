from dagster import (
    AssetSelection,
    Backoff,
    Jitter,
    RetryPolicy,
    define_asset_job,
)

project_classification_job = define_asset_job(
    name="project_classification_job",
    selection=AssetSelection.groups("classification", "sync"),
    op_retry_policy=RetryPolicy(
        max_retries=2,
        delay=30,
        backoff=Backoff.EXPONENTIAL,
        jitter=Jitter.FULL,
    ),
    tags={"dagster/max_concurrent_runs": "1"},
    description=(
        "Orchestrates the LLM classification of projects into Categories and Domains, "
        "then syncs results to the public Project table."
    ),
)
