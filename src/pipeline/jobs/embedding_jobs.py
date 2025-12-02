from dagster import (
    define_asset_job,
    in_process_executor,
    AssetSelection,
    RetryPolicy,
    Backoff,
    Jitter,
)


project_embedding_job = define_asset_job(
    name="project_embedding_job",
    selection=AssetSelection.groups("projects_embedding"),
    executor_def=in_process_executor,  # Consistent with scraper job
    op_retry_policy=RetryPolicy(
        max_retries=2,
        delay=30,
        backoff=Backoff.EXPONENTIAL,
        jitter=Jitter.FULL,
    ),
    description=(
        "Generate embeddings for projects scraped by github_scraper_job. "
        "This job is automatically triggered by the embedding_job_sensor after "
        "successful completion of the scraper job. It processes project data "
        "and generates vector embeddings for similarity search and recommendations."
    ),
)

__all__ = ["project_embedding_job"]
