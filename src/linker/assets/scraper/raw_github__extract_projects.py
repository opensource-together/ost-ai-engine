import json
import os
import subprocess

from dagster import (
    AssetKey,
    MetadataValue,
    Output,
    asset,
)

from ...resources.cfg_resource import build_scraper_env

DEFAULT_OWNERS = ["team:OST/spideyai-X"]


@asset(
    kinds={"go", "postgres"},
    owners=DEFAULT_OWNERS,
    group_name="ingestion",
    required_resource_keys={"config"},
    key=AssetKey(["github", "raw_github_project"]),  # Matches DB table
)
def raw_github__extract_projects(context):
    """Execute Go scraper to fetch GitHub projects and write to DB.

    Supports multi-query parallel scraping and single-query legacy format.
    """
    context.log.info("raw_github__extract_projects: Starting GitHub scraper execution")
    cfg = context.resources.config

    # Start with full environment, then add/override with config values
    env = os.environ.copy()
    env.update(build_scraper_env(cfg))

    # Ensure DATABASE_URL is passed (from config or env)
    if "DATABASE_URL" not in env:
        msg = "DATABASE_URL must be set in environment or config for scraper"
        raise ValueError(msg)

    # Locate binary from config resource
    scraper_path = cfg.go_scraper_path
    if not scraper_path:
        raise RuntimeError("GO_SCRAPER_PATH not configured")

    if not os.path.exists(scraper_path):
        raise RuntimeError(f"Go scraper binary not found at {scraper_path}")

    context.log.info(f"Using scraper at {scraper_path}")
    queries_json = env.get("GITHUB_SCRAPING_QUERIES", "[]")
    context.log.info(f"Queries: {queries_json}")

    try:
        # Run scraper
        result = subprocess.run(
            [scraper_path],
            capture_output=True,
            text=True,
            env=env,
            cwd=os.getcwd(),
            timeout=600,  # 10 minutes for parallel multi-query
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
        except Exception:
            context.log.warning("Could not parse scraper summary JSON")
            return Output(
                value=None,
                metadata={"status": "completed_via_go_unparsed"},
            )

        # Multi-query format (has "queries" key)
        if "queries" in summary:
            for qr in summary["queries"]:
                context.log.info(
                    f"  query={qr['query']!r}  collected={qr['collected_count']}  "
                    f"upserted={qr['upserted_count']}  failed={qr['failed_upserts']}"
                )

            metadata: dict[str, MetadataValue] = {
                "num_queries": MetadataValue.int(len(summary["queries"])),
                "total_collected": MetadataValue.int(summary.get("total_collected", 0)),
                "total_upserted": MetadataValue.int(summary.get("total_upserted", 0)),
                "total_failed": MetadataValue.int(summary.get("total_failed", 0)),
                "duration_seconds": MetadataValue.float(
                    summary.get("duration_seconds", 0)
                ),
                "status": MetadataValue.text(summary.get("status", "unknown")),
            }

            # Per-query breakdown as JSON text
            metadata["per_query"] = MetadataValue.json(summary["queries"])

            return Output(value=None, metadata=metadata)

        # Legacy single-query format
        return Output(
            value=None,
            metadata={
                "collected_count": MetadataValue.int(summary.get("collected_count", 0)),
                "upserted_count": MetadataValue.int(summary.get("upserted_count", 0)),
                "query": MetadataValue.text(
                    env.get("GITHUB_SCRAPING_QUERY", "unknown")
                ),
                "status": MetadataValue.text("completed_via_go"),
            },
        )

    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("GitHub scraper timed out after 600s") from exc
    except Exception as e:
        context.log.error(f"GitHub scraper execution error: {e}")
        raise
