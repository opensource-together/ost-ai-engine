from dagster import AssetSelection, define_asset_job

project_embedding_job = define_asset_job(
    name="project_embedding_job",
    selection=AssetSelection.groups("ml_preparation", "ml", "matching"),
    tags={"dagster/max_concurrent_runs": "1"},
    description=(
        "Runs dbt models for ML context, computes project embeddings, "
        "and materializes matching recommendations."
    ),
)
