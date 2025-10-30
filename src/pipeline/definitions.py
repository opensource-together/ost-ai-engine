from dagster import (
    Definitions,
    define_asset_job,
    multiprocess_executor,
    in_process_executor,
    AssetSelection,
)
from .schedules.github import make_github_scraper_schedule
from .resources.cfg_resource import config_resource
from .assets.raw.assets import (
    raw_github__extract_projects,
    raw_gitlab__extract_projects,
)
from .assets.core.assets import (
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
    core_github__normalize_repo_meta,
    core_github__map_languages_to_techstacks,
    core_github__map_topics_to_categories,
)
from .assets.out.assets import (
    out_github__table_projects_db,
)

from .assets.raw.asset_checks import (
    raw_github__extract_projects_non_empty,
    raw_gitlab__extract_projects_non_empty,
)
from .assets.core.asset_checks import (
    core_github__extract_top_projects_description_is_not_empty,
    core_repo_lang_detect_language_fields_present,
    core_github__table_projects_mapped_repoUrl_present,
)
from .assets.out.asset_checks import (
    out_github__table_projects_db_counts_valid,
)

# Use the in-process executor for the sensitive pipeline to avoid child process
# crashes caused by C-extensions (pandas/numpy/BLAS) in forked processes.
github_scraper_job = define_asset_job(
    name="github_scraper_job",
    selection=AssetSelection.groups("github_projects_scraper"),
    executor_def=in_process_executor,
    description=(
        "Scrape trending repositories (GitHub and GitLab), filter and rank them, "
        "normalize to the Prisma Project schema, and upsert the results into the database. "
        "The job runs the Go scrapers, applies language detection and data-quality checks, "
        "maps fields to the Project model, and emits insert/update metrics. "
        "Configurable (scraper queries, top-N, fastText model path) and safe for repeated runs."
    ),
)

# Optional: a safer multiprocess variant that limits concurrency and uses
github_scraper_job_mp_limited = define_asset_job(
    name="github_scraper_job_mp_limited",
    selection=AssetSelection.groups("github_projects_scraper"),
    executor_def=multiprocess_executor.configured({"max_concurrent": 1, "start_method": {"forkserver": {}}}),
    description="Multiprocess variant with max_concurrent and forkserver start method",
)

# Build schedule using the schedules factory to avoid circular imports
github_scraper_schedule = make_github_scraper_schedule(github_scraper_job)

defs = Definitions(
    assets=[
    raw_github__extract_projects,
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
    core_github__normalize_repo_meta,
    core_github__map_languages_to_techstacks,
    core_github__map_topics_to_categories,
        out_github__table_projects_db,
        raw_gitlab__extract_projects
    ],
    resources={
        "config": config_resource,
    },
    asset_checks=[
        # raw scraper results
        raw_github__extract_projects_non_empty,
        raw_gitlab__extract_projects_non_empty,

        # core transforms / checks
        core_repo_lang_detect_language_fields_present,
        core_github__extract_top_projects_description_is_not_empty,
        core_github__table_projects_mapped_repoUrl_present,

        # out checks
        out_github__table_projects_db_counts_valid,
    ],
    jobs=[github_scraper_job],
    schedules=[github_scraper_schedule],
)
