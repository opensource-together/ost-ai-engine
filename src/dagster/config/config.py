########################################
# CONFIGURATION MODULE - OST AI ENGINE #
########################################
import os
import yaml
from dotenv import load_dotenv
from dagster import Config
from pydantic import Field

load_dotenv()

CONFIG_YAML_PATH = os.getenv("OST_CONFIG_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "config.yaml"))
with open(CONFIG_YAML_PATH, "r") as f:
    config_yaml = yaml.safe_load(f)    
class PipelineConfig(Config):
    """
    Central configuration for the Dagster pipeline.
    All secrets and connection info are loaded from config/config.yaml.
    """
    db_url: str = Field(
        default=config_yaml.get("DATABASE_URL", ""),
        description="Database connection string (e.g. postgresql://user:pass@host:port/dbname)"
    )
    github_token: str = Field(
        default=config_yaml.get("GITHUB_ACCESS_TOKEN", ""),
        description="GitHub API access token"
    )
    gitlab_token: str = Field(
        default=config_yaml.get("GITLAB_ACCESS_TOKEN", ""),
        description="GitLab API access token"
    )
    github_scraping_query: str = Field(
        default=config_yaml.get("GITHUB_SCRAPING_QUERY", ""),
        description="GitHub scraper parameter query"
    )
    github_top_n: int = Field(
        default=config_yaml.get("GITHUB_TOP_N", 30),
        description="Number of top GitHub repos to fetch per run"
    )
