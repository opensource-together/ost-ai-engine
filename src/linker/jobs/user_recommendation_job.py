from dagster import AssetKey, AssetSelection, define_asset_job

user_recommendation_job = define_asset_job(
    name="user_recommendation_job",
    selection=AssetSelection.groups("ml_preparation", "matching")
    | AssetSelection.assets(AssetKey(["ml", "embd_user"]))
    | AssetSelection.assets(AssetKey(["public", "Project"])),
    tags={"dagster/max_concurrent_runs": "1"},
    description=(
        "Refreshes dbt ML preparation models, recomputes user embeddings, "
        "materializes matching recommendations, and syncs to public Project table."
    ),
)
