from dagster import (
    asset_check,
    AssetCheckResult,
    MetadataValue,
)


@asset_check(
    asset="github_top_projects_asset",
    name="github_top_projects_description_check",
)
def github_top_projects_description_check(context, github_top_projects_asset):
    """Check that each project has a non-empty description.

    Returns detailed metadata to help debugging.
    """
    if not isinstance(github_top_projects_asset, list):
        msg = "Input to check is not a list."
        context.log.error(msg)
        return AssetCheckResult(
            passed=False,
            description=msg,
            metadata={
                "type": MetadataValue.text(str(type(github_top_projects_asset))),
                "count": MetadataValue.null(),
            },
        )

    missing_indices = []
    missing_examples = []
    for i, project in enumerate(github_top_projects_asset):
        if project.get("description") in (None, ""):
            missing_indices.append(i)
            if len(missing_examples) < 5:
                example_title = project.get("name") or project.get("full_name") or project.get("title") or project.get("repoUrl")
                missing_examples.append({"index": i, "example": example_title})

    metadata = {
        "missing_count": MetadataValue.int(len(missing_indices)),
        "missing_indices": MetadataValue.json(missing_indices[:50]),
        "missing_examples": MetadataValue.json(missing_examples),
        "total": MetadataValue.int(len(github_top_projects_asset)),
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
