"""
Configuration resource for Dagster pipeline.
Consolidates all config into PipelineConfig which reads directly from environment.
"""

import os
from datetime import date, timedelta
from dotenv import load_dotenv
from dagster import resource, Config
from pydantic import Field

load_dotenv()

# Dynamic query building
seven_days_ago = (date.today() - timedelta(days=60)).isoformat()
# Terms to exclude from search results to improve quality
# NOTE: GitHub API has limits on query complexity (max ~5-10 logical operators).
# Keep this list short and focused on high-imact noise.
EXCLUDED_TERMS = [
    "download",
    "list",
    "awesome",
    "collection",
]

DEFAULT_GITHUB_QUERY = " ".join([
    "stars:2500..2503",
    "topics:>0",
    "forks:>0",
    f"pushed:>={seven_days_ago}",
    "is:public",
    "archived:false",
] + [f'NOT "{term}"' for term in EXCLUDED_TERMS])


class PipelineConfig(Config):
    """
    Central configuration for the Dagster pipeline.
    All config is loaded directly from environment variables.
    """

    # Database
    db_url: str = Field(
        default=os.getenv("DATABASE_URL", ""),
        description="Database connection string (e.g. postgresql://user:pass@host:port/dbname)"
    )

    # FastText
    fasttext_model_path: str = Field(
        default=os.getenv("FASTTEXT_MODEL_PATH", ""),
        description="Filesystem path to the FastText lid.176.ftz model",
    )

    # GitHub
    github_token: str = Field(
        default=os.getenv("GITHUB_ACCESS_TOKEN", ""),
        description="GitHub API access token"
    )
    github_scraping_query: str = Field(
        default=os.getenv("GITHUB_SCRAPING_QUERY", DEFAULT_GITHUB_QUERY),
        description="GitHub scraper parameter query"
    )
    github_api_url: str = Field(
        default=os.getenv("GITHUB_API_URL", "https://api.github.com/search/repositories"),
        description="GitHub API URL"
    )

    # Go binary paths
    go_scraper_path: str = Field(
        default=os.getenv("GO_SCRAPER_PATH", ""),
        description="Path to the Go scraper binary (github-scraper)",
    )
    go_fetcher_path: str = Field(
        default=os.getenv("GO_FETCHER_PATH", ""),
        description="Path to the Go fetcher binary (ost-fetcher)",
    )


def build_scraper_env(cfg: PipelineConfig) -> dict:
    """Return environment as config based on PipelineConfig.
    Keep it scoped to only needed keys (no os.environ copy) to avoid leaks.
    """
    env: dict[str, str] = {}
    # GitHub
    if cfg.github_scraping_query:
        env["GITHUB_SCRAPING_QUERY"] = cfg.github_scraping_query
    if cfg.github_token:
        env["GITHUB_ACCESS_TOKEN"] = cfg.github_token
    if cfg.github_api_url:
        env["GITHUB_API_URL"] = cfg.github_api_url
    # Go paths
    if cfg.go_scraper_path:
        env["GO_SCRAPER_PATH"] = cfg.go_scraper_path
    if cfg.go_fetcher_path:
        env["GO_FETCHER_PATH"] = cfg.go_fetcher_path
    return env


@resource
def config_resource():
    """Dagster resource providing a PipelineConfig instance.
    Keeps configuration centralized and injectable into assets/jobs.
    """
    return PipelineConfig()