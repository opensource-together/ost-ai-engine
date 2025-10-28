import os
import yaml
from dotenv import load_dotenv
from dagster import Config
from pydantic import Field
from pathlib import Path

load_dotenv()

CONFIG_YAML_PATH = os.getenv("OST_CONFIG_PATH")

with open(CONFIG_YAML_PATH, "r") as f:
    config_yaml = yaml.safe_load(f)

class PipelineConfig(Config):
    """
    Central configuration for the Dagster pipeline.
    All secrets and connection info are loaded from config/cfg.yaml.
    """

    # ENV
    db_url: str = Field(
        default=config_yaml.get("DATABASE_URL", ""),
        description="Database connection string (e.g. postgresql://user:pass@host:port/dbname)"
    )
    # FastText model path used by core language detection
    fasttext_model_path: str = Field(
        default=config_yaml.get("FASTTEXT_MODEL_PATH", ""),
        description="Filesystem path to the FastText lid.176.ftz model used for language identification",
    )

    # GITHUB
    github_token: str = Field(
        default=config_yaml.get("GITHUB_ACCESS_TOKEN", ""),
        description="GitHub API access token"
    )
    github_scraping_query: str = Field(
        default=config_yaml.get("GITHUB_SCRAPING_QUERY", ""),
        description="GitHub scraper parameter query"
    )
    github_scraper_cron: str = Field(
        default=config_yaml.get("GITHUB_SCRAPER_CRON", ""),
        description="Cron schedule for GitHub scraper Dagster job"
    )
    github_top_n: int = Field(
        default=config_yaml.get("GITHUB_TOP_N", 30),
        description="Number of top GitHub repos to fetch per run"
    )

    github_api_url: str = Field(
        default=config_yaml.get("GITHUB_API_URL", ""),
        description="GitHub API URL (required, e.g. https://api.github.com/search/repositories)"
    )

    # GITLAB
    gitlab_token: str = Field(
        default=config_yaml.get("GITLAB_ACCESS_TOKEN", ""),
        description="GitLab API access token"
    )
    gitlab_scraping_query: str = Field(
        default=config_yaml.get("GITLAB_SCRAPING_QUERY", ""),
        description="GitLab scraper parameter query (keyword)"
    )
    gitlab_projects_visibility: str = Field(
        default=config_yaml.get("GITLAB_PROJECTS_VISIBILITY", "public"),
        description="GitLab projects visibility (public/private/internal)"
    )
    gitlab_projects_archived: str = Field(
        default=config_yaml.get("GITLAB_PROJECTS_ARCHIVED", "false"),
        description="GitLab projects archived (true/false)"
    )
    gitlab_projects_order_by: str = Field(
        default=config_yaml.get("GITLAB_PROJECTS_ORDER_BY", "created_at"),
        description="GitLab projects order_by (created_at, updated_at, etc.)"
    )
    gitlab_projects_sort: str = Field(
        default=config_yaml.get("GITLAB_PROJECTS_SORT", "desc"),
        description="GitLab projects sort (asc/desc)"
    )
    gitlab_top_n: int = Field(
        default=config_yaml.get("GITLAB_TOP_N", 30),
        description="Number of top GitLab repos to fetch per run"
    )

    # Path to the techstacks seed file (TypeScript). Used by assets to build allowed tech list.
    techstacks_seed_path: str = Field(
        default=config_yaml.get("TECHSTACKS_SEED_PATH", "/app/prisma/seed/techstacks-data.ts"),
        description="Filesystem path to the techstacks seed file (techstacks-data.ts)",
    )

    # Strategy used by merger asset to combine parallel outputs: intersection|union|prefer_primary
    merge_strategy: str = Field(
        default=config_yaml.get("MERGE_STRATEGY", "intersection"),
        description="Merge strategy for combining parallel asset outputs (intersection|union|prefer_primary)",
    )
