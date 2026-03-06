import json
from datetime import date, timedelta

import pytest

from src.linker.resources.cfg_resource import (
    EXCLUDED_TERMS,
    STAR_RANGES,
    PipelineConfig,
    build_default_github_queries,
    build_default_github_query,
    build_fetcher_env,
    build_scraper_env,
)


@pytest.mark.unit
class TestBuildDefaultGithubQuery:
    def test_contains_star_range(self):
        query = build_default_github_query()
        assert "stars:300..5000" in query

    def test_contains_good_first_issues(self):
        query = build_default_github_query()
        assert "good-first-issues:>1" in query

    def test_excludes_all_terms(self):
        query = build_default_github_query()
        for term in EXCLUDED_TERMS:
            assert f'NOT "{term}"' in query

    def test_pushed_date_is_seven_days_ago(self):
        query = build_default_github_query()
        expected_date = (date.today() - timedelta(days=7)).isoformat()
        assert f"pushed:>={expected_date}" in query

    def test_contains_archive_and_public_filters(self):
        query = build_default_github_query()
        assert "is:public" in query
        assert "archived:false" in query


@pytest.mark.unit
class TestBuildDefaultGithubQueries:
    def test_returns_one_query_per_star_range(self):
        queries = build_default_github_queries()
        assert len(queries) == len(STAR_RANGES)

    def test_each_query_has_correct_star_range(self):
        queries = build_default_github_queries()
        for query, (low, high) in zip(queries, STAR_RANGES):
            assert f"stars:{low}..{high}" in query

    def test_each_query_excludes_terms(self):
        queries = build_default_github_queries()
        for query in queries:
            for term in EXCLUDED_TERMS:
                assert f'NOT "{term}"' in query

    def test_each_query_has_pushed_date(self):
        queries = build_default_github_queries()
        expected_date = (date.today() - timedelta(days=7)).isoformat()
        for query in queries:
            assert f"pushed:>={expected_date}" in query


def _make_config(**overrides: str) -> PipelineConfig:
    """Build a PipelineConfig with sensible test defaults."""
    defaults = {
        "db_url": "postgresql://u:p@localhost:5432/test",
        "github_token": "ghp_test_token",
        "go_scraper_path": "/usr/local/bin/github-scraper",
        "go_fetcher_path": "/usr/local/bin/ost-fetcher",
    }
    defaults.update(overrides)
    return PipelineConfig(**defaults)


@pytest.mark.unit
class TestBuildScraperEnv:
    def test_includes_database_url(self):
        cfg = _make_config(db_url="postgresql://a:b@host/db")
        env = build_scraper_env(cfg)
        assert env["DATABASE_URL"] == "postgresql://a:b@host/db"

    def test_uses_explicit_query_when_provided(self):
        cfg = _make_config(github_scraping_query="stars:>1000")
        env = build_scraper_env(cfg)
        assert env["GITHUB_SCRAPING_QUERY"] == "stars:>1000"

    def test_falls_back_to_default_query(self):
        """When no explicit query, first query uses first STAR_RANGES entry."""
        cfg = _make_config(github_scraping_query="")
        env = build_scraper_env(cfg)
        low, high = STAR_RANGES[0]
        assert f"stars:{low}..{high}" in env["GITHUB_SCRAPING_QUERY"]

    def test_includes_github_token(self):
        cfg = _make_config(github_token="ghp_abc")
        env = build_scraper_env(cfg)
        assert env["GITHUB_ACCESS_TOKEN"] == "ghp_abc"

    def test_includes_go_paths(self):
        cfg = _make_config(
            go_scraper_path="/bin/scraper",
            go_fetcher_path="/bin/fetcher",
        )
        env = build_scraper_env(cfg)
        assert env["GO_SCRAPER_PATH"] == "/bin/scraper"
        assert env["GO_FETCHER_PATH"] == "/bin/fetcher"

    def test_sets_queries_json_array_when_no_explicit_query(self):
        """GITHUB_SCRAPING_QUERIES is a JSON array with one entry per star range."""
        cfg = _make_config(github_scraping_query="")
        env = build_scraper_env(cfg)
        queries = json.loads(env["GITHUB_SCRAPING_QUERIES"])
        assert isinstance(queries, list)
        assert len(queries) == len(STAR_RANGES)

    def test_sets_single_query_in_array_when_explicit(self):
        """Explicit query is wrapped in a single-element JSON array."""
        cfg = _make_config(github_scraping_query="stars:>5000")
        env = build_scraper_env(cfg)
        queries = json.loads(env["GITHUB_SCRAPING_QUERIES"])
        assert queries == ["stars:>5000"]

    def test_legacy_var_set_for_backward_compat(self):
        """GITHUB_SCRAPING_QUERY is always set to the first query for backward compat."""
        cfg = _make_config(github_scraping_query="")
        env = build_scraper_env(cfg)
        queries = json.loads(env["GITHUB_SCRAPING_QUERIES"])
        assert env["GITHUB_SCRAPING_QUERY"] == queries[0]


@pytest.mark.unit
class TestBuildFetcherEnv:
    def test_includes_database_url(self):
        cfg = _make_config(db_url="postgresql://x:y@h/d")
        env = build_fetcher_env(cfg)
        assert env["DATABASE_URL"] == "postgresql://x:y@h/d"

    def test_includes_github_token(self):
        cfg = _make_config(github_token="ghp_tok")
        env = build_fetcher_env(cfg)
        assert env["GITHUB_ACCESS_TOKEN"] == "ghp_tok"

    def test_returns_exactly_two_keys(self):
        cfg = _make_config()
        env = build_fetcher_env(cfg)
        assert set(env.keys()) == {"DATABASE_URL", "GITHUB_ACCESS_TOKEN"}
