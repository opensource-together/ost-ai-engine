from dagster import Definitions, load_assets_from_modules, AssetExecutionContext
from dagster_dbt import DbtCliResource, dbt_assets, DbtProject
from pathlib import Path

import os
# Use env var or fallback to relative path from this file
# This file is in src/pipeline/definitions.py
# dbt is in dbt (root)
# So relative path is ../../dbt
DEFAULT_DBT_DIR = Path(__file__).parent.parent.parent / "dbt"
DBT_PROJECT_DIR = Path(os.getenv("DBT_PROJECT_DIR", DEFAULT_DBT_DIR)).resolve()
dbt_project = DbtProject(
    project_dir=DBT_PROJECT_DIR,
    profiles_dir=DBT_PROJECT_DIR,
)
dbt_project.prepare_if_dev()

@dbt_assets(manifest=dbt_project.manifest_path, name="dbt_models")
def dbt_project_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()

dbt_resource = DbtCliResource(project_dir=DBT_PROJECT_DIR)

dbt_assets_list = [dbt_project_assets]
for asset in dbt_assets_list:
    # dbt_assets returns a CacheableAssetsDefinition or AssetsDefinition. 
    # We can't easily mutate it if it's cacheable.
    # But dagster-dbt 0.25+ returns AssetsDefinition.
    # Let's try to wrap it or just rely on 'default' group if we can't change it easily.
    # Or use the 'group' argument in dbt_project.yml? No.
    # Actually, we can just include "default" group in the job if dbt assets are there.
    pass

from .schedules.github_scraper_schedule import make_github_scraper_schedule
from .resources.cfg_resource import config_resource
from .resources.fasttext_resource import FastTextModelResource
from .resources.embedding_model_resource import EmbeddingModelResource

# Scraper Assets
from .assets.scraper import (
    raw_github__extract_projects,
    raw_github__load_project,
    core_github__detect_languages,
    core_github__fetch_readme,
    core_github__fetch_repo_languages,
    core_github__fetch_repo_topics,
)

# Embedding Assets
from .assets.embedding import (
    raw_projects__prepare_context,
    core_projects__compute_embeddings,
    out_projects__store_embeddings,
)

scraper_assets = load_assets_from_modules([
    raw_github__extract_projects,
    raw_github__load_project,
    core_github__detect_languages,
    core_github__fetch_readme,
    core_github__fetch_repo_languages,
    core_github__fetch_repo_topics,
])

embedding_assets = load_assets_from_modules([
    raw_projects__prepare_context,
    core_projects__compute_embeddings,
    out_projects__store_embeddings,
])

from .jobs.cleanup_dagster_job import cleanup_dagster_history_job
from .schedules.cleanup_dagster_schedule import cleanup_dagster_history_schedule

from .jobs.github_scraper_job import github_scraper_job
from .jobs.embedding_jobs import project_embedding_job
from .sensors import embedding_job_sensor

# schedule
github_scraper_schedule = make_github_scraper_schedule(github_scraper_job)

defs = Definitions(
    assets=[
        *scraper_assets,
        *embedding_assets,
        *dbt_assets_list,
    ],
    resources={
        "config": config_resource,
        "fasttext_model": FastTextModelResource(),
        "embedding_model": EmbeddingModelResource(),
        "dbt": dbt_resource,
    },
    jobs=[
        github_scraper_job,
        cleanup_dagster_history_job,
        project_embedding_job,
    ],
    schedules=[github_scraper_schedule, cleanup_dagster_history_schedule],
    sensors=[embedding_job_sensor],
)
