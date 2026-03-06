import os
import subprocess

import pandas as pd
from dagster import (
    AssetExecutionContext,
    AssetIn,
    AssetKey,
    Output,
    asset,
)

from ...resources.cfg_resource import build_fetcher_env

DEFAULT_OWNERS = ["team:OST/spideyai-X"]


@asset(
    kinds={"go", "postgres"},
    owners=DEFAULT_OWNERS,
    # Depends on detection (to filter topics)
    ins={
        "core_github__detect_languages": AssetIn(
            key=AssetKey(["github", "int_github_detection"])
        )
    },
    group_name="ingestion",
    key=AssetKey(["github", "raw_github_topics"]),  # Matches dbt source
    required_resource_keys={"config"},
)
def core_github__fetch_repo_topics(
    context: AssetExecutionContext, core_github__detect_languages: pd.DataFrame
) -> Output[None]:
    """
    Fetch GitHub /topics for each project using Go fetcher.

    **Description:**
    Triggers the external Go binary (`ost-fetcher`) to retrieve repository topics
    from GitHub API and upsert them directly into PostgreSQL.

    **Logic:**
    1. **Execution**: Calls `ost-fetcher --mode topics`.
    2. **Concurrency**: the Go binary handles massive concurrency.
    3. **Output**: Returns status metadata, data is written to DB.
    """
    context.log.info("core_github__fetch_repo_topics: Starting Go fetcher...")

    # Path to the compiled Go binary from config
    cfg = context.resources.config
    fetcher_bin = cfg.go_fetcher_path

    if not fetcher_bin:
        raise RuntimeError("GO_FETCHER_PATH not configured")

    if not os.path.exists(fetcher_bin):
        raise RuntimeError(
            f"Go binary not found at {fetcher_bin}. "
            "Run 'go build -o ost-fetcher .' "
            "in src/services/go/fetcher/"
        )

    env = os.environ.copy()
    env.update(build_fetcher_env(cfg))

    cmd = [fetcher_bin, "--mode", "topics", "--concurrency", "20"]

    context.log.info(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, env=env, capture_output=True, text=True, check=True, timeout=600
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
