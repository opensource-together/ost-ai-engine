from dagster import (
    Definitions,
    define_asset_job,
)
from .schedules.github import make_github_scraper_schedule
from .resources.cfg_resource import config_resource
from .assets.raw.assets import (
    github_scraper_asset,
    github_mapping_asset,
    github_top_projects_asset,
    github_to_db_asset,
    gitlab_scraper_asset,
)

from .assets.raw.asset_checks import (
    github_top_projects_description_check,
)

github_scraper_job = define_asset_job(
    name="github_scraper_job",
    selection=[
        "github_scraper_asset",
        "github_top_projects_asset",
        "github_mapping_asset",
        "github_to_db_asset",
    ],
    description=(
        "Pipeline to scrape trending GitHub projects, rank them, "
        "normalize their data structure, and insert the results into the database. "
        "Includes data quality checks at each step."
    ),
)

# Build schedule using the schedules factory to avoid circular imports
github_scraper_schedule = make_github_scraper_schedule(github_scraper_job)

defs = Definitions(
    assets=[
        github_scraper_asset,
        github_top_projects_asset,
        github_mapping_asset,
        github_to_db_asset,
        gitlab_scraper_asset
    ],
    resources={
        "config": config_resource,
    },
    asset_checks=[
        github_top_projects_description_check,
    ],
    jobs=[github_scraper_job],
    schedules=[github_scraper_schedule],
)
