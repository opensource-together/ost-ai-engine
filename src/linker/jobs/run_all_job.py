from dagster import define_asset_job, AssetSelection

run_all_job = define_asset_job(
    name="run_all_job",
    selection=AssetSelection.all()
)
