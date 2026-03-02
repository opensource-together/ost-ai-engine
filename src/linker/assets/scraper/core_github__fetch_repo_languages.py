import typing as _t
import os
import subprocess
from dagster import (
    asset,
    AssetIn,
    AssetKey,
    MetadataValue,
    Output,
)
from .utils import (
    _extract_owner_repo,
    _fetch_repo_languages,
    _make_serializable,
)
from src.services.python.db import get_db_cursor
import json

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

import pandas as pd

@asset(
    kinds={"go", "postgres"},
    owners=DEFAULT_OWNERS,
    # Depends on detection (to filter languages)
    ins={"core_github__detect_languages": AssetIn(key=AssetKey(["github", "int_github_detection"]))},
    group_name="ingestion",
    key=AssetKey(["github", "raw_github_languages"]), # Matches dbt source
    required_resource_keys={"config"},
)
def core_github__fetch_repo_languages(context, core_github__detect_languages: pd.DataFrame):
    """
    Fetch GitHub /languages for each project using Go fetcher.

    **Description:**
    Triggers the external Go binary (`ost-fetcher`) to retrieve language breakdown
    from GitHub API and upsert them directly into PostgreSQL.

    **Logic:**
    1. **Execution**: Calls `ost-fetcher --mode languages`.
    2. **Concurrency**: the Go binary handles massive concurrency.
    3. **Output**: Returns status metadata, data is written to DB.
    """
    context.log.info("core_github__fetch_repo_languages: Starting Go fetcher...")
    
    # Path to the compiled Go binary from config
    cfg = context.resources.config
    fetcher_bin = cfg.go_fetcher_path
    
    if not fetcher_bin:
        raise RuntimeError("GO_FETCHER_PATH not configured in cfg.yaml")
    
    if not os.path.exists(fetcher_bin):
        raise RuntimeError(f"Go binary not found at {fetcher_bin}. Please run 'go build -o ost-fetcher .' in src/services/go/fetcher/")

    env = os.environ.copy()
    db_url = env.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL is required for Go fetcher")
        
    cmd = [fetcher_bin, "--mode", "languages", "--concurrency", "20"]

    context.log.info(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        context.log.info(f"Go fetcher stdout:\n{result.stdout}")
        if result.stderr:
            context.log.warning(f"Go fetcher stderr:\n{result.stderr}")
            
    except subprocess.CalledProcessError as e:
        context.log.error(f"Go fetcher failed with code {e.returncode}")
        context.log.error(f"Stdout: {e.stdout}")
        context.log.error(f"Stderr: {e.stderr}")
        raise RuntimeError("Go fetcher execution failed") from e

    return Output(value=None, metadata={"status": "completed_via_go"})
