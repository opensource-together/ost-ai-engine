from dagster import Definitions, EnvVar, load_assets_from_modules, AssetExecutionContext, FilesystemIOManager
from dagster_dbt import DbtCliResource, dbt_assets, DbtProject
from pathlib import Path

import os
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

from .resources.cfg_resource import PipelineConfig
from .resources.fasttext_resource import FastTextModelResource

from .resources.llm_classifier_resource import LLMClassifierResource
from .resources.sentence_transformer_resource import SentenceTransformerResource
from .resources.io_manager import PandasPostgresIOManager

db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise ValueError("DATABASE_URL environment variable is not set")

postgres_io_manager = PandasPostgresIOManager(db_url=db_url)

# scraper Assets
from .assets.scraper import (
    raw_github__extract_projects,
    core_github__detect_languages,
    core_github__fetch_readme,
    core_github__fetch_repo_languages,
    core_github__fetch_repo_topics,
)

scraper_assets = load_assets_from_modules([
    raw_github__extract_projects,
    core_github__detect_languages,
    core_github__fetch_readme,
    core_github__fetch_repo_languages,
    core_github__fetch_repo_topics,
])

from .jobs.cleanup_dagster_job import cleanup_dagster_history_job
from .schedules.cleanup_dagster_schedule import cleanup_dagster_history_schedule

from .jobs.project_scraper_job import project_scraper_job

# classification Assets
from .assets.classification.core_match__classify_projects import core_match__classify_projects
from .assets.sync.core_public__sync_projects import core_public__sync_projects


# ML Assets
from .assets.embedding.core_ml__embed_projects import core_ml__embed_projects
from .assets.embedding.core_ml__embed_users import core_ml__embed_users

# schedule
from .schedules.run_all_schedule import run_all_schedule

# jobs
from .jobs.run_all_job import run_all_job
from .jobs.project_classification_job import project_classification_job
from .jobs.project_embedding_job import project_embedding_job

from .sensors.classification_sensor import classification_sensor

defs = Definitions(
    assets=[
        *scraper_assets,
        *dbt_assets_list,
        core_match__classify_projects,
        core_public__sync_projects,
        core_ml__embed_projects,
        core_ml__embed_users,
    ],
    resources={
        "config": PipelineConfig(
            db_url=EnvVar("DATABASE_URL"),
            github_token=EnvVar("GITHUB_ACCESS_TOKEN"),
            go_scraper_path=EnvVar("GO_SCRAPER_PATH"),
            go_fetcher_path=EnvVar("GO_FETCHER_PATH"),
        ),
        "fasttext_model": FastTextModelResource(),
        "llm_classifier": LLMClassifierResource(), # API based (OpenRouter)
        "sentence_transformer": SentenceTransformerResource(device="cpu"), # Using CPU for embedding for now, or mps
        "dbt": dbt_resource,
        "io_manager": postgres_io_manager,
        "fs_io_manager": FilesystemIOManager(),
    },
    jobs=[
        project_scraper_job,
        cleanup_dagster_history_job,
        project_classification_job,
        project_embedding_job,
        run_all_job,
    ],
    schedules=[cleanup_dagster_history_schedule, run_all_schedule],
    sensors=[classification_sensor],
)
