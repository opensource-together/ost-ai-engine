"""Embedding asset consumes the streaming io_manager.

Pins two things:

1. The asset declares `streaming_io_manager` as its input manager, so the
   embedding candidate table is streamed chunk-by-chunk instead of being
   materialized in memory.
2. The streaming logic (`_embed_stream`) iterates over chunks rather than
   taking a single DataFrame — pass an iterator of DataFrames and confirm
   every row is embedded + upserted.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd

from src.linker.assets.embedding.core_ml__embed_projects import (
    _embed_stream,
    core_ml__embed_projects,
)


class TestInputManagerBinding:
    def test_projects_df_uses_streaming_io_manager(self) -> None:
        """The AssetIn for projects_df must point to streaming_io_manager."""
        input_defs = core_ml__embed_projects.op.ins
        assert "projects_df" in input_defs
        assert input_defs["projects_df"].input_manager_key == "streaming_io_manager"


class TestStreamingEmbed:
    @staticmethod
    def _make_engine() -> tuple[MagicMock, MagicMock]:
        conn = MagicMock()
        conn.__enter__ = MagicMock(return_value=conn)
        conn.__exit__ = MagicMock(return_value=False)
        conn.begin.return_value.__enter__ = MagicMock(return_value=None)
        conn.begin.return_value.__exit__ = MagicMock(return_value=False)

        engine = MagicMock()
        engine.connect.return_value = conn
        return engine, conn

    def test_iterates_all_chunks_and_upserts_each_row(self) -> None:
        chunks = [
            pd.DataFrame(
                {
                    "project_id": ["p1", "p2"],
                    "rich_context_string": ["ctx1", "ctx2"],
                }
            ),
            pd.DataFrame(
                {
                    "project_id": ["p3"],
                    "rich_context_string": ["ctx3"],
                }
            ),
        ]
        encoder = MagicMock()
        encoder.encode_batch.side_effect = [
            [[0.1, 0.2], [0.3, 0.4]],
            [[0.5, 0.6]],
        ]
        engine, conn = self._make_engine()
        log = MagicMock()

        total = _embed_stream(iter(chunks), encoder, engine, log)

        assert total == 3
        assert encoder.encode_batch.call_count == 2
        assert conn.execute.call_count == 3

    def test_empty_iterator_is_noop(self) -> None:
        encoder = MagicMock()
        engine, _ = self._make_engine()
        log = MagicMock()

        total = _embed_stream(iter([]), encoder, engine, log)

        assert total == 0
        encoder.encode_batch.assert_not_called()
        engine.connect.assert_not_called()

    def test_chunk_with_only_empty_contexts_skipped(self) -> None:
        """Rows with falsy rich_context_string must not hit the embedder."""
        chunks = [
            pd.DataFrame(
                {
                    "project_id": ["p1", "p2"],
                    "rich_context_string": ["", None],
                }
            ),
            pd.DataFrame(
                {
                    "project_id": ["p3"],
                    "rich_context_string": ["ctx3"],
                }
            ),
        ]
        encoder = MagicMock()
        encoder.encode_batch.side_effect = [[[0.5, 0.6]]]
        engine, conn = self._make_engine()
        log = MagicMock()

        total = _embed_stream(iter(chunks), encoder, engine, log)

        assert total == 1
        assert encoder.encode_batch.call_count == 1
        assert conn.execute.call_count == 1

    def test_empty_dataframe_chunk_skipped(self) -> None:
        chunks = [
            pd.DataFrame({"project_id": [], "rich_context_string": []}),
            pd.DataFrame({"project_id": ["p1"], "rich_context_string": ["ctx1"]}),
        ]
        encoder = MagicMock()
        encoder.encode_batch.side_effect = [[[0.1, 0.2]]]
        engine, conn = self._make_engine()
        log = MagicMock()

        total = _embed_stream(iter(chunks), encoder, engine, log)

        assert total == 1
        assert encoder.encode_batch.call_count == 1
