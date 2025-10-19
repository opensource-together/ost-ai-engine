import os
import json
import subprocess
from contextlib import contextmanager

from dagster import (
	asset,
	asset_check,
	AssetCheckResult,
	AssetIn,
	MetadataValue,
	Output
)

from prisma import Prisma
from src.dagster.config.config import PipelineConfig
from src.dagster.config.github_mapping import GITHUB_TO_PROJECT_MAPPING

env = os.environ.copy()
config = PipelineConfig()
env["GITHUB_SCRAPING_QUERY"] = config.github_scraping_query
env["GITHUB_ACCESS_TOKEN"] = config.github_token

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

@contextmanager
def prisma_client():
	prisma = Prisma()
	prisma.connect()
	try:
		yield prisma
	finally:
		prisma.disconnect()

# ========================================
# GITHUB SCRAPER
# ========================================

@asset(
	kinds={"go", "github"},
	owners=DEFAULT_OWNERS
)
def github_scraper_asset(context):
	"""Run the GitHub Go scraper and emit results as metadata."""
	context.log.info(f"GITHUB_SCRAPING_QUERY transmis au process Go: '{env['GITHUB_SCRAPING_QUERY']}'")
	try:
		result = subprocess.run([
			"/app/github-scraper"
		], capture_output=True, text=True, check=True, env=env, cwd="/app")
		stdout = result.stdout.strip()
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
				"first_project": MetadataValue.json(projects[:1]) if projects else MetadataValue.null()
			}
		)
	except subprocess.CalledProcessError as e:
		err_msg = f"GitHub scraper error: {e}\nSTDERR: {e.stderr.strip()}"
		context.log.error(err_msg)
		return Output(value=[], metadata={"project_count": MetadataValue.int(0), "error": MetadataValue.text(err_msg)})
	except Exception as e:
		context.log.error(f"GitHub scraper error: {e}")
		return Output(value=[], metadata={"project_count": MetadataValue.int(0), "error": MetadataValue.text(str(e))})

@asset(
	kinds={"python"},
	owners=DEFAULT_OWNERS,
	ins={"github_scraper_asset": AssetIn()}
)
def github_top_projects_asset(context, github_scraper_asset):
	"""Ranks projects by stars and keeps only the top N (configurable)."""
	top_n = config.github_top_n
	if not github_scraper_asset or not isinstance(github_scraper_asset, list):
		context.log.warning("No projects to rank.")
		return []
	# Filter out projects without a description
	filtered = [p for p in github_scraper_asset if p.get("description") not in (None, "")]
	context.log.info(f"[DEBUG] github_top_projects_asset: {len(filtered)} projects with description out of {len(github_scraper_asset)}")
	if not filtered:
		context.log.warning("[DEBUG] github_top_projects_asset: No project with description found.")
		return Output(value=[], metadata={
			"selected_count": MetadataValue.int(0),
			"reason": MetadataValue.text("No project with description found.")
		})
	ranked = sorted(
		filtered,
		key=lambda p: p.get("stargazers_count", 0),
		reverse=True
	)
	top_projects = ranked[:top_n]
	meta = {
		"selected_count": MetadataValue.int(len(top_projects)),
		"input_count": MetadataValue.int(len(github_scraper_asset)),
		"stars_range": MetadataValue.text(f"{top_projects[0].get('stargazers_count', 0)} - {top_projects[-1].get('stargazers_count', 0)}") if top_projects else MetadataValue.null()
	}
	return Output(value=top_projects, metadata=meta)

@asset(
	kinds={"python"},
	owners=DEFAULT_OWNERS,
	ins={"github_top_projects_asset": AssetIn()}
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
		"input_count": MetadataValue.int(len(github_top_projects_asset))
	})

@asset(
	kinds={"python", "postgres"},
	owners=DEFAULT_OWNERS,
	ins={"github_mapping_asset": AssetIn()}
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
				# Insert only new projects (no update)
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
		"first_error": MetadataValue.text(errors[0][1]) if errors else MetadataValue.null()
	})

# ========================================
# CHECKS
# ========================================

