from dagster import Definitions
from .assets import hello_asset

defs = Definitions(assets=[hello_asset])
