"""Unit tests for SQLAlchemy row mapping helpers."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import UUID

from src.api.row_mapping import mapping_row_first, mapping_rows


class TestRowMapping:
    def test_mapping_rows_converts_uuid_values_to_strings(self) -> None:
        uid = UUID("550e8400-e29b-41d4-a716-446655440000")
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = [{"id": uid, "name": "x"}]

        rows = mapping_rows(mock_result)

        assert rows == [{"id": "550e8400-e29b-41d4-a716-446655440000", "name": "x"}]

    def test_mapping_row_first_converts_uuid_values_to_strings(self) -> None:
        uid = UUID("550e8400-e29b-41d4-a716-446655440000")
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {"id": uid}

        row = mapping_row_first(mock_result)

        assert row == {"id": "550e8400-e29b-41d4-a716-446655440000"}

    def test_mapping_row_first_returns_none_when_empty(self) -> None:
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None

        assert mapping_row_first(mock_result) is None
