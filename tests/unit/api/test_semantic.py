"""Unit tests for semantic search service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.api.semantic import SemanticSearchService


class TestSemanticSearchService:
    @patch("src.api.semantic.SentenceTransformer")
    def test_encode_returns_list(self, mock_st: MagicMock) -> None:
        model = MagicMock()
        encoded = MagicMock()
        encoded.tolist.return_value = [0.1, 0.2, 0.3]
        model.encode.return_value = encoded
        mock_st.return_value = model

        service = SemanticSearchService()
        vector = service.encode("hello world")

        assert vector == [0.1, 0.2, 0.3]
        model.encode.assert_called_once_with("hello world", normalize_embeddings=True)

    @patch("src.api.semantic.SentenceTransformer")
    def test_load_is_idempotent(self, mock_st: MagicMock) -> None:
        service = SemanticSearchService()
        service.load()
        service.load()
        mock_st.assert_called_once()
