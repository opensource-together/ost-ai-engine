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

from src.dagster.config.cfg_resource import build_scraper_env
from src.dagster.config.map.mapping_map import GITHUB_TO_PROJECT_MAPPING, GITLAB_TO_PROJECT_MAPPING
from src.services.python.prisma_client import prisma_client

DEFAULT_OWNERS = ["team:OST/spideyai-X"]


@asset(
    kinds={"go", "github"},
    owners=DEFAULT_OWNERS,
    required_resource_keys={"config"},
)
def github_scraper_asset(context):
    """Run the GitHub Go scraper and emit results as metadata."""
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
    kinds={"python"},
    owners=DEFAULT_OWNERS,
    ins={"github_scraper_asset": AssetIn()},
    required_resource_keys={"config"},
)
def github_top_projects_asset(context, github_scraper_asset):
    """Ranks projects by stars and keeps only the top N (configurable)."""
    top_n = context.resources.config.github_top_n
    if not github_scraper_asset or not isinstance(github_scraper_asset, list):
        context.log.warning("No projects to rank.")
        return []
    filtered = [p for p in github_scraper_asset if p.get("description") not in (None, "")]
    context.log.info(f"[DEBUG] github_top_projects_asset: {len(filtered)} projects with description out of {len(github_scraper_asset)}")
    if not filtered:
        context.log.warning("[DEBUG] github_top_projects_asset: No project with description found.")
        return Output(value=[], metadata={
            "selected_count": MetadataValue.int(0),
            "reason": MetadataValue.text("No project with description found."),
        })
    ranked = sorted(filtered, key=lambda p: p.get("stargazers_count", 0), reverse=True)
    top_projects = ranked[:top_n]
    meta = {
        "selected_count": MetadataValue.int(len(top_projects)),
        "input_count": MetadataValue.int(len(github_scraper_asset)),
        "stars_range": MetadataValue.text(f"{top_projects[0].get('stargazers_count', 0)} - {top_projects[-1].get('stargazers_count', 0)}") if top_projects else MetadataValue.null(),
    }
    return Output(value=top_projects, metadata=meta)


@asset(
    kinds={"python"},
    owners=DEFAULT_OWNERS,
    ins={"github_top_projects_asset": AssetIn()},
)
def github_mapping_asset(context, github_top_projects_asset):
    """Transforms top ranked GitHub projects to match the Prisma Project model using the mapping config."""
    if github_top_projects_asset is None:
        context.log.warning("No data found from github_top_projects_asset. Returning empty list.")
        return []
    def map_repo(repo):
        mapped = {}
        for prisma_field, source in GITHUB_TO_PROJECT_MAPPING.items():
            if callable(source):
                mapped[prisma_field] = source(repo)
            elif isinstance(source, str) and "." in source:
                keys = source.split(".")
                value = repo
                for k in keys:
                    value = value.get(k, None) if isinstance(value, dict) else None
                mapped[prisma_field] = value
            elif isinstance(source, str):
                mapped[prisma_field] = repo.get(source)
            else:
                mapped[prisma_field] = source
        return mapped

    projects = [map_repo(repo) for repo in github_top_projects_asset]
    context.log.info(f"[DEBUG] github_mapping_asset: {len(projects)} mapped projects.")
    return Output(value=projects, metadata={
        "mapped_count": MetadataValue.int(len(projects)),
        "input_count": MetadataValue.int(len(github_top_projects_asset)),
    })


@asset(
    kinds={"python", "postgres"},
    owners=DEFAULT_OWNERS,
    ins={"github_mapping_asset": AssetIn()},
)
def github_to_db_asset(context, github_mapping_asset):
    """Inserts mapped projects into the Project table using the Prisma Python client (based on repoUrl)."""
    inserted = 0
    errors = []
    with prisma_client() as prisma:
        for i, project in enumerate(github_mapping_asset):
            repo_url = project.get("repoUrl")
            if not repo_url:
                context.log.warning(f"Skipping project {i}: missing repoUrl (required for insert).")
                errors.append((i, "missing_repoUrl"))
                continue
            try:
                project_data = {k: v for k, v in project.items() if v is not None}
                prisma.project.create(data=project_data)
                inserted += 1
            except Exception as e:
                context.log.error(f"Error inserting project {i} (repoUrl={repo_url}): {e}")
                errors.append((i, str(e)))
    context.log.info(f"{inserted} projects inserted into the Project table.")
    if errors:
        context.log.warning(f"{len(errors)} insert errors: {errors[:3]}")
    return Output(value=inserted, metadata={
        "inserted_count": MetadataValue.int(inserted),
        "error_count": MetadataValue.int(len(errors)),
        "first_error": MetadataValue.text(errors[0][1]) if errors else MetadataValue.null(),
    })


@asset(
    kinds={"go", "gitlab"},
    owners=DEFAULT_OWNERS,
    required_resource_keys={"config"},
)
def gitlab_scraper_asset(context):
    """Run the GitLab Go scraper and emit results as metadata."""
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
