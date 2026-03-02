"""
Configuration resource for Dagster pipeline.
Consolidates all config into PipelineConfig which reads directly from environment.
"""

from datetime import date, timedelta

from dagster import ConfigurableResource

# Terms to exclude from search results to filter out non-contributable repos.
# NOTE: GitHub API has limits on query complexity (max ~5-10 NOT operators).
EXCLUDED_TERMS = [
    "awesome",
    "roadmap",
    "cheatsheet",
    "interview",
    "resources",
    "tutorial",
    "course",
    "exercises",
]


def build_default_github_query() -> str:
    """Build GitHub search query with a fresh date each time it is called."""
    seven_days_ago = (date.today() - timedelta(days=7)).isoformat()
    return " ".join(
        [
            "stars:300..5000",
            "good-first-issues:>1",
            "help-wanted-issues:>0",
            "topics:>2",
            "fork:false",
            f"pushed:>={seven_days_ago}",
            "is:public",
            "archived:false",
        ]
        + [f'NOT "{term}"' for term in EXCLUDED_TERMS]
    )


class PipelineConfig(ConfigurableResource):
    """
    Central configuration for the Dagster pipeline.

    Required fields (db_url, github_token, go_scraper_path, go_fetcher_path)
    receive ``EnvVar(...)`` in definitions.py so they are resolved at runtime.
    """

    # Database
    db_url: str
    # GitHub
    github_token: str
    github_scraping_query: str = ""
    github_api_url: str = "https://api.github.com/search/repositories"
    # Go binary paths
    go_scraper_path: str
    go_fetcher_path: str


def build_scraper_env(cfg: PipelineConfig) -> dict[str, str]:
    """Return environment dict for the Go scraper subprocess."""
    env: dict[str, str] = {}
    env["DATABASE_URL"] = cfg.db_url
    # GitHub – fall back to a freshly-computed query when no explicit one is set
    env["GITHUB_SCRAPING_QUERY"] = cfg.github_scraping_query or build_default_github_query()
    if cfg.github_token:
        env["GITHUB_ACCESS_TOKEN"] = cfg.github_token
    if cfg.github_api_url:
        env["GITHUB_API_URL"] = cfg.github_api_url
    if cfg.go_scraper_path:
        env["GO_SCRAPER_PATH"] = cfg.go_scraper_path
    if cfg.go_fetcher_path:
        env["GO_FETCHER_PATH"] = cfg.go_fetcher_path
    return env


def build_fetcher_env(cfg: PipelineConfig) -> dict[str, str]:
    """Return environment dict for the Go fetcher subprocess."""
    return {
        "DATABASE_URL": cfg.db_url,
        "GITHUB_ACCESS_TOKEN": cfg.github_token,
    }
