from dagster import Definitions
from .assets import github_scraper_asset, gitlab_scraper_asset, github_mapping_asset

defs = Definitions(assets=[
    github_scraper_asset, 
    gitlab_scraper_asset,
    github_mapping_asset
])
