"""
Configuration resource for Dagster pipeline.
Consolidates all config into PipelineConfig which reads directly from environment.
"""

import json
from datetime import date, timedelta

from dagster import ConfigurableResource

# Terms to exclude from search results to filter out non-contributable repos.
# NOTE: GitHub Search API rejects queries with more than ~5 NOT operators.
EXCLUDED_TERMS = [
    "awesome",
    "roadmap",
    "cheatsheet",
    "interview",
]

# Star ranges for parallel multi-query scraping.
# Each range becomes a separate GitHub search query, running concurrently.
STAR_RANGES: list[tuple[int, int]] = [(300, 1000), (1000, 3000), (3000, 5000)]


def _build_github_query(star_range: tuple[int, int]) -> str:
    """Build a single GitHub search query for the given star range."""
    seven_days_ago = (date.today() - timedelta(days=7)).isoformat()
    return " ".join(
        [
            f"stars:{star_range[0]}..{star_range[1]}",
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


def build_default_github_query() -> str:
    """Build GitHub search query with a fresh date each time it is called.

    Backward-compatible: returns a single query covering the full 300..5000 range.
    """
    return _build_github_query((300, 5000))


def build_default_github_queries() -> list[str]:
    """Build one GitHub search query per star range for parallel scraping."""
    return [_build_github_query(r) for r in STAR_RANGES]


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
    go_trending_path: str = ""


def build_scraper_env(cfg: PipelineConfig) -> dict[str, str]:
    """Return environment dict for the Go scraper subprocess."""
    env: dict[str, str] = {}
    env["DATABASE_URL"] = cfg.db_url

    # Build queries list: explicit single query wrapped in array, or default multi-range
    if cfg.github_scraping_query:
        queries = [cfg.github_scraping_query]
    else:
        queries = build_default_github_queries()

    env["GITHUB_SCRAPING_QUERIES"] = json.dumps(queries)
    # Backward compat: legacy single-query var (first query in the list)
    env["GITHUB_SCRAPING_QUERY"] = queries[0]

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


def build_trending_env(cfg: PipelineConfig) -> dict[str, str]:
    """Return environment dict for the Go trending scraper subprocess."""
    env: dict[str, str] = {"DATABASE_URL": cfg.db_url}
    if cfg.github_token:
        env["GITHUB_ACCESS_TOKEN"] = cfg.github_token
    return env
