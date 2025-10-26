import os
from dagster import resource
from src.services.python.load_cfg import PipelineConfig


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
    # GitLab
    if getattr(cfg, "gitlab_scraping_query", None):
        env["GITLAB_SCRAPING_QUERY"] = str(cfg.gitlab_scraping_query)
    if getattr(cfg, "gitlab_token", None):
        env["GITLAB_ACCESS_TOKEN"] = str(cfg.gitlab_token)
    env["GITLAB_PROJECTS_VISIBILITY"] = str(getattr(cfg, "gitlab_projects_visibility", "public"))
    env["GITLAB_PROJECTS_ARCHIVED"] = str(getattr(cfg, "gitlab_projects_archived", "false")).lower()
    env["GITLAB_PROJECTS_ORDER_BY"] = str(getattr(cfg, "gitlab_projects_order_by", "created_at"))
    env["GITLAB_PROJECTS_SORT"] = str(getattr(cfg, "gitlab_projects_sort", "desc"))
    env["OST_CONFIG_PATH"] = os.getenv("OST_CONFIG_PATH", "")
    return env


@resource
def config_resource():
    """Dagster resource providing a PipelineConfig instance.
    Keeps configuration centralized and injectable into assets/jobs.
    """
    return PipelineConfig()