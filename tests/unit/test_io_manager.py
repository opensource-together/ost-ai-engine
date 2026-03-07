import pytest

from src.linker.resources.io_manager import (
    _ALLOWED_TABLES,
    _VALID_IDENTIFIERS_RE,
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
