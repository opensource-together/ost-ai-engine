"""Unit tests for Go fetcher topics asset wiring."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from dagster import build_asset_context

from src.linker.assets.scraper.core_github__fetch_repo_topics import (
    core_github__fetch_repo_topics,
)
from src.linker.resources.cfg_resource import PipelineConfig


class TestCoreGithubFetchRepoTopics:
    def test_runtime_error_when_fetcher_binary_missing(self) -> None:
        cfg = PipelineConfig(
            db_url="postgresql://u:p@localhost:5432/db",
            github_token="test-token",
            github_scraping_query="",
            go_scraper_path="/bin/scraper",
            go_fetcher_path="/nonexistent/bin/ost-fetcher",
            go_trending_path="/bin/trending",
        )
        context = build_asset_context(resources={"config": cfg})
        df = pd.DataFrame([{"id": "1"}])

        with patch("os.path.exists", return_value=False):
            with pytest.raises(RuntimeError, match="Go binary not found"):
                core_github__fetch_repo_topics(
                    context=context,
                    core_github__detect_languages=df,
                )

    @patch("src.linker.assets.scraper.core_github__fetch_repo_topics.subprocess.run")
    def test_invokes_fetcher_with_topics_mode(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        cfg = PipelineConfig(
            db_url="postgresql://u:p@localhost:5432/db",
            github_token="test-token",
            github_scraping_query="",
            go_scraper_path="/bin/scraper",
            go_fetcher_path="/bin/ost-fetcher",
            go_trending_path="/bin/trending",
        )
        context = build_asset_context(resources={"config": cfg})
        df = pd.DataFrame([{"id": "1"}])

        with patch("os.path.exists", return_value=True):
            output = core_github__fetch_repo_topics(
                context=context,
                core_github__detect_languages=df,
            )

        cmd = mock_run.call_args[0][0]
        assert cmd == ["/bin/ost-fetcher", "--mode", "topics", "--concurrency", "20"]
        assert output.metadata["status"].value == "completed_via_go"
