"""
  Application bootstrap settings for the Linker package.

  This module resolves configuration needed before Dagster resources are
  constructed, such as dbt project.
  """

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Directories structure:
# ost-linker/
# ├── src/
# │   ├── linker/
# │   ├── services/
# │   └── ...
# ├── dbt/
# ├── prisma/
# ├── scripts/

ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR / ".env"
DEFAULT_DBT_DIR = ROOT_DIR / "dbt"


class Settings(BaseSettings):
    """Application bootstrap settings resolved before Dagster resources exist."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        extra="ignore",
    )

    dbt_project_dir: Path = DEFAULT_DBT_DIR

    @field_validator("dbt_project_dir")
    @classmethod
    def validate_dbt_project_dir(cls, value: Path) -> Path:
        resolved = value.resolve()

        if not resolved.exists():
            raise ValueError(f"DBT project dir does not exist: {resolved}")

        if not resolved.is_dir():
            raise ValueError(f"DBT project dir is not a directory: {resolved}")

        if not (resolved / "dbt_project.yml").exists():
            raise ValueError(f"Missing dbt_project.yml in: {resolved}")

        return resolved


settings = Settings()
