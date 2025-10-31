import os
import json
import subprocess
from contextlib import contextmanager

from dagster import (
    asset,
    AssetIn,
    MetadataValue,
    Output,
)

# Dagster resources
from src.pipeline.resources.cfg_resource import build_scraper_env
from src.pipeline.resources.map.mapping_map import (
    GITLAB_TO_PROJECT_MAPPING,
)

DEFAULT_OWNERS = ["team:OST/spideyai-X"]


@asset(
    kinds={"go", "github"},
    owners=DEFAULT_OWNERS,
    group_name="github_projects_scraper",
    required_resource_keys={"config"},
)
def raw_github__extract_projects(context):
    """Run the GitHub Go scraper and return scraped projects.

    Description:
    - Executes the compiled Go `github-scraper` binary.
    - Parses stdout as JSON and returns a list of project dicts.
    - Emits metadata: project_count, first_project.
    """
    cfg = context.resources.config
    env = build_scraper_env(cfg)
    context.log.info(f"GITHUB_SCRAPING_QUERY to Go: '{env['GITHUB_SCRAPING_QUERY']}'")
    try:
        result = subprocess.run([
            "/app/github-scraper"
        ], capture_output=True, text=True, env=env, cwd="/app", timeout=120)
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        if result.returncode != 0:
            context.log.error(f"GitHub scraper exited with code {result.returncode}")
            context.log.error(f"GitHub scraper stdout: {stdout}")
            context.log.error(f"GitHub scraper stderr: {stderr}")
            raise RuntimeError(f"GitHub scraper failed (exit {result.returncode}). See logs for stdout/stderr")
        context.log.info(f"GitHub scraper raw output: {stdout[:500]}")
        parsed = json.loads(stdout)
        if isinstance(parsed, dict) and "items" in parsed:
            projects = parsed["items"]
        elif isinstance(parsed, list):
            projects = parsed
        else:
            projects = []
        count = len(projects)
        context.log.info(f"[DEBUG] github_scraper_asset: {count} projects scraped. Example: {projects[:1]}")
        return Output(
            value=projects,
            metadata={
                "project_count": MetadataValue.int(count),
                "first_project": MetadataValue.json(projects[:1]) if projects else MetadataValue.null(),
            },
        )
    except OSError as e:
        context.log.error(f"GitHub scraper OSError: {e}")
        return Output(value=[], metadata={"project_count": MetadataValue.int(0), "error": MetadataValue.text(str(e))})
    except Exception as e:
        context.log.exception("GitHub scraper error")
        return Output(value=[], metadata={"project_count": MetadataValue.int(0), "error": MetadataValue.text(str(e))})





@asset(
    kinds={"go", "gitlab"},
    owners=DEFAULT_OWNERS,
    group_name="gitlab",
    required_resource_keys={"config"},
)
def raw_gitlab__extract_projects(context):
    """Run the GitLab Go scraper and return scraped projects.

    Description:
    - Executes the compiled Go `gitlab-scraper` binary.
    - Parses stdout as JSON and returns a list of project dicts.
    - Emits metadata: project_count, first_project.
    """
    cfg = context.resources.config
    env = build_scraper_env(cfg)
    context.log.info(f"GITLAB_SCRAPING_QUERY transmis au process Go: '{env['GITLAB_SCRAPING_QUERY']}'")
    context.log.info(f"GITLAB_PROJECTS_VISIBILITY: {env['GITLAB_PROJECTS_VISIBILITY']}, ARCHIVED: {env['GITLAB_PROJECTS_ARCHIVED']}, ORDER_BY: {env['GITLAB_PROJECTS_ORDER_BY']}, SORT: {env['GITLAB_PROJECTS_SORT']}")
    try:
        result = subprocess.run([
            "/app/gitlab-scraper"
        ], capture_output=True, text=True, env=env, cwd="/app", timeout=120)
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        if result.returncode != 0:
            context.log.error(f"GitLab scraper exited with code {result.returncode}")
            context.log.error(f"GitLab scraper stdout: {stdout}")
            context.log.error(f"GitLab scraper stderr: {stderr}")
            raise RuntimeError(f"GitLab scraper failed (exit {result.returncode}). See logs for stdout/stderr")
        context.log.info(f"GitLab scraper raw output: {stdout[:500]}")
        parsed = json.loads(stdout)
        if isinstance(parsed, dict) and "items" in parsed:
            projects = parsed["items"]
        elif isinstance(parsed, list):
            projects = parsed
        else:
            projects = []
        count = len(projects)
        context.log.info(f"[DEBUG] gitlab_scraper_asset: {count} projects scraped. Example: {projects[:1]}")
        return Output(
            value=projects,
            metadata={
                "project_count": MetadataValue.int(count),
                "first_project": MetadataValue.json(projects[:1]) if projects else MetadataValue.null(),
            },
        )
    except OSError as e:
        context.log.error(f"GitLab scraper OSError: {e}")
        return Output(value=[], metadata={"project_count": MetadataValue.int(0), "error": MetadataValue.text(str(e))})
    except Exception as e:
        context.log.exception("GitLab scraper error")
        return Output(value=[], metadata={"project_count": MetadataValue.int(0), "error": MetadataValue.text(str(e))})
