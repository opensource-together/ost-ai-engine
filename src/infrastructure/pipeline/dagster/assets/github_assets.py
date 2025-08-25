import json
import subprocess
import os
from datetime import date, datetime
from pathlib import Path
from typing import List

from dagster import (
    AssetIn,
    AssetKey,
    Config,
    Nothing,
    Output,
    asset,
)
from github import Github
from sqlalchemy import text

from src.infrastructure.postgres.database import get_db_session
from src.infrastructure.config import settings

# Use PROJECT_ROOT from config for dbt project directory
DBT_PROJECT_DIR = (Path(settings.PROJECT_ROOT) / settings.DBT_PROJECT_DIR).resolve()

class GithubConfig(Config):
    """Configuration for the GitHub repo scraping asset."""
    query: str = ""  # Will use settings.GITHUB_SCRAPING_QUERY if empty
    max_repositories: int = 0  # Will use settings.GITHUB_MAX_REPOSITORIES if 0


@asset(
    name="github_repositories",
    description="Scrape GitHub with Go and upsert directly into github_PROJECT (Postgres).",
    required_resource_keys={"github_client"},  # Keep for compatibility
    group_name="github_scraping",
    compute_kind="github",
)
def github_repositories(context, config: GithubConfig) -> Output[List[dict]]:
    """
    Scrapes the GitHub API using Go service and upserts directly into Postgres.
    Also returns the scraped repositories for visibility/metadata.
    """

    # Use settings if not provided in config
    query = config.query or settings.GITHUB_SCRAPING_QUERY
    max_repos = config.max_repositories or settings.GITHUB_MAX_REPOSITORIES

    context.log.info(f"🚀 Starting GitHub scraping with Go service (direct DB upsert)")
    context.log.info(f"📊 Target: {max_repos} repositories")
    context.log.info(f"🔍 Query: '{query}'")

    try:
        # Get tokens and DB URL from centralized config
        github_token = settings.GITHUB_ACCESS_TOKEN
        db_url = settings.DATABASE_URL

        # Build command for Go service using config
        go_service_path = settings.GO_SCRAPER_PATH
        cmd = [
            go_service_path,
            "--query", query,
            "--max-repos", str(max_repos),
            "--output", "json",
            "--db-url", db_url,
            "--upsert",
        ]

        # Add token if available
        if github_token and github_token != "your_github_token_here":
            cmd.extend(["--token", github_token])
            context.log.info("✅ Using authenticated GitHub client")
        else:
            context.log.warning("⚠️ Using unauthenticated GitHub client (limited rate)")

        # Execute Go service
        context.log.info(f"🔧 Executing: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=os.getcwd()
        )


        if result.stderr:
            context.log.info("🔍 Go service logs:")
            for line in result.stderr.strip().split('\n'):
                if line.strip():
                    context.log.info(f"   {line.strip()}")

        # Parse JSON output from Go service
        repositories = json.loads(result.stdout)

        context.log.info(f"✅ Go service completed successfully!")
        context.log.info(f"📊 Total repositories scraped: {len(repositories)}")

        return Output(
            repositories,
            metadata={
                "count": len(repositories),
                "query": query,
                "limit": max_repos,
                "service": "go",
                "upserted_to_db": True,
            },
        )

    except subprocess.CalledProcessError as e:
        context.log.error(f"🚨 Go service failed with exit code {e.returncode}")
        context.log.error(f"📄 Stdout: {e.stdout}")
        context.log.error(f"📄 Stderr: {e.stderr}")
        raise Exception(f"Go service failed: {e.stderr}")

    except json.JSONDecodeError as e:
        context.log.error(f"🚨 Failed to parse JSON from Go service: {e}")
        context.log.error(f"📄 Raw output: {result.stdout[:500]}...")
        raise Exception(f"Invalid JSON from Go service: {e}")

    except Exception as e:
        context.log.error(f"🚨 Unexpected error: {e}")
        raise


@asset(
    name="github_project_table",
    description="Checkpoint: verify github_PROJECT populated after Go upsert.",
    ins={"repos": AssetIn(key=AssetKey("github_repositories"))},
    group_name="github_scraping",
    compute_kind="postgres",
)
def github_project_table(context, repos: List[dict]) -> Output[None]:
    """
    Simple checkpoint to verify that rows exist in github_PROJECT.
    """
    from sqlalchemy import text as sql_text

    with get_db_session() as db:
        count = db.execute(sql_text('SELECT COUNT(*) FROM "github_PROJECT"')).scalar()
        context.log.info(f"✅ github_PROJECT row count: {count}")
        if count == 0:
            raise Exception("github_PROJECT is empty after Go upsert")

    return Output(None)
