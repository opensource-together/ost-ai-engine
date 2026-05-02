"""Guard-rail smoke tests for raw GitHub project scraper asset (audit FINDING-002)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from dagster import build_asset_context

from src.linker.assets.scraper.raw_github__extract_projects import (
    raw_github__extract_projects,
)
from src.linker.resources.cfg_resource import PipelineConfig


class TestRawGithubExtractProjectsGuards:
    def test_runtime_error_when_scraper_missing(self) -> None:
        cfg = PipelineConfig(
            db_url="postgresql://u:p@localhost:5432/db",
            github_token="test-token",
            github_scraping_query="",
            go_scraper_path="/nonexistent/bin/ost-scraper",
            go_fetcher_path="/nonexistent/bin/ost-fetcher",
            go_trending_path="/nonexistent/bin/ost-trending",
        )

        context = build_asset_context(resources={"config": cfg})

        with patch("os.path.exists", return_value=False):
            with pytest.raises(RuntimeError, match="binary not found"):
                raw_github__extract_projects(context=context)
