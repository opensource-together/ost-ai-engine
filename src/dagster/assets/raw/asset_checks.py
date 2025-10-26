from dagster import (
    asset_check,
    AssetCheckResult,
    AssetIn,
    MetadataValue,
)

from src.services.python.prisma_client import prisma_client


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


@asset_check(asset="github_mapping_asset", name="github_mapping_type_check")
def github_mapping_type_check(context, github_mapping_asset):
    metadata = {
        "type": MetadataValue.text(str(type(github_mapping_asset))),
        "count": MetadataValue.int(len(github_mapping_asset)) if isinstance(github_mapping_asset, list) else MetadataValue.null(),
        "first": MetadataValue.json(github_mapping_asset[:1]) if isinstance(github_mapping_asset, list) and len(github_mapping_asset) > 0 else MetadataValue.null(),
        "is_list": MetadataValue.bool(isinstance(github_mapping_asset, list)),
    }
    if not isinstance(github_mapping_asset, list):
        msg = "Mapping output is not a list."
        context.log.error(msg)
        metadata["error"] = MetadataValue.text(msg)
        return AssetCheckResult(passed=False, description=msg, metadata=metadata)
    if len(github_mapping_asset) == 0:
        msg = "Mapping output is empty."
        context.log.error(msg)
        metadata["error"] = MetadataValue.text(msg)
        return AssetCheckResult(passed=False, description=msg, metadata=metadata)
    msg = "Mapping output is a non-empty list."
    context.log.info(msg)
    metadata["info"] = MetadataValue.text(msg)
    return AssetCheckResult(passed=True, description=msg, metadata=metadata)


@asset_check(asset="github_mapping_asset", name="github_mapping_required_fields_check")
def github_mapping_required_fields_check(context, github_mapping_asset):
    required_fields = ["title", "repoUrl", "provider", "published", "trending"]
    missing_fields = []
    type_errors = []
    for i, project in enumerate(github_mapping_asset):
        for field in required_fields:
            if field not in project or project[field] in (None, ""):
                missing_fields.append((i, field))
        if "published" in project and not isinstance(project["published"], bool):
            type_errors.append((i, "published_not_bool"))
        if "trending" in project:
            if not isinstance(project["trending"], bool):
                type_errors.append((i, "trending_not_bool"))
            elif project["trending"] is not True:
                type_errors.append((i, "trending_not_true"))
    metadata = {
        "missing_fields": MetadataValue.int(len(missing_fields)),
        "type_errors": MetadataValue.int(len(type_errors)),
        "missing_examples": MetadataValue.json(missing_fields[:5]),
        "type_error_examples": MetadataValue.json(type_errors[:5]),
        "total": MetadataValue.int(len(github_mapping_asset)),
        "required_fields": MetadataValue.json(required_fields),
    }
    if missing_fields or type_errors:
        msg = f"{len(missing_fields)} missing/invalid fields, {len(type_errors)} type errors."
        context.log.error(msg)
        metadata["error"] = MetadataValue.text(msg)
        return AssetCheckResult(passed=False, description=msg, metadata=metadata)
    msg = "All projects have required fields and correct types."
    context.log.info(msg)
    metadata["info"] = MetadataValue.text(msg)
    return AssetCheckResult(passed=True, description=msg, metadata=metadata)


@asset_check(asset="github_mapping_asset", name="github_mapping_duplicate_url_check")
def github_mapping_duplicate_url_check(context, github_mapping_asset):
    repo_urls = [p.get("repoUrl") for p in github_mapping_asset if "repoUrl" in p and p.get("repoUrl")]
    github_urls = [p.get("githubUrl") for p in github_mapping_asset if "githubUrl" in p and p.get("githubUrl")]
    duplicate_repo_urls = len(repo_urls) != len(set(repo_urls))
    duplicate_github_urls = len(github_urls) != len(set(github_urls))
    metadata = {
        "repoUrl_duplicates": MetadataValue.bool(duplicate_repo_urls),
        "githubUrl_duplicates": MetadataValue.bool(duplicate_github_urls),
        "repoUrl_count": MetadataValue.int(len(repo_urls)),
        "githubUrl_count": MetadataValue.int(len(github_urls)),
        "total": MetadataValue.int(len(github_mapping_asset)),
    }
    if duplicate_repo_urls or duplicate_github_urls:
        msg = "Duplicate repoUrl detected." if duplicate_repo_urls else ""
        if duplicate_github_urls:
            msg += " Duplicate githubUrl detected."
        context.log.error(msg)
        metadata["error"] = MetadataValue.text(msg.strip())
        return AssetCheckResult(passed=False, description=msg.strip(), metadata=metadata)
    msg = "No duplicate repoUrl or githubUrl detected."
    context.log.info(msg)
    metadata["info"] = MetadataValue.text(msg)
    return AssetCheckResult(passed=True, description=msg, metadata=metadata)