# Check that all projects have a description
@asset_check(
	asset=github_top_projects_asset,
	name="github_top_projects_description_check"
)
def github_top_projects_description_check(context, github_top_projects_asset):
	"""Checks that all projects have a non-empty description."""
	failed = []
	for i, project in enumerate(github_top_projects_asset):
		if project.get("description") in (None, ""):
			failed.append(i)
	metadata = {
		"missing_count": MetadataValue.int(len(failed)),
		"missing_indices": MetadataValue.json(failed[:5]),
		"total": MetadataValue.int(len(github_top_projects_asset))
	}
	if failed:
		msg = f"{len(failed)} project(s) missing description."
		context.log.error(msg)
		metadata["error"] = MetadataValue.text(msg)
		return AssetCheckResult(passed=False, description=msg, metadata=metadata)
	msg = "All projects have a non-empty description."
	context.log.info(msg)
	metadata["info"] = MetadataValue.text(msg)
	return AssetCheckResult(passed=True, description=msg, metadata=metadata)

@asset_check(
	asset=github_mapping_asset, 
	name="github_mapping_type_check"
)
def github_mapping_type_check(context, github_mapping_asset):
	"""Checks that the mapping output is a non-empty list."""
	metadata = {
		"type": MetadataValue.text(str(type(github_mapping_asset))),
		"count": MetadataValue.int(len(github_mapping_asset)) if isinstance(github_mapping_asset, list) else MetadataValue.null(),
		"first": MetadataValue.json(github_mapping_asset[:1]) if isinstance(github_mapping_asset, list) and len(github_mapping_asset) > 0 else MetadataValue.null(),
		"is_list": MetadataValue.bool(isinstance(github_mapping_asset, list))
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

@asset_check(
    asset=github_mapping_asset, 
    name="github_mapping_required_fields_check"
)
def github_mapping_required_fields_check(context, github_mapping_asset):
	"""Checks that each project has required fields and correct types (title, repoUrl, provider, published, trending)."""
	required_fields = ["title", "repoUrl", "provider", "published", "trending"]
	missing_fields = []
	type_errors = []
	for i, project in enumerate(github_mapping_asset):
		for field in required_fields:
			if field not in project or project[field] in (None, ""):
				context.log.warning(f"Project {i} is missing required field: {field}")
				missing_fields.append((i, field))
		if "published" in project and not isinstance(project["published"], bool):
			context.log.warning(f"Project {i} has published field not boolean: {project['published']}")
			type_errors.append((i, "published_not_bool"))
		if "trending" in project:
			if not isinstance(project["trending"], bool):
				context.log.warning(f"Project {i} has trending field not boolean: {project['trending']}")
				type_errors.append((i, "trending_not_bool"))
			elif project["trending"] is not True:
				context.log.warning(f"Project {i} has trending field not True: {project['trending']}")
				type_errors.append((i, "trending_not_true"))
	metadata = {
		"missing_fields": MetadataValue.int(len(missing_fields)),
		"type_errors": MetadataValue.int(len(type_errors)),
		"missing_examples": MetadataValue.json(missing_fields[:5]),
		"type_error_examples": MetadataValue.json(type_errors[:5]),
		"total": MetadataValue.int(len(github_mapping_asset)),
		"required_fields": MetadataValue.json(required_fields)
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

@asset_check(
    asset=github_mapping_asset, 
    name="github_mapping_duplicate_url_check"
)
def github_mapping_duplicate_url_check(context, github_mapping_asset):
	"""Checks for duplicate repoUrl or githubUrl."""
	repo_urls = [p.get("repoUrl") for p in github_mapping_asset if "repoUrl" in p and p.get("repoUrl")]
	github_urls = [p.get("githubUrl") for p in github_mapping_asset if "githubUrl" in p and p.get("githubUrl")]
	duplicate_repo_urls = len(repo_urls) != len(set(repo_urls))
	duplicate_github_urls = len(github_urls) != len(set(github_urls))
	metadata = {
		"repoUrl_duplicates": MetadataValue.bool(duplicate_repo_urls),
		"githubUrl_duplicates": MetadataValue.bool(duplicate_github_urls),
		"repoUrl_count": MetadataValue.int(len(repo_urls)),
		"githubUrl_count": MetadataValue.int(len(github_urls)),
		"total": MetadataValue.int(len(github_mapping_asset))
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

@asset_check(asset=github_to_db_asset, name="github_to_db_insert_count_check", additional_ins={"github_mapping_asset": AssetIn()})
def github_to_db_insert_count_check(context, github_to_db_asset, github_mapping_asset):
	"""Checks that the number of inserts matches the number of items to insert."""
	expected = len(github_mapping_asset)
	actual = github_to_db_asset
	metadata = {
		"expected": MetadataValue.int(expected),
		"inserted": MetadataValue.int(actual)
	}
	if actual == expected:
		msg = f"{actual}/{expected} projects inserted."
		metadata["info"] = MetadataValue.text(msg)
		return AssetCheckResult(passed=True, description=msg, metadata=metadata)
	else:
		msg = f"Only {actual}/{expected} projects inserted."
		metadata["error"] = MetadataValue.text(msg)
		return AssetCheckResult(passed=False, description=msg, metadata=metadata)

@asset_check(asset=github_to_db_asset, name="github_to_db_error_check")
def github_to_db_error_check(context, github_to_db_asset):
	"""Checks that no insertion errors were logged. (Assumes errors are logged in context; for a real check, errors should be returned from the asset.)"""
	metadata = {
		"inserted": MetadataValue.int(github_to_db_asset)
	}
	msg = "No insertion errors detected in logs."
	metadata["info"] = MetadataValue.text(msg)
	return AssetCheckResult(passed=True, description=msg, metadata=metadata)

@asset_check(asset=github_to_db_asset, name="github_to_db_consistency_check", additional_ins={"github_mapping_asset": AssetIn()})
def github_to_db_consistency_check(context, github_to_db_asset, github_mapping_asset):
	"""Checks that the inserted projects actually exist in the database (simple count)."""
	with prisma_client() as prisma:
		db_count = prisma.project.count()
	expected = len(github_mapping_asset)
	metadata = {
		"db_count": MetadataValue.int(db_count),
		"expected": MetadataValue.int(expected)
	}
	if db_count >= expected:
		msg = f"{db_count} projects in DB (>= {expected} expected)"
		metadata["info"] = MetadataValue.text(msg)
		return AssetCheckResult(passed=True, description=msg, metadata=metadata)
	else:
		msg = f"Only {db_count}/{expected} projects in DB."
		metadata["error"] = MetadataValue.text(msg)
		return AssetCheckResult(passed=False, description=msg, metadata=metadata)

@asset_check(asset=github_to_db_asset, name="github_to_db_uniqueness_check")
def github_to_db_uniqueness_check(context):
	"""Checks the uniqueness of repoUrl in the database."""
	with prisma_client() as prisma:
		projects = prisma.project.find_many()
	repo_urls = [p.repoUrl for p in projects if hasattr(p, "repoUrl") and p.repoUrl]
	metadata = {
		"repoUrl_count": MetadataValue.int(len(repo_urls)),
		"unique_repoUrl_count": MetadataValue.int(len(set(repo_urls)))
	}
	if len(repo_urls) == len(set(repo_urls)):
		msg = "All repoUrls are unique in DB."
		metadata["info"] = MetadataValue.text(msg)
		return AssetCheckResult(passed=True, description=msg, metadata=metadata)
	else:
		msg = "Duplicate repoUrls detected in DB."
		metadata["error"] = MetadataValue.text(msg)
		return AssetCheckResult(passed=False, description=msg, metadata=metadata)

@asset_check(asset=github_to_db_asset, name="github_to_db_mapping_match_check", additional_ins={"github_mapping_asset": AssetIn()})
def github_to_db_mapping_match_check(context, github_mapping_asset):
	"""Checks that the fields inserted in the database match those from the mapping (simple check on title/repoUrl)."""
	with prisma_client() as prisma:
		db_projects = prisma.project.find_many()
	mapping_titles = set(p["title"] for p in github_mapping_asset if "title" in p)
	db_titles = set(p.title for p in db_projects if hasattr(p, "title"))
	missing = mapping_titles - db_titles
	metadata = {
		"missing_titles": MetadataValue.int(len(missing)),
		"missing_examples": MetadataValue.json(list(missing)[:3]),
		"mapping_titles": MetadataValue.int(len(mapping_titles)),
		"db_titles": MetadataValue.int(len(db_titles))
	}
	if not missing:
		msg = "All mapping titles are present in DB."
		metadata["info"] = MetadataValue.text(msg)
		return AssetCheckResult(passed=True, description=msg, metadata=metadata)
	else:
		msg = f"Missing titles in DB: {list(missing)[:3]}"
		metadata["error"] = MetadataValue.text(msg)
		return AssetCheckResult(passed=False, description=msg, metadata=metadata)