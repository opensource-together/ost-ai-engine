from dagster import Definitions, load_assets_from_modules

from .schedules.github_scraper_schedule import make_github_scraper_schedule
from .resources.cfg_resource import config_resource
from .resources.fasttext_resource import fasttext_model_resource
from .assets.scraper.raw import github as raw_github
from .assets.scraper.core import filtering, fetching, mapping, categorization
from .assets.scraper.out import github as out_github

raw_assets = load_assets_from_modules([raw_github])
core_assets = load_assets_from_modules([
    filtering,
    fetching,
    mapping,
    categorization
])
out_assets = load_assets_from_modules([out_github])

from .jobs.cleanup_dagster_job import cleanup_dagster_history_job
from .schedules.cleanup_dagster_schedule import cleanup_dagster_history_schedule

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
    *raw_assets,

    # core assets
    *core_assets,

    # out assets
    *out_assets,
    ],
    resources={
        "config": config_resource,
        "fasttext_model": fasttext_model_resource.configured({
            "model_path": "/app/models/lid.176.ftz"
        }),
    },
    jobs=[
        github_scraper_job,
        cleanup_dagster_history_job,
        projects_embedding_job,
        categories_embedding_job,
        users_embedding_job,
    ],
    schedules=[github_scraper_schedule, cleanup_dagster_history_schedule],
)
