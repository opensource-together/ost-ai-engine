from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.linker.resources.io_manager import (
    _ALLOWED_TABLES,
    _VALID_IDENTIFIERS_RE,
    PandasPostgresIOManager,
    _iter_chunks,
    _validate_identifier,
)


class TestValidIdentifiersRegex:
    def test_accepts_lowercase_alpha(self) -> None:
        assert _VALID_IDENTIFIERS_RE.match("github")

    def test_accepts_underscore_prefix(self) -> None:
        assert _VALID_IDENTIFIERS_RE.match("_private")

    def test_accepts_alphanumeric_with_underscore(self) -> None:
        assert _VALID_IDENTIFIERS_RE.match("stg_github__project")

    def test_rejects_leading_digit(self) -> None:
        assert _VALID_IDENTIFIERS_RE.match("1table") is None

    def test_rejects_empty_string(self) -> None:
        assert _VALID_IDENTIFIERS_RE.match("") is None

    def test_rejects_special_chars(self) -> None:
        assert _VALID_IDENTIFIERS_RE.match("my-table") is None


class TestValidateIdentifier:
    def test_all_allowed_tables_pass(self) -> None:
        for schema, table in _ALLOWED_TABLES:
            _validate_identifier(schema, table)

    def test_sql_injection_in_schema_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid schema name"):
            _validate_identifier('github"; DROP TABLE', "Project")

    def test_sql_injection_in_table_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid table name"):
            _validate_identifier("public", 'Project"; DROP TABLE')

    def test_valid_format_but_not_allowlisted(self) -> None:
        with pytest.raises(ValueError, match="not in the IO manager allowlist"):
            _validate_identifier("github", "fake_table")

    def test_empty_schema_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid schema name"):
            _validate_identifier("", "Project")

    def test_empty_table_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid table name"):
            _validate_identifier("public", "")

    def test_dash_in_schema_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid schema name"):
            _validate_identifier("my-schema", "Project")


class TestDbtAllowlistSync:
    """Ensures every dbt model's (schema, model_name) is in _ALLOWED_TABLES."""

    @staticmethod
    def _parse_dbt_models() -> set[tuple[str, str]]:
        from pathlib import Path

        import yaml

        dbt_project = Path(__file__).resolve().parents[2] / "dbt" / "dbt_project.yml"
        with open(dbt_project) as f:
            config = yaml.safe_load(f)

        pairs: set[tuple[str, str]] = set()
        layers = config.get("models", {}).get("ost_linker", {})
        for layer_config in layers.values():
            if not isinstance(layer_config, dict):
                continue
            for model_name, model_config in layer_config.items():
                if model_name.startswith("+") or not isinstance(model_config, dict):
                    continue
                schema = model_config.get("+schema")
                if schema:
                    pairs.add((schema, model_name))
        return pairs

    def test_every_dbt_model_in_allowlist(self) -> None:
        """Catches allowlist drift — the exact bug found during pipeline smoke test."""
        dbt_pairs = self._parse_dbt_models()
        assert dbt_pairs, "No dbt models parsed — check dbt_project.yml structure"
        missing = dbt_pairs - _ALLOWED_TABLES
        assert not missing, (
            f"dbt models missing from IO manager _ALLOWED_TABLES: {missing}. "
            f"Add them to io_manager.py."
        )


class TestIterChunks:
    def test_dataframe_yields_once(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3]})
        chunks = list(_iter_chunks(df))
        assert len(chunks) == 1
        assert chunks[0].equals(df)

    def test_iterator_passthrough(self) -> None:
        a = pd.DataFrame({"x": [1]})
        b = pd.DataFrame({"x": [2, 3]})
        chunks = list(_iter_chunks(iter([a, b])))
        assert len(chunks) == 2
        assert chunks[0].equals(a)
        assert chunks[1].equals(b)

    def test_generator_passthrough(self) -> None:
        def gen():
            yield pd.DataFrame({"x": [1]})
            yield pd.DataFrame({"x": [2]})

        chunks = list(_iter_chunks(gen()))
        assert len(chunks) == 2


class TestChunkSizeConfig:
    def test_defaults_to_none(self) -> None:
        mgr = PandasPostgresIOManager(db_url="postgresql://fake/db")
        assert mgr.chunk_size is None

    def test_configurable(self) -> None:
        mgr = PandasPostgresIOManager(db_url="postgresql://fake/db", chunk_size=500)
        assert mgr.chunk_size == 500


