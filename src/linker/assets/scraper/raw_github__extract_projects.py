import os
import json
import subprocess
import typing as _t
from dagster import (
    asset,
    MetadataValue,
    Output,
    AssetKey,
)
from ...resources.cfg_resource import build_scraper_env

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

@asset(
    kinds={"go", "postgres"},
    owners=DEFAULT_OWNERS,
    group_name="ingestion",
    required_resource_keys={"config"},
    key=AssetKey(["github", "raw_github_project"]), # Matches DB table
)
def raw_github__extract_projects(context):
    """
    Executes the external Go scraper to fetch GitHub project data and write directly to DB.
    """
    context.log.info("raw_github__extract_projects: Starting GitHub scraper execution")
    cfg = context.resources.config
    
    # Start with full environment, then add/override with config values
    env = os.environ.copy()
    env.update(build_scraper_env(cfg))
    
    # Ensure DATABASE_URL is passed (from config or env)
    if "DATABASE_URL" not in env:
        raise ValueError("DATABASE_URL must be set in environment or config for scraper")

    # Locate binary from config resource
    scraper_path = cfg.go_scraper_path
    if not scraper_path:
        raise RuntimeError("GO_SCRAPER_PATH not configured")

    if not os.path.exists(scraper_path):
        raise RuntimeError(f"Go scraper binary not found at {scraper_path}")

    context.log.info(f"Using scraper at {scraper_path}")
    context.log.info(f"Query: '{env.get('GITHUB_SCRAPING_QUERY')}'")

    try:
        # Run scraper
        result = subprocess.run(
            [scraper_path],
            capture_output=True,
            text=True,
            env=env,
            cwd=os.getcwd(), # Cwd might matter for config file loading if used
            timeout=300 # 5 minutes
        )
        
        stdout = result.stdout
        stderr = result.stderr
        
        if result.returncode != 0:
            context.log.error(f"GitHub scraper exited with code {result.returncode}")
            context.log.error(f"Stderr: {stderr}")
            context.log.error(f"Stdout: {stdout}")
            raise RuntimeError(f"GitHub scraper failed (exit {result.returncode})")

        context.log.info(f"Scraper stdout: {stdout}")
        if stderr:
             context.log.warning(f"Scraper stderr: {stderr}")
             
        # Parse summary from stdout
        try:
            summary = json.loads(stdout)
            count = summary.get("collected_count", 0)
            upserted = summary.get("upserted_count", 0)
        except Exception:
            context.log.warning("Could not parse scraper summary JSON")
            count = 0
            upserted = 0

        return Output(
            value=None,
            metadata={
                "collected_count": MetadataValue.int(count),
                "upserted_count": MetadataValue.int(upserted),
                "query": MetadataValue.text(env.get("GITHUB_SCRAPING_QUERY", "unknown")),
                "status": "completed_via_go"
            },
        )

    except subprocess.TimeoutExpired:
        raise RuntimeError("GitHub scraper timed out after 300s")
    except Exception as e:
        context.log.error(f"GitHub scraper execution error: {e}")
        raise
