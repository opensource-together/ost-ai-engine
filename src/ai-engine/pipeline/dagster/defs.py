from __future__ import annotations

import importlib.util
from pathlib import Path
from dagster import Definitions
import os
from dagster_dbt import DbtCliResource
try:
    # Load .env so env vars exist when Dagster imports this module
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(dotenv_path=Path(__file__).resolve().parents[4] / ".env")
except Exception:
    pass


def _load_module(module_path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, str(module_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {module_name} from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


here = Path(__file__).resolve().parent

# Load asset functions directly from files to avoid package-relative imports
github_mod = _load_module(here / "assets" / "scrapers" / "scraper_go_github.py", "asset_scraper_github")
gitlab_mod = _load_module(here / "assets" / "scrapers" / "scraper_go_gitlab.py", "asset_scraper_gitlab")
dbt_mod = _load_module(here / "assets" / "dbt_transforms.py", "dbt_transforms_mod")

repo_root = Path(os.environ["PROJECT_ROOT"]).resolve()

# Resolve dbt directories from env (no defaults)
dbt_project_dir_env = os.environ["DBT_PROJECT_DIR"]
dbt_profiles_dir_env = os.environ["DBT_PROFILES_DIR"]

def _to_abs(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (repo_root / p)

dbt_project_dir = _to_abs(dbt_project_dir_env)
dbt_profiles_dir = _to_abs(dbt_profiles_dir_env)

defs = Definitions(
    assets=[
        github_mod.scrape_github_projects,
        gitlab_mod.scrape_gitlab_projects,
        dbt_mod.dbt_transforms,
    ],
    resources={
        "dbt": DbtCliResource(
            dbt_executable="/app/.venv/bin/dbt",
            project_dir=str(dbt_project_dir), 
            profiles_dir=str(dbt_profiles_dir)
        ),
    },
)


