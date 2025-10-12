from dagster import Definitions
from .assets import (
    github_scraper_asset,
    gitlab_scraper_asset,
    github_mapping_asset,
    github_to_db_asset,
    github_mapping_type_check,
    github_mapping_required_fields_check,
    github_mapping_duplicate_url_check,
    github_to_db_insert_count_check,
    github_to_db_error_check,
    github_to_db_consistency_check,
    github_to_db_uniqueness_check,
    github_to_db_mapping_match_check,
)

defs = Definitions(
    assets=[
        github_scraper_asset,
        gitlab_scraper_asset,
        github_mapping_asset,
        github_to_db_asset
    ],
    asset_checks=[
        github_mapping_type_check,
        github_mapping_required_fields_check,
        github_mapping_duplicate_url_check,
        github_to_db_insert_count_check,
        github_to_db_error_check,
        github_to_db_consistency_check,
        github_to_db_uniqueness_check,
        github_to_db_mapping_match_check
    ]
)
