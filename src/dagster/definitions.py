from dagster import Definitions
from .assets import *

defs = Definitions(
    assets=[
        github_scraper_asset,
        gitlab_scraper_asset,
        github_mapping_asset
    ],
    asset_checks=[
        github_mapping_type_check,
        github_mapping_required_fields_check,
        github_mapping_duplicate_url_check
    ]
)
