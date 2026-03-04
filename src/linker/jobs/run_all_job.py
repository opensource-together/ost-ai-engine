from dagster import AssetSelection, define_asset_job

run_all_job = define_asset_job(name="run_all_job", selection=AssetSelection.all())
