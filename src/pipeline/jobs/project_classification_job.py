from dagster import define_asset_job, AssetSelection, AssetKey

project_classification_job = define_asset_job(
    name="project_classification_job",
    selection=AssetSelection.groups("matching"),
    description="Syncs projects and classifies them using LLM (Phi-3.5)."
)
