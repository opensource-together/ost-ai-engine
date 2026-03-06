from dagster import AssetKey, AssetSelection, define_asset_job

user_recommendation_job = define_asset_job(
    name="user_recommendation_job",
    selection=AssetSelection.groups("ml_user_preparation")
    | AssetSelection.assets(AssetKey(["ml", "embd_user"]))
    | AssetSelection.assets(AssetKey(["public", "match_user_recommendation"])),
    tags={"dagster/max_concurrent_runs": "1"},
    description=(
        "Refreshes user dbt models, recomputes user embeddings, "
        "and materializes user-specific recommendations."
    ),
)
