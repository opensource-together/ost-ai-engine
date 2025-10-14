from dagster import Definitions, ScheduleDefinition, define_asset_job
from .assets import (
    github_scraper_asset,
    github_mapping_asset,
    github_top_projects_asset,
    github_to_db_asset,
    github_top_projects_description_check,
    github_top_projects_date_check,
    github_mapping_type_check,
    github_mapping_required_fields_check,
    github_mapping_duplicate_url_check,
    github_to_db_insert_count_check,
    github_to_db_error_check,
    github_to_db_consistency_check,
    github_to_db_uniqueness_check,
    github_to_db_mapping_match_check,
)

github_scraper_job = define_asset_job(
    name="github_scraper_job",
    selection=[
        "github_scraper_asset",
        "github_top_projects_asset",
        "github_mapping_asset",
        "github_to_db_asset"
    ]
)

github_scraper_schedule = ScheduleDefinition(
    job=github_scraper_job,
    cron_schedule="0 */6 * * *",  # every 6 hrs
)

defs = Definitions(
    assets=[
        github_scraper_asset,
        github_top_projects_asset,
        github_mapping_asset,
        github_to_db_asset
    ],
    asset_checks=[
        github_top_projects_description_check,
        github_top_projects_date_check,
        github_mapping_type_check,
        github_mapping_required_fields_check,
        github_mapping_duplicate_url_check,
        github_to_db_insert_count_check,
        github_to_db_error_check,
        github_to_db_consistency_check,
        github_to_db_uniqueness_check,
        github_to_db_mapping_match_check
    ],
    jobs=[github_scraper_job],
    schedules=[github_scraper_schedule]
)
