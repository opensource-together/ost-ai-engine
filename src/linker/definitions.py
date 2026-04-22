"""
Dagster definitions for the linker package.

This module is imported at process startup, before Dagster resources are
constructed. For that reason, bootstrap values needed at import time are
read from `settings.py`.
"""

import os
from collections.abc import Iterator
from typing import Any

from dagster import (
    AssetExecutionContext,
    Definitions,
    EnvVar,
    FilesystemIOManager,
    load_assets_from_modules,
)
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

from .settings import settings

# Import-time bootstrap config belongs in settings.py.
DBT_PROJECT_DIR = settings.dbt_project_dir

dbt_project = DbtProject(
    project_dir=DBT_PROJECT_DIR,
    profiles_dir=DBT_PROJECT_DIR,
)
dbt_project.prepare_if_dev()


@dbt_assets(manifest=dbt_project.manifest_path, name="dbt_models")
def dbt_project_assets(
    context: AssetExecutionContext,
    dbt: DbtCliResource,
) -> Iterator[Any]:
    yield from dbt.cli(
        ["build", "--indirect-selection", "cautious"], context=context
    ).stream()


dbt_resource = DbtCliResource(project_dir=DBT_PROJECT_DIR)

dbt_assets_list = [dbt_project_assets]

# scraper Assets
from .assets.scraper import (
    core_github__detect_languages,
    core_github__fetch_readme,
    core_github__fetch_repo_languages,
    core_github__fetch_repo_topics,
    raw_github__extract_projects,
    raw_github__extract_trending,
)
from .resources.cfg_resource import PipelineConfig
from .resources.fasttext_resource import FastTextModelResource
from .resources.io_manager import PandasPostgresIOManager
from .resources.llm_classifier_resource import LLMClassifierResource
from .resources.sentence_transformer_resource import SentenceTransformerResource

scraper_assets = load_assets_from_modules(
    [
        raw_github__extract_projects,
        raw_github__extract_trending,
        core_github__detect_languages,
        core_github__fetch_readme,
        core_github__fetch_repo_languages,
        core_github__fetch_repo_topics,
    ]
)

# classification Assets
from .assets.classification.core_match__classify_projects import (
    core_match__classify_projects,
)

# ML Assets
from .assets.embedding.core_ml__embed_projects import core_ml__embed_projects
from .assets.embedding.core_ml__embed_users import core_ml__embed_users
from .assets.sync.core_public__sync_projects import core_public__sync_projects
from .jobs.cleanup_dagster_job import cleanup_dagster_history_job
from .jobs.project_enrichment_job import project_enrichment_job

# jobs
from .jobs.run_all_job import run_all_job
from .jobs.user_recommendation_job import user_recommendation_job
from .schedules.cleanup_dagster_schedule import cleanup_dagster_history_schedule

# schedule
from .schedules.project_enrichment_schedule import project_enrichment_schedule
from .schedules.user_recommendation_schedule import user_recommendation_schedule


def build_assets() -> list[Any]:
    """Return the assets registered in the Linker Dagster repository."""
    return [
        *scraper_assets,
        *dbt_assets_list,
        core_match__classify_projects,
        core_public__sync_projects,
        core_ml__embed_projects,
        core_ml__embed_users,
    ]


def build_resources() -> dict[str, Any]:
    """Return Dagster resources configured for runtime resolution."""
    return {
        "config": PipelineConfig(
            db_url=EnvVar("DATABASE_URL"),
            github_token=EnvVar("GITHUB_ACCESS_TOKEN"),
            go_scraper_path=EnvVar("GO_SCRAPER_PATH"),
            go_fetcher_path=EnvVar("GO_FETCHER_PATH"),
            **(
                {
                    "go_trending_path": EnvVar("GO_TRENDING_PATH"),
                }
                if os.getenv("GO_TRENDING_PATH")
                else {}
            ),
        ),
        "fasttext_model": FastTextModelResource(
            model_path=EnvVar("FASTTEXT_MODEL_PATH"),
        ),
        "llm_classifier": LLMClassifierResource(
            api_key=EnvVar("MISTRAL_API_KEY"),
        ),
        "sentence_transformer": SentenceTransformerResource(
            device="cpu"
        ),  # Using CPU for embedding for now, or mps
        "dbt": dbt_resource,
        "io_manager": PandasPostgresIOManager(db_url=EnvVar("DATABASE_URL")),
        "streaming_io_manager": PandasPostgresIOManager(
            db_url=EnvVar("DATABASE_URL"),
            chunk_size=10_000,
        ),
        "fs_io_manager": FilesystemIOManager(),
    }


def build_jobs() -> list[Any]:
    """Return jobs exposed by the Linker Dagster repository."""
    return [
        cleanup_dagster_history_job,
        project_enrichment_job,
        run_all_job,
        user_recommendation_job,
    ]


def build_schedules() -> list[Any]:
    """Return schedules exposed by the Linker Dagster repository."""
    return [
        cleanup_dagster_history_schedule,
        project_enrichment_schedule,
        user_recommendation_schedule,
    ]


def build_sensors() -> list[Any]:
    """Return sensors exposed by the Linker Dagster repository."""
    return []


defs = Definitions(
    assets=build_assets(),
    resources=build_resources(),
    jobs=build_jobs(),
    schedules=build_schedules(),
    sensors=build_sensors(),
)
