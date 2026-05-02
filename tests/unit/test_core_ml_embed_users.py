"""Regression tests for user embedding Dagster asset (audit FINDING-005)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from dagster import FilesystemIOManager, Output, build_asset_context

from src.linker.assets.embedding.core_ml__embed_users import core_ml__embed_users


@pytest.fixture
def sample_user_df() -> pd.DataFrame:
    return pd.DataFrame(
        [{"user_id": "u1", "user_context": "Alice contributes to Rust parsers"}]
    )


class TestCoreMlEmbedUsers:
    def test_empty_user_df_returns_zero_count(self, tmp_path) -> None:
        model = MagicMock()
        context = build_asset_context(
            resources={
                "sentence_transformer": model,
                "io_manager": FilesystemIOManager(base_dir=str(tmp_path)),
            },
        )
        empty = pd.DataFrame(columns=["user_id", "user_context"])

        output = core_ml__embed_users(context=context, user_df=empty)

        assert isinstance(output, Output)
        assert output.metadata["count"].value == 0
        model.encode_batch.assert_not_called()

    @patch(
        "src.linker.assets.embedding.core_ml__embed_users.get_db_cursor",
    )
    def test_writes_one_row_via_cursor(
        self,
        mock_get_cursor: MagicMock,
        sample_user_df: pd.DataFrame,
        tmp_path,
    ) -> None:
        fake_cur = MagicMock()
        cursor_cm = MagicMock()
        cursor_cm.__enter__.return_value = fake_cur
        cursor_cm.__exit__.return_value = False
        mock_get_cursor.return_value = cursor_cm

        model = MagicMock()
        model.encode_batch.return_value = [[[0.1, 0.2, 0.3]]]

        context = build_asset_context(
            resources={
                "sentence_transformer": model,
                "io_manager": FilesystemIOManager(base_dir=str(tmp_path)),
            },
        )

        output = core_ml__embed_users(context=context, user_df=sample_user_df)

        model.encode_batch.assert_called_once_with(
            ["Alice contributes to Rust parsers"]
        )
        fake_cur.execute.assert_called_once()
        assert output.metadata["count"].value == 1
