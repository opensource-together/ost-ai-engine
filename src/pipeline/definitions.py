from dagster import Definitions

from .schedules.github_scraper_schedule import make_github_scraper_schedule
from .resources.cfg_resource import config_resource
from .resources.fasttext_resource import fasttext_model_resource
from .assets.scraper.raw.assets import (
    raw_github__extract_projects,
)
from .assets.scraper.core.assets import (
    raw_github__to_df,
    core_repo_lang_detect,
    core_repo_primary_language_filter,
    core_merge_filtered_projects,
    core_github__extract_top_projects,
    core_github__table_projects_mapped,
    core_github__fetch_repo_languages,
    core_github__fetch_repo_topics,
    core_github__fetch_readme,
    core_github__merge_repo_meta,
    core_github__map_languages_to_techstacks,
)
from .assets.scraper.out.assets import (
    out_github__table_projects_db,
)
from .jobs.cleanup_dagster_job import cleanup_dagster_history_job
from .schedules.cleanup_dagster_schedule import cleanup_dagster_history_schedule
from .assets.scraper.raw.asset_checks import (
    raw_github__extract_projects_non_empty,
)

from .assets.scraper.core.asset_checks import (
    core_github__extract_top_projects_description_is_not_empty,
    core_repo_lang_detect_language_fields_present,
    core_github__table_projects_mapped_repoUrl_present,
)
from .assets.scraper.out.asset_checks import (
    out_github__table_projects_db_counts_valid,
)

from .jobs.github_scraper_job import github_scraper_job
from .jobs.embedding_jobs import (
    projects_embedding_job,
    categories_embedding_job,
    users_embedding_job,
)

# schedule
github_scraper_schedule = make_github_scraper_schedule(github_scraper_job)

defs = Definitions(
    assets=[
    # raw assets
    raw_github__extract_projects,
    raw_github__to_df,

    # core assets
    core_repo_lang_detect,
    core_repo_primary_language_filter,
    core_merge_filtered_projects,
    core_github__extract_top_projects,
    core_github__table_projects_mapped,
    core_github__fetch_repo_languages,
    core_github__fetch_repo_topics,
    core_github__fetch_readme,
    core_github__merge_repo_meta,
    core_github__map_languages_to_techstacks,

    # out assets
    out_github__table_projects_db
    ],
    resources={
        "config": config_resource,
        "fasttext_model": fasttext_model_resource.configured({
            "model_path": "/app/models/lid.176.ftz"
        }),
    },
    asset_checks=[
        # raw scraper results
        raw_github__extract_projects_non_empty,

        # core transforms / checks
        core_repo_lang_detect_language_fields_present,
        core_github__extract_top_projects_description_is_not_empty,
        core_github__table_projects_mapped_repoUrl_present,

        # out checks
        out_github__table_projects_db_counts_valid,
    ],
    jobs=[
        github_scraper_job,
        cleanup_dagster_history_job,
        projects_embedding_job,
        categories_embedding_job,
        users_embedding_job,
    ],
    schedules=[github_scraper_schedule, cleanup_dagster_history_schedule],
)
