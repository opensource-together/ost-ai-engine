from dagster import AssetSelection, define_asset_job

user_recommendation_job = define_asset_job(
    name="user_recommendation_job",
    selection=AssetSelection.assets("core_ml__embed_users")
    | AssetSelection.groups("matching")
    | AssetSelection.assets("core_public__sync_projects"),
    description=(
        "Recomputes user embeddings, refreshes matching models, "
        "and syncs results to the public Project table."
    ),
)