class TestHandleOutputStreaming:
    """Verify chunked writes use to_sql once per chunk and truncate once upfront."""

    def _fake_context(self, schema: str, table: str) -> MagicMock:
        ctx = MagicMock()
        ctx.asset_key.path = [schema, table]
        return ctx

    def test_writes_each_chunk_separately(self) -> None:
        mgr = PandasPostgresIOManager(db_url="postgresql://fake/db", chunk_size=100)
        fake_engine = MagicMock()
        with patch.object(
            PandasPostgresIOManager, "engine", new_callable=lambda: fake_engine
        ):
            chunks = [
                pd.DataFrame({"id": [1, 2]}),
                pd.DataFrame({"id": [3, 4, 5]}),
            ]
            with patch("pandas.DataFrame.to_sql") as to_sql_mock:
                mgr.handle_output(self._fake_context("public", "Project"), iter(chunks))

            assert to_sql_mock.call_count == 2
            # Truncate should have been issued exactly once, before any write.
            fake_engine.begin.assert_called_once()

    def test_dataframe_still_works(self) -> None:
        """Backward compat: plain DataFrame input still goes through a single write."""
        mgr = PandasPostgresIOManager(db_url="postgresql://fake/db")
        fake_engine = MagicMock()
        with (
            patch.object(
                PandasPostgresIOManager, "engine", new_callable=lambda: fake_engine
            ),
            patch("pandas.DataFrame.to_sql") as to_sql_mock,
        ):
            mgr.handle_output(
                self._fake_context("public", "Project"),
                pd.DataFrame({"id": [1, 2, 3]}),
            )
        assert to_sql_mock.call_count == 1

    def test_none_is_noop(self) -> None:
        mgr = PandasPostgresIOManager(db_url="postgresql://fake/db")
        fake_engine = MagicMock()
        with (
            patch.object(
                PandasPostgresIOManager, "engine", new_callable=lambda: fake_engine
            ),
            patch("pandas.DataFrame.to_sql") as to_sql_mock,
        ):
            mgr.handle_output(self._fake_context("public", "Project"), None)
        to_sql_mock.assert_not_called()
        fake_engine.begin.assert_not_called()

    def test_empty_chunks_skipped(self) -> None:
        mgr = PandasPostgresIOManager(db_url="postgresql://fake/db", chunk_size=100)
        fake_engine = MagicMock()
        with patch.object(
            PandasPostgresIOManager, "engine", new_callable=lambda: fake_engine
        ):
            chunks = [
                pd.DataFrame({"id": [1, 2]}),
                pd.DataFrame({"id": pd.Series([], dtype="int64")}),
                pd.DataFrame({"id": [3]}),
            ]
            with patch("pandas.DataFrame.to_sql") as to_sql_mock:
                mgr.handle_output(self._fake_context("public", "Project"), iter(chunks))
            assert to_sql_mock.call_count == 2


class TestLoadInputStreaming:
    def _fake_context(self, schema: str, table: str) -> MagicMock:
        ctx = MagicMock()
        ctx.asset_key.path = [schema, table]
        return ctx

    def test_chunk_size_passes_through_to_read_sql(self) -> None:
        mgr = PandasPostgresIOManager(db_url="postgresql://fake/db", chunk_size=500)
        fake_engine = MagicMock()
        with (
            patch.object(
                PandasPostgresIOManager, "engine", new_callable=lambda: fake_engine
            ),
            patch("pandas.read_sql") as read_sql_mock,
        ):
            read_sql_mock.return_value = iter([pd.DataFrame({"a": [1]})])
            mgr.load_input(self._fake_context("public", "Project"))
            _, kwargs = read_sql_mock.call_args
            assert kwargs.get("chunksize") == 500

    def test_no_chunk_size_loads_full_dataframe(self) -> None:
        mgr = PandasPostgresIOManager(db_url="postgresql://fake/db")
        fake_engine = MagicMock()
        with (
            patch.object(
                PandasPostgresIOManager, "engine", new_callable=lambda: fake_engine
            ),
            patch("pandas.read_sql") as read_sql_mock,
        ):
            read_sql_mock.return_value = pd.DataFrame({"a": [1]})
            mgr.load_input(self._fake_context("public", "Project"))
            _, kwargs = read_sql_mock.call_args
            assert "chunksize" not in kwargs or kwargs["chunksize"] is None
