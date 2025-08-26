from __future__ import annotations
import subprocess
import os
from pathlib import Path

from dagster import asset, Output, AssetIn, Nothing

# Use centralized config instead of manual dotenv loading
from src.infrastructure.config import settings

# Use PROJECT_ROOT from config for dbt project directory
DBT_PROJECT_DIR = (Path(settings.PROJECT_ROOT) / settings.DBT_PROJECT_DIR).resolve()


@asset(
    name="dbt_raw_repositories",
    description="Create raw_github_repositories table structure via dbt",
    group_name="data_transformation",
    compute_kind="dbt",
)
def dbt_raw_repositories_asset(context) -> Output[None]:
    """
    Creates the raw_github_repositories table structure using dbt.
    This must run before the GitHub scraper tries to insert data.
    """
    context.log.info(f"🚀 Creating raw_github_repositories table structure")
    # Use subprocess to run dbt directly with correct parameters
    result = subprocess.run(
        ["dbt", "run", "--select", "raw_github_repositories", "--profiles-dir", str(DBT_PROJECT_DIR), "--project-dir", str(DBT_PROJECT_DIR)],
        capture_output=True,
        text=True,
        cwd=str(DBT_PROJECT_DIR) # Ensure dbt runs from its project directory
    )
    context.log.info(result.stdout)
    if result.stderr:
        context.log.error(result.stderr)
    if result.returncode != 0:
        raise Exception(f"dbt run failed: {result.stderr}")
    context.log.info(f"✅ raw_github_repositories table created successfully.")
    return Output(None)


@asset(
    name="dbt_project_embeddings_data",
    description="Execute ml_project_embeddings dbt model to prepare project embedding data",
    ins={"project_data": AssetIn("dbt_projects", dagster_type=Nothing)},  # Wait for dbt_projects
    group_name="ml_preparation",
    compute_kind="dbt",
)
def dbt_project_embeddings_data_asset(context) -> Output[None]:
    """
    Runs the dbt model `ml_project_embeddings` to prepare project data for embeddings.
    This creates embed_PROJECTS_temp table.
    """
    context.log.info(f"🚀 Starting dbt model: ml_project_embeddings")
    # Use subprocess to run dbt directly with correct parameters
    result = subprocess.run(
        ["dbt", "run", "--select", "ml_project_embeddings", "--profiles-dir", str(DBT_PROJECT_DIR), "--project-dir", str(DBT_PROJECT_DIR)],
        capture_output=True,
        text=True,
        cwd=str(DBT_PROJECT_DIR) # Ensure dbt runs from its project directory
    )
    context.log.info(result.stdout)
    if result.stderr:
        context.log.error(result.stderr)
    if result.returncode != 0:
        raise Exception(f"dbt run failed: {result.stderr}")
    context.log.info(f"✅ dbt model ml_project_embeddings completed.")
    return Output(None)


@asset(
    name="dbt_projects",
    description="Execute github_to_project dbt model with dependency control",
    ins={"github_data": AssetIn("github_data_ready", dagster_type=Nothing)}, # Wait for GitHub data
    group_name="data_transformation",
    compute_kind="dbt",
)
def dbt_projects_asset(context) -> Output[None]:
    """
    Runs the dbt model `github_to_project` to transform raw GitHub data into the PROJECT table.
    """
    context.log.info(f"🚀 Starting dbt model: github_to_project")
    # Use subprocess to run dbt directly with correct parameters
    result = subprocess.run(
        ["dbt", "run", "--select", "github_to_project", "--profiles-dir", str(DBT_PROJECT_DIR), "--project-dir", str(DBT_PROJECT_DIR)],
        capture_output=True,
        text=True,
        cwd=str(DBT_PROJECT_DIR) # Ensure dbt runs from its project directory
    )
    context.log.info(result.stdout)
    if result.stderr:
        context.log.error(result.stderr)
    if result.returncode != 0:
        raise Exception(f"dbt run failed: {result.stderr}")
    context.log.info(f"✅ dbt model github_to_project completed.")
    return Output(None)



@asset(
    name="dbt_project_enriched_data",
    description="Execute embed_PROJECTS dbt model with dependency control",
    ins={"mapping_data": AssetIn("mappings_ready", dagster_type=Nothing)}, # Wait for mapping to complete
    group_name="ml_preparation",
    compute_kind="dbt",
)
def dbt_project_enriched_data_asset(context) -> Output[None]:
    """
    Runs the dbt model `embed_PROJECTS` to prepare enriched data for embeddings.
    """
    context.log.info(f"🚀 Starting dbt model: embed_PROJECTS")
    # Use subprocess to run dbt directly with correct parameters
    result = subprocess.run(
        ["dbt", "run", "--select", "embed_PROJECTS", "--profiles-dir", str(DBT_PROJECT_DIR), "--project-dir", str(DBT_PROJECT_DIR)],
        capture_output=True,
        text=True,
        cwd=str(DBT_PROJECT_DIR) # Ensure dbt runs from its project directory
    )
    context.log.info(result.stdout)
    if result.stderr:
        context.log.error(result.stderr)
    if result.returncode != 0:
        raise Exception(f"dbt run failed: {result.stderr}")
    context.log.info(f"✅ dbt model embed_PROJECTS completed.")
    return Output(None)


@asset(
    name="dbt_user_embeddings_data",
    description="Execute embed_USERS dbt model with dependency control",
    ins={"mapping_data": AssetIn("mappings_ready", dagster_type=Nothing)}, # Wait for mapping to complete
    group_name="ml_preparation",
    compute_kind="dbt",
)
def dbt_user_embeddings_data_asset(context) -> Output[None]:
    """
    Runs the dbt model `embed_USERS` to prepare enriched user data for embeddings.
    """
    context.log.info(f"🚀 Starting dbt model: embed_USERS")
    # Use subprocess to run dbt directly with correct parameters
    result = subprocess.run(
        ["dbt", "run", "--select", "embed_USERS", "--profiles-dir", str(DBT_PROJECT_DIR), "--project-dir", str(DBT_PROJECT_DIR)],
        capture_output=True,
        text=True,
        cwd=str(DBT_PROJECT_DIR) # Ensure dbt runs from its project directory
    )
    context.log.info(result.stdout)
    if result.stderr:
        context.log.error(result.stderr)
    if result.returncode != 0:
        raise Exception(f"dbt run failed: {result.stderr}")
    context.log.info(f"✅ dbt model embed_USERS completed.")
    return Output(None)
