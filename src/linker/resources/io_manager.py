import re
from collections.abc import Iterable, Iterator

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


def _resolve_schema_table(asset_key_path: list[str]) -> tuple[str, str]:
    if len(asset_key_path) > 1:
        return asset_key_path[-2], asset_key_path[-1]
    return "public", asset_key_path[-1]


class PandasPostgresIOManager(ConfigurableIOManager):
    """Pass pandas DataFrames between assets via Postgres.

    When `chunk_size` is None (default) the manager loads and writes full
    DataFrames — backward-compatible with assets typed as `pd.DataFrame`.

    When `chunk_size` is set, `load_input` returns an `Iterator[pd.DataFrame]`
    (server-side cursor via `pandas.read_sql(..., chunksize=N)`) and
    `handle_output` accepts either a DataFrame or any iterable of DataFrames,
    writing chunk-by-chunk. Downstream assets that opt in must type their
    input as `Iterator[pd.DataFrame]` and iterate over it.
    """

    db_url: str
    chunk_size: int | None = None

    _engine: Engine | None = PrivateAttr(default=None)

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            self._engine = create_engine(self.db_url)
        return self._engine

    def handle_output(
        self,
        context: OutputContext,
        obj: pd.DataFrame | Iterable[pd.DataFrame] | None,
    ) -> None:
        if obj is None:
            context.log.info("Skipping output write because obj is None")
            return

        schema, table = _resolve_schema_table(list(context.asset_key.path))
        _validate_identifier(schema, table)

        context.log.info(f"Writing dataframe to {schema}.{table}")

        # Truncate-then-append: truncate once, then append each chunk.
        with self.engine.begin() as conn:
            conn.execute(text(f'TRUNCATE TABLE "{schema}"."{table}"'))

        written_rows = 0
        for chunk_idx, chunk in enumerate(_iter_chunks(obj)):
            if chunk is None or chunk.empty:
                continue
            chunk.to_sql(
                table,
                self.engine,
                schema=schema,
                if_exists="append",
                index=False,
                chunksize=self.chunk_size,
                method="multi" if self.chunk_size else None,
            )
            written_rows += len(chunk)
            if self.chunk_size:
                context.log.debug(
                    f"Wrote chunk {chunk_idx} ({len(chunk)} rows) to {schema}.{table}"
                )

        context.log.info(f"Wrote {written_rows} rows to {schema}.{table}")

    def load_input(
        self, context: InputContext
    ) -> pd.DataFrame | Iterator[pd.DataFrame]:
        schema, table = _resolve_schema_table(list(context.asset_key.path))
        _validate_identifier(schema, table)

        full_table_name = f'"{schema}"."{table}"'
        query = f"SELECT * FROM {full_table_name}"

        if self.chunk_size:
            context.log.info(
                f"Streaming input from {full_table_name} (chunk_size={self.chunk_size})"
            )
            return pd.read_sql(query, self.engine, chunksize=self.chunk_size)

        context.log.info(f"Loading input from {full_table_name}")
        return pd.read_sql(query, self.engine)


def _iter_chunks(
    obj: pd.DataFrame | Iterable[pd.DataFrame],
) -> Iterator[pd.DataFrame]:
    """Normalize input to an iterator of DataFrames."""
    if isinstance(obj, pd.DataFrame):
        yield obj
        return
    yield from obj
