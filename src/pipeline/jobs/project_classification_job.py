from dagster import define_asset_job, AssetSelection, AssetKey

project_classification_job = define_asset_job(
    name="project_classification_job",
    selection=AssetSelection.groups("classification"),
    description="Orchestrates the LLM classification of projects into Categories and Domains."
)
