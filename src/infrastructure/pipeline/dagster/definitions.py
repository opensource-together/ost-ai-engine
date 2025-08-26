"""
Dagster definitions for the data engine pipeline.

This module declares:
- Resources (e.g., GitHub client)
- Jobs (e.g., repository scraping)
- The assembled Definitions object discovered by Dagster webserver/CLI.
"""

from __future__ import annotations

from dagster import Definitions, define_asset_job, IOManager, InputManager, io_manager, input_manager
from dagster_dbt import DbtCliResource

from .assets.dbt import DBT_PROJECT_DIR, ml_project_embeddings_asset, github_to_project_asset, embed_PROJECTS_dbt_asset, embed_USERS_dbt_asset
from .assets.embedding_assets import project_embeddings_asset, hybrid_project_embeddings_asset
from .assets.user_embedding_assets import user_embeddings
from .assets.github_assets import github_project_table, github_repositories
from .assets.reference_assets import reference_tables_populated, projects_mapped, mapping_completed


from .resources.embedding_service import embedding_service
from .resources.github_client import github_client


# Job global qui orchestre tout le pipeline de bout en bout (sans reference_tables_populated car one-shot)
training_data_pipeline = define_asset_job(
    "training_data_pipeline", 
    description="Complete pipeline: GitHub scraping → data transformation → project mapping → ML training data preparation",
    # Dagster orchestrates the order via dependencies in each asset
    selection=[
        "github_repositories",      # 1. Scrape GitHub API and upsert → github_PROJECT
        "github_project_table",     # 2. Checkpoint: verify github_PROJECT
        "github_to_project",        # 3. Transform → PROJECT (dbt)
        "projects_mapped",          # 4. Map projects → relations (Python)
        "mapping_completed",        # 5. Checkpoint: mappings done
        "ml_project_embeddings",    # 6. Prepare project embedding data (dbt)
        "project_embeddings",       # 7. Generate semantic embeddings (Python)
        "hybrid_project_embeddings", # 8. Generate hybrid embeddings (Python) - NEW!
        "embed_USERS",               # 9. Prepare user embedding data (dbt)
        "user_embeddings",          # 10. Generate user embeddings (Python)
    ],
)

defs = Definitions(
    assets=[
        github_repositories, 
        github_project_table, 
        reference_tables_populated,
        projects_mapped,
        mapping_completed,
        ml_project_embeddings_asset,  # Prepare project embedding data
        github_to_project_asset,  # Individual dbt asset with explicit dependencies
        embed_PROJECTS_dbt_asset,  # dbt model for project embedding preparation
        embed_USERS_dbt_asset,  # dbt model for user embedding preparation
        project_embeddings_asset,  # Generate semantic embeddings
        hybrid_project_embeddings_asset,  # Generate hybrid embeddings - NEW!
        user_embeddings,  # Generate user embeddings
    ],
    jobs=[training_data_pipeline],
    resources={
        "github_client": github_client,
        "embedding_service": embedding_service(),
        "dbt": DbtCliResource(
            project_dir=str(DBT_PROJECT_DIR),
            profiles_dir=str(DBT_PROJECT_DIR),
        ),
        "nothing_input": input_manager(lambda context, obj: None),
    },
)


