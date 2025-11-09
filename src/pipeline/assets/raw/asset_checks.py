from dagster import (
    asset_check,
    AssetCheckResult,
    MetadataValue,
)


@asset_check(
    asset="core_github__extract_top_projects",
    name="core_github__extract_top_projects_description_is_not_empty",
)
def core_github__extract_top_projects_description_is_not_empty(context, core_github__extract_top_projects):
    """Check that each project has a non-empty description.

    Returns detailed metadata to help debugging.
    """
    # Accept list or DataFrame
    import pandas as pd

    if isinstance(core_github__extract_top_projects, pd.DataFrame):
        core_list = core_github__extract_top_projects.to_dict(orient="records")
    elif isinstance(core_github__extract_top_projects, list):
        core_list = core_github__extract_top_projects
    else:
        msg = "Input to check is not a list or DataFrame."
        context.log.error(msg)
        return AssetCheckResult(
            passed=False,
            description=msg,
            metadata={
                "type": MetadataValue.text(str(type(core_github__extract_top_projects))),
                "count": MetadataValue.null(),
            },
        )

    missing_indices = []
    missing_examples = []
    for i, project in enumerate(core_list):
        if project.get("description") in (None, ""):
            missing_indices.append(i)
            if len(missing_examples) < 5:
                example_title = project.get("name") or project.get("full_name") or project.get("title") or project.get("repoUrl")
                missing_examples.append({"index": i, "example": example_title})

    metadata = {
        "missing_count": MetadataValue.int(len(missing_indices)),
        "missing_indices": MetadataValue.json(missing_indices[:50]),
        "missing_examples": MetadataValue.json(missing_examples),
    "total": MetadataValue.int(len(core_list)),
    }

    if missing_indices:
        msg = f"{len(missing_indices)} project(s) missing description."
        context.log.error(msg)
        metadata["error"] = MetadataValue.text(msg)
        return AssetCheckResult(passed=False, description=msg, metadata=metadata)

    msg = "All projects have a non-empty description."
    context.log.info(msg)
    metadata["info"] = MetadataValue.text(msg)
    return AssetCheckResult(passed=True, description=msg, metadata=metadata)


@asset_check(
    asset="raw_github__extract_projects",
    name="raw_github__extract_projects_non_empty",
)
def raw_github__extract_projects_non_empty(context, raw_github__extract_projects):
    """Ensure the GitHub scraper returned a non-empty list of projects."""
    if not isinstance(raw_github__extract_projects, list):
        msg = "Output is not a list."
        context.log.error(msg)
        return AssetCheckResult(passed=False, description=msg, metadata={"type": MetadataValue.text(str(type(raw_github__extract_projects)))} )

    count = len(raw_github__extract_projects)
    if count == 0:
        msg = "GitHub scraper returned no projects."
        context.log.error(msg)
        return AssetCheckResult(passed=False, description=msg, metadata={"project_count": MetadataValue.int(0)})

    return AssetCheckResult(passed=True, description=f"GitHub scraper returned {count} projects.", metadata={"project_count": MetadataValue.int(count)})


@asset_check(
    asset="raw_gitlab__extract_projects",
    name="raw_gitlab__extract_projects_non_empty",
)
def raw_gitlab__extract_projects_non_empty(context, raw_gitlab__extract_projects):
    """Ensure the GitLab scraper returned a non-empty list of projects."""
    if not isinstance(raw_gitlab__extract_projects, list):
        msg = "Output is not a list."
        context.log.error(msg)
        return AssetCheckResult(passed=False, description=msg, metadata={"type": MetadataValue.text(str(type(raw_gitlab__extract_projects)))} )

    count = len(raw_gitlab__extract_projects)
    if count == 0:
        msg = "GitLab scraper returned no projects."
        context.log.error(msg)
        return AssetCheckResult(passed=False, description=msg, metadata={"project_count": MetadataValue.int(0)})

    return AssetCheckResult(passed=True, description=f"GitLab scraper returned {count} projects.", metadata={"project_count": MetadataValue.int(count)})
