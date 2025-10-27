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
	"""Ensure each project has a non-empty description and return diagnostics.

	Produces metadata: missing_count, missing_indices, missing_examples, total.
	"""
	if not isinstance(core_github__extract_top_projects, list):
		msg = "Input to check is not a list."
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
	for i, project in enumerate(core_github__extract_top_projects):
		if project.get("description") in (None, ""):
			missing_indices.append(i)
			if len(missing_examples) < 5:
				example_title = project.get("name") or project.get("full_name") or project.get("title") or project.get("repoUrl")
				missing_examples.append({"index": i, "example": example_title})

	metadata = {
		"missing_count": MetadataValue.int(len(missing_indices)),
		"missing_indices": MetadataValue.json(missing_indices[:50]),
		"missing_examples": MetadataValue.json(missing_examples),
		"total": MetadataValue.int(len(core_github__extract_top_projects)),
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
	asset="core_repo_lang_detect",
	name="core_repo_lang_detect_language_fields_present",
)
def core_repo_lang_detect_language_fields_present(context, core_repo_lang_detect):
	"""Verify each record has `language` and `language_confidence` keys (may be None).

	Fails when output is not a list or items are missing the expected keys.
	"""
	if not isinstance(core_repo_lang_detect, list):
		msg = "Output is not a list."
		context.log.error(msg)
		return AssetCheckResult(passed=False, description=msg, metadata={"type": MetadataValue.text(str(type(core_repo_lang_detect)))})

	missing = []
	for i, item in enumerate(core_repo_lang_detect):
		if not isinstance(item, dict) or ("language" not in item or "language_confidence" not in item):
			missing.append(i)

	if missing:
		msg = f"{len(missing)} item(s) missing language fields."
		context.log.error(msg)
		return AssetCheckResult(passed=False, description=msg, metadata={"missing_indices": MetadataValue.json(missing[:50])})

	return AssetCheckResult(passed=True, description="All items contain language and language_confidence fields.", metadata={"total": MetadataValue.int(len(core_repo_lang_detect))})


@asset_check(
	asset="core_github__table_projects_mapped",
	name="core_github__table_projects_mapped_repoUrl_present",
)
def core_github__table_projects_mapped_repoUrl_present(context, core_github__table_projects_mapped):
	"""Ensure mapped projects include a non-empty `repoUrl` for all items (required for DB upsert)."""
	if not isinstance(core_github__table_projects_mapped, list):
		msg = "Output is not a list."
		context.log.error(msg)
		return AssetCheckResult(passed=False, description=msg, metadata={"type": MetadataValue.text(str(type(core_github__table_projects_mapped)))})

	missing_indices = []
	for i, proj in enumerate(core_github__table_projects_mapped):
		if not isinstance(proj, dict) or not proj.get("repoUrl"):
			missing_indices.append(i)

	if missing_indices:
		msg = f"{len(missing_indices)} mapped project(s) missing repoUrl."
		context.log.error(msg)
		return AssetCheckResult(passed=False, description=msg, metadata={"missing_indices": MetadataValue.json(missing_indices[:50])})

	return AssetCheckResult(passed=True, description="All mapped projects include repoUrl.", metadata={"mapped_count": MetadataValue.int(len(core_github__table_projects_mapped))})
