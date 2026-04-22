import json
import os
import subprocess

from dagster import (
    AssetExecutionContext,
    AssetKey,
    MetadataValue,
    Output,
    asset,
)

from ...resources.cfg_resource import build_trending_env

DEFAULT_OWNERS = ["team:OST/spideyai-X"]


@asset(
    kinds={"go", "postgres"},
    owners=DEFAULT_OWNERS,
    group_name="ingestion",
    required_resource_keys={"config"},
    key=AssetKey(["github", "raw_trending_project"]),
)
def raw_github__extract_trending(context: AssetExecutionContext) -> Output[None]:
    """Execute Go trending scraper to fetch GitHub Trending repos and write to DB."""
    context.log.info("raw_github__extract_trending: Starting GitHub Trending scraper")
    cfg = context.resources.config

    env = os.environ.copy()
    env.update(build_trending_env(cfg))

    if "DATABASE_URL" not in env:
        msg = "DATABASE_URL must be set in environment or config for trending scraper"
        raise ValueError(msg)

    trending_path = cfg.go_trending_path
    if not trending_path:
        raise RuntimeError("GO_TRENDING_PATH not configured")

    if not os.path.exists(trending_path):
        raise RuntimeError(f"Go trending binary not found at {trending_path}")

    context.log.info(f"Using trending scraper at {trending_path}")

    try:
        result = subprocess.run(
            [trending_path],
            capture_output=True,
            text=True,
            env=env,
            cwd=os.getcwd(),
            timeout=300,
        )

        stdout = result.stdout
        stderr = result.stderr

        if result.returncode != 0:
            context.log.error(f"Trending scraper exited with code {result.returncode}")
            context.log.error(f"Stderr: {stderr}")
            context.log.error(f"Stdout: {stdout}")
            raise RuntimeError(f"Trending scraper failed (exit {result.returncode})")

        context.log.info(f"Trending scraper stdout: {stdout}")
        if stderr:
            context.log.warning(f"Trending scraper stderr: {stderr}")

        try:
            summary = json.loads(stdout)
        except Exception:
            context.log.warning("Could not parse trending scraper summary JSON")
            return Output(
                value=None,
                metadata={"status": "completed_via_go_unparsed"},
            )

        return Output(
            value=None,
            metadata={
                "collected": MetadataValue.int(summary.get("collected", 0)),
                "upserted": MetadataValue.int(summary.get("upserted", 0)),
                "failed": MetadataValue.int(summary.get("failed", 0)),
                "trending_date": MetadataValue.text(
                    summary.get("trending_date", "unknown")
                ),
                "duration_seconds": MetadataValue.float(
                    summary.get("duration_seconds", 0)
                ),
                "status": MetadataValue.text(summary.get("status", "unknown")),
            },
        )

    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Trending scraper timed out after 300s") from exc
    except Exception as e:
        context.log.error(f"Trending scraper execution error: {e}")
        raise
