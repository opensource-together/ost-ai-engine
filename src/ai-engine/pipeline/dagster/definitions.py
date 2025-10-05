from __future__ import annotations

import os
from pathlib import Path

from dagster import Definitions

try:
    # Load .env so env vars exist when Dagster imports this module
    from dotenv import load_dotenv  # type: ignore

    load_dotenv(dotenv_path=Path(__file__).resolve().parents[4] / ".env")
except Exception:
    pass


repo_root = Path(os.environ.get("PROJECT_ROOT", Path(__file__).resolve().parents[4])).resolve()


# Import assets from the same directory
import sys
from pathlib import Path
assets_file = Path(__file__).parent / "assets.py"
spec = __import__("importlib.util").util.spec_from_file_location("assets", assets_file)
assets_module = __import__("importlib.util").util.module_from_spec(spec)
spec.loader.exec_module(assets_module)

scrape_github_projects = assets_module.scrape_github_projects
scrape_gitlab_projects = assets_module.scrape_gitlab_projects


defs = Definitions(
    assets=[
        scrape_github_projects,
        scrape_gitlab_projects,
    ],
)