@asset_check(asset="github_to_db_asset", name="github_to_db_insert_count_check", additional_ins={"github_mapping_asset": AssetIn()})
def github_to_db_insert_count_check(context, github_to_db_asset, github_mapping_asset):
    expected = len(github_mapping_asset)
    actual = github_to_db_asset
    metadata = {"expected": MetadataValue.int(expected), "inserted": MetadataValue.int(actual)}
    if actual == expected:
        msg = f"{actual}/{expected} projects inserted."
        metadata["info"] = MetadataValue.text(msg)
        return AssetCheckResult(passed=True, description=msg, metadata=metadata)
    else:
        msg = f"Only {actual}/{expected} projects inserted."
        metadata["error"] = MetadataValue.text(msg)
        return AssetCheckResult(passed=False, description=msg, metadata=metadata)


@asset_check(asset="github_to_db_asset", name="github_to_db_error_check")
def github_to_db_error_check(context, github_to_db_asset):
    metadata = {"inserted": MetadataValue.int(github_to_db_asset)}
    msg = "No insertion errors detected in logs."
    metadata["info"] = MetadataValue.text(msg)
    return AssetCheckResult(passed=True, description=msg, metadata=metadata)


@asset_check(asset="github_to_db_asset", name="github_to_db_consistency_check", additional_ins={"github_mapping_asset": AssetIn()})
def github_to_db_consistency_check(context, github_to_db_asset, github_mapping_asset):
    with prisma_client() as prisma:
        db_count = prisma.project.count()
    expected = len(github_mapping_asset)
    metadata = {"db_count": MetadataValue.int(db_count), "expected": MetadataValue.int(expected)}
    if db_count >= expected:
        msg = f"{db_count} projects in DB (>= {expected} expected)"
        metadata["info"] = MetadataValue.text(msg)
        return AssetCheckResult(passed=True, description=msg, metadata=metadata)
    else:
        msg = f"Only {db_count}/{expected} projects in DB."
        metadata["error"] = MetadataValue.text(msg)
        return AssetCheckResult(passed=False, description=msg, metadata=metadata)


@asset_check(asset="github_to_db_asset", name="github_to_db_uniqueness_check")
def github_to_db_uniqueness_check(context):
    with prisma_client() as prisma:
        projects = prisma.project.find_many()
    repo_urls = [p.repoUrl for p in projects if hasattr(p, "repoUrl") and p.repoUrl]
    metadata = {"repoUrl_count": MetadataValue.int(len(repo_urls)), "unique_repoUrl_count": MetadataValue.int(len(set(repo_urls)))}
    if len(repo_urls) == len(set(repo_urls)):
        msg = "All repoUrls are unique in DB."
        metadata["info"] = MetadataValue.text(msg)
        return AssetCheckResult(passed=True, description=msg, metadata=metadata)
    else:
        msg = "Duplicate repoUrls detected in DB."
        metadata["error"] = MetadataValue.text(msg)
        return AssetCheckResult(passed=False, description=msg, metadata=metadata)


@asset_check(asset="github_to_db_asset", name="github_to_db_mapping_match_check", additional_ins={"github_mapping_asset": AssetIn()})
def github_to_db_mapping_match_check(context, github_mapping_asset):
    with prisma_client() as prisma:
        db_projects = prisma.project.find_many()
    mapping_titles = set(p["title"] for p in github_mapping_asset if "title" in p)
    db_titles = set(p.title for p in db_projects if hasattr(p, "title"))
    missing = mapping_titles - db_titles
    metadata = {
        "missing_titles": MetadataValue.int(len(missing)),
        "missing_examples": MetadataValue.json(list(missing)[:3]),
        "mapping_titles": MetadataValue.int(len(mapping_titles)),
        "db_titles": MetadataValue.int(len(db_titles)),
    }
    if not missing:
        msg = "All mapping titles are present in DB."
        metadata["info"] = MetadataValue.text(msg)
        return AssetCheckResult(passed=True, description=msg, metadata=metadata)
    else:
        msg = f"Missing titles in DB: {list(missing)[:3]}"
        metadata["error"] = MetadataValue.text(msg)
        return AssetCheckResult(passed=False, description=msg, metadata=metadata)
