import os
from dagster import resource
from src.pipeline.utils import PipelineConfig


def build_scraper_env(cfg: PipelineConfig) -> dict:
    """Return a minimal env dict for Go scrapers based on PipelineConfig.
    Keep it scoped to only needed keys (no os.environ copy) to avoid leaks.
    """
    env: dict[str, str] = {}
    # GitHub
    if getattr(cfg, "github_scraping_query", None):
        env["GITHUB_SCRAPING_QUERY"] = str(cfg.github_scraping_query)
    if getattr(cfg, "github_token", None):
        env["GITHUB_ACCESS_TOKEN"] = str(cfg.github_token)
    if getattr(cfg, "github_api_url", None):
        env["GITHUB_API_URL"] = str(cfg.github_api_url)
    # Config
    env["OST_CONFIG_PATH"] = os.getenv("OST_CONFIG_PATH", "")
    return env


@resource
def config_resource():
    """Dagster resource providing a PipelineConfig instance.
    Keeps configuration centralized and injectable into assets/jobs.
    """
    return PipelineConfig()