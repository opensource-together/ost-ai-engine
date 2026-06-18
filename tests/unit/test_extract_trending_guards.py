"""Guard-rail tests for GitHub trending scraper asset."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from dagster import build_asset_context

from src.linker.assets.scraper.raw_github__extract_trending import (
    raw_github__extract_trending,
)
from src.linker.resources.cfg_resource import PipelineConfig


class TestRawGithubExtractTrendingGuards:
    def test_runtime_error_when_trending_binary_missing(self) -> None:
        cfg = PipelineConfig(
            db_url="postgresql://u:p@localhost:5432/db",
            github_token="test-token",
            github_scraping_query="",
            go_scraper_path="/bin/scraper",
            go_fetcher_path="/bin/fetcher",
            go_trending_path="/nonexistent/bin/ost-trending",
        )
        context = build_asset_context(resources={"config": cfg})

        with patch.dict("os.environ", {"DATABASE_URL": cfg.db_url}):
            with patch("os.path.exists", return_value=False):
                with pytest.raises(RuntimeError, match="binary not found"):
                    raw_github__extract_trending(context=context)

    def test_runtime_error_when_go_trending_path_unset(self) -> None:
        cfg = PipelineConfig(
            db_url="postgresql://u:p@localhost:5432/db",
            github_token="test-token",
            github_scraping_query="",
            go_scraper_path="/bin/scraper",
            go_fetcher_path="/bin/fetcher",
            go_trending_path="",
        )
        context = build_asset_context(resources={"config": cfg})

        with patch.dict("os.environ", {"DATABASE_URL": cfg.db_url}):
            with pytest.raises(RuntimeError, match="GO_TRENDING_PATH"):
                raw_github__extract_trending(context=context)
