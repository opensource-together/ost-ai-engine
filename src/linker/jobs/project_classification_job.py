from dagster import AssetSelection, define_asset_job

project_classification_job = define_asset_job(
    name="project_classification_job",
    selection=AssetSelection.groups("classification"),
    description=(
        "Orchestrates the LLM classification of projects into Categories and Domains."
    ),
)
