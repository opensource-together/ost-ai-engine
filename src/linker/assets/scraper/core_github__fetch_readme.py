import os
import subprocess
from dagster import (
    asset,
    AssetIn,
    AssetKey,
    Output,
)

import pandas as pd

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

@asset(
    kinds={"go", "postgres"},
    owners=DEFAULT_OWNERS,
    # Depends on detection
    ins={"core_github__detect_languages": AssetIn(key=AssetKey(["github", "int_github_detection"]))},
    group_name="ingestion",
    key=AssetKey(["github", "raw_github_readme"]), # Matches dbt source
    required_resource_keys={"config"},
)
def core_github__fetch_readme(context, core_github__detect_languages: pd.DataFrame):
    """
    Fetch GitHub /readme for each project using Go fetcher.

    **Description:**
    Triggers the external Go binary (`ost-fetcher`) to retrieve README content
    from GitHub API and upsert them directly into PostgreSQL.

    **Logic:**
    1. **Execution**: Calls `ost-fetcher --mode readme`.
    2. **Concurrency**: the Go binary handles massive concurrency.
    3. **Output**: Returns status metadata, data is written to DB.
    """
    context.log.info("core_github__fetch_readme: Starting Go fetcher...")
    
    # Path to the compiled Go binary from config
    cfg = context.resources.config
    fetcher_bin = cfg.go_fetcher_path
    
    if not fetcher_bin:
        raise RuntimeError("GO_FETCHER_PATH not configured in cfg.yaml")
    
    if not os.path.exists(fetcher_bin):
        raise RuntimeError(f"Go binary not found at {fetcher_bin}. Please run 'go build -o ost-fetcher .' in src/services/go/fetcher/")

    # Environment with DATABASE_URL
    env = os.environ.copy()
    db_url = env.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL is required for Go fetcher")
        
    cmd = [fetcher_bin, "--mode", "readme", "--concurrency", "20"]

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

    # We don't return the full list of content anymore as it's in DB.
    # We return empty list or metadata.
    return Output(value=None, metadata={"status": "completed_via_go"})
