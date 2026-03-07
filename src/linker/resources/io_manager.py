import re

import pandas as pd
from dagster import ConfigurableIOManager, InputContext, OutputContext
from pydantic import PrivateAttr
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Allowlist of valid schema.table pairs that the IO manager may read/write.
# Any identifier not matching this set will be rejected to prevent SQL injection.
_VALID_IDENTIFIERS_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

_ALLOWED_TABLES: set[tuple[str, str]] = {
    # ingestion / dbt staging (github schema)
    ("github", "stg_github__project"),
    ("github", "stg_github__readme"),
    ("github", "stg_github__languages"),
    ("github", "stg_github__topics"),
    ("github", "stg_github__detection"),
    ("github", "stg_public__category"),
    ("github", "stg_public__domain"),
    # dbt staging (ml schema)
    ("ml", "stg_public__user"),
    ("ml", "stg_public__project"),
    # dbt intermediate (github schema)
    ("github", "int_project_enriched"),
    ("github", "int_github_detection"),
    # dbt intermediate (ml schema)
    ("ml", "int_user_enriched"),
    ("ml", "int_project_contextualized"),
    ("ml", "int_project_embedding_candidate"),
    # dbt marts / facts
    ("github", "fct_github_project"),
    ("ml", "fct_public_user"),
    # match (public schema per dbt config)
    ("public", "match_global_recommendation"),
    ("public", "match_user_recommendation"),
    ("match", "match_global_recommendation"),
    ("match", "match_user_recommendation"),
    ("match", "project_classification"),
    # ml
    ("ml", "EmbdGithubProject"),
    ("ml", "EmbdUser"),
    # public
    ("public", "Project"),
    ("public", "User"),
    ("public", "Category"),
    ("public", "Domain"),
    ("public", "tech_stack"),
}


def _validate_identifier(schema: str, table: str) -> None:
    """Validate that schema and table names are safe identifiers on the allowlist."""
    if not _VALID_IDENTIFIERS_RE.match(schema):
        raise ValueError(f"Invalid schema name: {schema!r}")
    if not _VALID_IDENTIFIERS_RE.match(table):
        raise ValueError(f"Invalid table name: {table!r}")
    if (schema, table) not in _ALLOWED_TABLES:
        raise ValueError(
            f"Table {schema}.{table} is not in the IO manager allowlist. "
            "Add it to _ALLOWED_TABLES in io_manager.py if this is intentional."
        )


class PandasPostgresIOManager(ConfigurableIOManager):
    db_url: str

    _engine: Engine | None = PrivateAttr(default=None)

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            self._engine = create_engine(self.db_url)
        return self._engine

    def handle_output(self, context: OutputContext, obj: pd.DataFrame | None) -> None:
        if obj is None:
            context.log.info("Skipping output write because obj is None")
            return

        # Map AssetKey to Schema/Table
        if len(context.asset_key.path) > 1:
            schema, table = context.asset_key.path[-2], context.asset_key.path[-1]
        else:
            schema = "public"
            table = context.asset_key.path[-1]

        _validate_identifier(schema, table)

        context.log.info(f"Writing dataframe to {schema}.{table}")

        # Truncate-then-append instead of replace (which drops the table)
        with self.engine.begin() as conn:
            conn.execute(text(f'TRUNCATE TABLE "{schema}"."{table}"'))
        obj.to_sql(table, self.engine, schema=schema, if_exists="append", index=False)

    def load_input(self, context: InputContext) -> pd.DataFrame:
        # Map AssetKey to Schema/Table
        if len(context.asset_key.path) > 1:
            schema = context.asset_key.path[-2]
            table = context.asset_key.path[-1]
        else:
            schema = "public"
            table = context.asset_key.path[-1]

        _validate_identifier(schema, table)

        full_table_name = f'"{schema}"."{table}"'
        context.log.info(f"Loading input from {full_table_name}")
        query = f"SELECT * FROM {full_table_name}"
        return pd.read_sql(query, self.engine)
