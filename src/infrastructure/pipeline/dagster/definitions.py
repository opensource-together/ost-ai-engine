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

from .assets.dbt import DBT_PROJECT_DIR, dbt_project_embeddings_data_asset, dbt_projects_asset, dbt_project_enriched_data_asset, dbt_user_embeddings_data_asset
from .assets.embedding_assets import project_semantic_embeddings_asset, project_hybrid_embeddings_asset
from .assets.user_embedding_assets import user_embeddings
from .assets.github_assets import github_data_ready, github_scraping
from .assets.reference_assets import project_mappings, mappings_ready


from .resources.embedding_service import embedding_service
from .resources.github_client import github_client


# Job global qui orchestre tout le pipeline de bout en bout (sans reference_tables_populated car one-shot)
training_data_pipeline = define_asset_job(
    "training_data_pipeline", 
    description="Complete pipeline: GitHub scraping → data transformation → project mapping → ML training data preparation",
    # Dagster orchestrates the order via dependencies in each asset
    selection=[
        "github_scraping",          # 1. Scrape GitHub API and upsert → github_PROJECT
        "github_data_ready",        # 2. Checkpoint: verify github_PROJECT
        "dbt_projects",             # 3. Transform → PROJECT (dbt)
        "project_mappings",         # 4. Map projects → relations (Python)
        "mappings_ready",           # 5. Checkpoint: mappings done
        "dbt_project_embeddings_data", # 6. Prepare project embedding data (dbt)
        "project_semantic_embeddings", # 7. Generate semantic embeddings (Python)
        "project_hybrid_embeddings",   # 8. Generate hybrid embeddings (Python)
        "dbt_user_embeddings_data",    # 9. Prepare user embedding data (dbt)
        "user_embeddings",             # 10. Generate user embeddings (Python)
    ],
)

defs = Definitions(
    assets=[
        github_scraping, 
        github_data_ready, 
        project_mappings,
        mappings_ready,
        dbt_project_embeddings_data_asset,  # Prepare project embedding data
        dbt_projects_asset,  # Individual dbt asset with explicit dependencies
        dbt_project_enriched_data_asset,  # dbt model for project embedding preparation
        dbt_user_embeddings_data_asset,  # dbt model for user embedding preparation
        project_semantic_embeddings_asset,  # Generate semantic embeddings
        project_hybrid_embeddings_asset,  # Generate hybrid embeddings
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


