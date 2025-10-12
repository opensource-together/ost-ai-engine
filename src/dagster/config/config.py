########################################
# CONFIGURATION MODULE - OST AI ENGINE #
########################################

import os
from dotenv import load_dotenv

from dagster import Config
from pydantic import Field
from datetime import date

# Load environment variables from .env.local file
load_dotenv(dotenv_path=".env.local")

today = date.today().isoformat()

class PipelineConfig(Config):
    """
    Central configuration for the Dagster pipeline.
    All secrets and connection info are loaded from environment variables.
    """
    db_url: str = Field(
        default_factory=lambda: os.getenv("DATABASE_URL", ""),
        description="Database connection string (e.g. postgresql://user:pass@host:port/dbname)"
    )
    github_token: str = Field(
        default_factory=lambda: os.getenv("GITHUB_ACCESS_TOKEN", ""),
        description="GitHub API access token"
    )
    gitlab_token: str = Field(
        default_factory=lambda: os.getenv("GITLAB_ACCESS_TOKEN", ""),
        description="GitLab API access token"
    )
    github_scraping_query: str = Field(
        default=f"stars:>100 stars:<500 pushed:>={today} is:public archived:false",
        description="`GitHub scraper parameter query"
    )