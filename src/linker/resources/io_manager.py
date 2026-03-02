import pandas as pd
from pydantic import PrivateAttr
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from dagster import ConfigurableIOManager, InputContext, OutputContext


class PandasPostgresIOManager(ConfigurableIOManager):
    db_url: str

    _engine: Engine | None = PrivateAttr(default=None)

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            self._engine = create_engine(self.db_url)
        return self._engine

    def handle_output(self, context: OutputContext, obj: pd.DataFrame) -> None:
        if obj is None:
            context.log.info("Skipping output write because obj is None")
            return

        # Map AssetKey to Schema/Table
        if len(context.asset_key.path) > 1:
            schema, table = context.asset_key.path[-2], context.asset_key.path[-1]
        else:
            schema = "public"
            table = context.asset_key.path[-1]

        context.log.info(f"Writing dataframe to {schema}.{table}")
        obj.to_sql(table, self.engine, schema=schema, if_exists="replace", index=False)

    def load_input(self, context: InputContext) -> pd.DataFrame:
        # Map AssetKey to Schema/Table
        if len(context.asset_key.path) > 1:
            schema = context.asset_key.path[-2]
            table = context.asset_key.path[-1]
            full_table_name = f'"{schema}"."{table}"'
        else:
            full_table_name = f'"{context.asset_key.path[-1]}"'

        context.log.info(f"Loading input from {full_table_name}")
        query = f"SELECT * FROM {full_table_name}"
        return pd.read_sql(query, self.engine)
