from dagster import AssetSelection, define_asset_job

# Job that runs the full embedding pipeline:
# 1. dbt run (to refresh stg/raw public projects)
# 2. python embed (to compute and store embeddings)

project_embedding_job = define_asset_job(
    name="project_embedding_job",
    selection=AssetSelection.groups("ml")
    | AssetSelection.groups("ml_preparation")
    | AssetSelection.groups("classification")
    | AssetSelection.groups("matching"),
    description=(
        "Runs classification, DBT models for ML context, "
        "and computes project embeddings."
    ),
)
