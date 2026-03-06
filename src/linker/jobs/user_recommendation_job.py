from dagster import AssetSelection, define_asset_job

user_recommendation_job = define_asset_job(
    name="user_recommendation_job",
    selection=AssetSelection.groups("user_ml"),
    tags={"dagster/max_concurrent_runs": "1"},
    description=(
        "Refreshes user dbt models, recomputes user embeddings, "
        "and materializes user-specific recommendations."
    ),
)
