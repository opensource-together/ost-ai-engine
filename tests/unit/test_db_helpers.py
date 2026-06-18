"""Unit tests for shared psycopg2 helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.services.python.db import get_db_connection, get_db_cursor


class TestGetDbConnection:
    def test_raises_when_database_url_missing(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="DATABASE_URL"):
                with get_db_connection():
                    pass

    @patch("src.services.python.db.psycopg2.connect")
    def test_rolls_back_on_read_only_exit(self, mock_connect: MagicMock) -> None:
        conn = MagicMock()
        mock_connect.return_value = conn

        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://u:p@localhost/db"}):
            with get_db_connection(commit=False):
                pass

        conn.rollback.assert_called_once()
        conn.commit.assert_not_called()
        conn.close.assert_called_once()

    @patch("src.services.python.db.psycopg2.connect")
    def test_commits_when_requested(self, mock_connect: MagicMock) -> None:
        conn = MagicMock()
        mock_connect.return_value = conn

        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://u:p@localhost/db"}):
            with get_db_connection(commit=True):
                pass

        conn.commit.assert_called_once()
        conn.close.assert_called_once()


class TestGetDbCursor:
    @patch("src.services.python.db.psycopg2.connect")
    def test_yields_real_dict_cursor(self, mock_connect: MagicMock) -> None:
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value.__enter__.return_value = cur
        mock_connect.return_value = conn

        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://u:p@localhost/db"}):
            with get_db_cursor() as cursor:
                assert cursor is cur

        conn.rollback.assert_called()
