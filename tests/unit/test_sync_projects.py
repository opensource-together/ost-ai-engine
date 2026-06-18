"""Unit tests for public project sync asset."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from dagster import FilesystemIOManager, build_asset_context

from src.linker.assets.sync.core_public__sync_projects import (
    core_public__sync_projects,
)


@pytest.fixture
def sync_context(tmp_path):
    return build_asset_context(
        resources={"io_manager": FilesystemIOManager(base_dir=str(tmp_path))},
    )


class TestCorePublicSyncProjects:
    def test_no_op_when_input_empty(self, sync_context) -> None:
        core_public__sync_projects(
            context=sync_context,
            core_match__classify_projects=[],
        )

    @patch("src.linker.assets.sync.core_public__sync_projects.get_db_cursor")
    def test_syncs_one_project(
        self,
        mock_get_cursor: MagicMock,
        sync_context,
    ) -> None:
        tech_cur = MagicMock()
        tech_cur.fetchall.return_value = [{"id": "ts-1", "name": "Python"}]

        write_cur = MagicMock()
        outer_cm = MagicMock()
        outer_cm.__enter__.return_value = tech_cur
        outer_cm.__exit__.return_value = False

        inner_cm = MagicMock()
        inner_cm.__enter__.return_value = write_cur
        inner_cm.__exit__.return_value = False

        mock_get_cursor.side_effect = [outer_cm, inner_cm]

        data = [
            {
                "project": {
                    "id": "proj-1",
                    "title": "Test Repo",
                    "description": "A test",
                    "url": "https://github.com/org/repo",
                    "created_at": "2024-01-01",
                    "languages": {"Python": 100},
                    "topics": ["ml"],
                },
                "classification": {
                    "categoryId": "cat-1",
                    "domainId": "dom-1",
                    "modelVersion": "v1",
                    "promptVersion": "p1",
                },
            }
        ]

        core_public__sync_projects(
            context=sync_context,
            core_match__classify_projects=data,
        )

        assert write_cur.execute.call_count >= 2
