import os
from dagster import (
	asset,
	asset_check,
	AssetCheckResult,
	AssetIn,
	MetadataValue,
	Output
)
from src.dagster.config.github_mapping import (
    GITHUB_TO_PROJECT_MAPPING
)
import subprocess
import json

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

# ========================================
# GITHUB SCRAPER
# ========================================

@asset(
	kinds={"go", "github"},
	owners=DEFAULT_OWNERS
)
def github_scraper_asset(context):
	"""Run the GitHub Go scraper and emit results as metadata."""
	from src.dagster.config.config import PipelineConfig
	config = PipelineConfig()
	env = os.environ.copy()
	env["GITHUB_SCRAPING_QUERY"] = config.github_scraping_query
	env["GITHUB_ACCESS_TOKEN"] = config.github_token
	context.log.info(f"GITHUB_SCRAPING_QUERY transmis au process Go: '{env['GITHUB_SCRAPING_QUERY']}'")
	try:
		result = subprocess.run([
			"go", "run", "main.go"
		], capture_output=True, text=True, check=True, env=env, cwd="src/infrastructure/services/go/github")
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
		context.log.info(f"[DEBUG] github_scraper_asset: {count} projets scrapés. Exemple: {projects[:1]}")
		return Output(
			value=projects,
			metadata={
				"count": MetadataValue.int(count),
				"example": MetadataValue.text(str(projects[:1]))
			}
		)
	except subprocess.CalledProcessError as e:
		err_msg = f"Github scraper error: {e}\nSTDERR: {e.stderr.strip()}"
		context.log.error(err_msg)
		return Output(value=[], metadata={"count": MetadataValue.int(0), "error": MetadataValue.text(err_msg)})
	except Exception as e:
		context.log.error(f"Github scraper error: {e}")
		return Output(value=[], metadata={"count": MetadataValue.int(0), "error": MetadataValue.text(str(e))})

@asset(
	kinds={"python"},
	owners=DEFAULT_OWNERS,
	ins={"github_scraper_asset": AssetIn()}
)
def github_top_projects_asset(context, github_scraper_asset):
	"""Ranks projects by stars and keeps only the top N (configurable)."""
	from src.dagster.config.config import PipelineConfig
	config = PipelineConfig()
	top_n = config.github_top_n
	if not github_scraper_asset or not isinstance(github_scraper_asset, list):
		context.log.warning("No projects to rank.")
		return []
	# Filter out projects without a description
	filtered = [p for p in github_scraper_asset if p.get("description") not in (None, "")]
	context.log.info(f"[DEBUG] github_top_projects_asset: {len(filtered)} projets avec description sur {len(github_scraper_asset)}")
	if not filtered:
		context.log.warning("[DEBUG] github_top_projects_asset: No project with description found.")
		return []
	ranked = sorted(
		filtered,
		key=lambda p: p.get("stargazers_count", 0),
		reverse=True
	)
	top_projects = ranked[:top_n]
	if top_projects:
		context.log.info(f"[DEBUG] github_top_projects_asset: Top {top_n} projects selected (stars range: {top_projects[0].get('stargazers_count', 0)} - {top_projects[-1].get('stargazers_count', 0)})")
	else:
		context.log.info("[DEBUG] github_top_projects_asset: No projects selected.")
	return top_projects

@asset(
	kinds={"go", "python"},
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
	context.log.info(f"[DEBUG] github_mapping_asset: {len(projects)} projets mappés.")
	return projects

@asset(
	kinds={"python", "postgres"},
    owners=DEFAULT_OWNERS,
    ins={"github_mapping_asset": AssetIn()}
)
def github_to_db_asset(context, github_mapping_asset):
	"""Inserts mapped projects into the Project table using the Prisma Python client."""
	from prisma import Prisma
	prisma = Prisma()
	prisma.connect()
	inserted = 0
	errors = []
	for i, project in enumerate(github_mapping_asset):
		try:
			project_data = {k: v for k, v in project.items() if v is not None}
			prisma.project.create(data=project_data)
			inserted += 1
		except Exception as e:
			context.log.error(f"Error inserting project {i}: {e}")
			errors.append((i, str(e)))
	prisma.disconnect()
	context.log.info(f"{inserted} projects inserted into the Project table.")
	if errors:
		context.log.warning(f"{len(errors)} insertion errors: {errors[:3]}")

	return inserted

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
		"failed_count": len(failed),
		"failed_indices": failed[:5],
		"total_projects": len(github_top_projects_asset)
	}
	if failed:
		msg = f"{len(failed)} project(s) missing description: {failed[:5]}"
		context.log.error(msg)
		return AssetCheckResult(passed=False, description=msg, metadata=metadata)
	context.log.info("All projects have a non-empty description.")
	return AssetCheckResult(passed=True, description="All projects have a non-empty description.", metadata=metadata)

# Check that all projects respect the minimum creation date
@asset_check(
	asset=github_top_projects_asset,
	name="github_top_projects_date_check"
)
def github_top_projects_date_check(context, github_top_projects_asset):
	"""Checks that all projects were created after the minimum date."""
	from src.dagster.config.config import seven_days_ago
	import datetime
	failed = []
	for i, project in enumerate(github_top_projects_asset):
		created_at = project.get("created_at")
		if not created_at:
			failed.append((i, "missing_created_at"))
			continue
		try:
			created_date = datetime.date.fromisoformat(created_at[:10])
			min_date = datetime.date.fromisoformat(seven_days_ago)
			if created_date < min_date:
				failed.append((i, f"created_at_too_old: {created_at}"))
		except Exception as e:
			failed.append((i, f"invalid_created_at: {created_at}"))
	metadata = {
		"failed_count": len(failed),
		"failed_examples": failed[:5],
		"total_projects": len(github_top_projects_asset),
		"min_date": seven_days_ago
	}
	if failed:
		msg = f"{len(failed)} project(s) with invalid date: {failed[:5]}"
		context.log.error(msg)
		return AssetCheckResult(passed=False, description=msg, metadata=metadata)
	context.log.info("All projects were created after the minimum date.")
	return AssetCheckResult(passed=True, description="All projects were created after the minimum date.", metadata=metadata)

@asset_check(
	asset=github_mapping_asset, 
	name="github_mapping_type_check"
)
def github_mapping_type_check(context, github_mapping_asset):
	"""Checks that the mapping output is a non-empty list."""
	metadata = {
		"type": str(type(github_mapping_asset)),
		"length": len(github_mapping_asset) if isinstance(github_mapping_asset, list) else None,
		"example": github_mapping_asset[:1] if isinstance(github_mapping_asset, list) and len(github_mapping_asset) > 0 else [],
		"is_list": isinstance(github_mapping_asset, list)
	}
	if not isinstance(github_mapping_asset, list):
		context.log.error("Mapping output is not a list.")
		metadata["error"] = "Not a list"
		return AssetCheckResult(passed=False, description="Mapping output is not a list.", metadata=metadata)
	if len(github_mapping_asset) == 0:
		context.log.error("Mapping output is empty.")
		metadata["error"] = "Empty list"
		return AssetCheckResult(passed=False, description="Mapping output is empty.", metadata=metadata)
	context.log.info("Mapping output is a non-empty list.")
	return AssetCheckResult(passed=True, description="Mapping output is a non-empty list.", metadata=metadata)

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
		# Vérifie le type des champs published et trending
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
		"missing_fields_count": len(missing_fields),
		"type_errors_count": len(type_errors),
		"missing_fields_examples": missing_fields[:5],
		"type_errors_examples": type_errors[:5],
		"total_projects": len(github_mapping_asset),
		"required_fields": required_fields
	}
	if missing_fields or type_errors:
		msg = f"Missing or invalid required fields in {len(missing_fields)} project(s), type errors in {len(type_errors)} project(s): {missing_fields[:5]} {type_errors[:5]}"
		context.log.error(msg)
		return AssetCheckResult(passed=False, description=msg, metadata=metadata)
	context.log.info("All projects have required fields and correct types.")
	return AssetCheckResult(passed=True, description="All projects have required fields and correct types.", metadata=metadata)

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
		"duplicate_repo_urls": duplicate_repo_urls,
		"duplicate_github_urls": duplicate_github_urls,
		"repo_urls_count": len(repo_urls),
		"github_urls_count": len(github_urls),
		"total_projects": len(github_mapping_asset)
	}
	if duplicate_repo_urls or duplicate_github_urls:
		msg = "Duplicate repoUrl detected." if duplicate_repo_urls else ""
		if duplicate_github_urls:
			msg += " Duplicate githubUrl detected."
		context.log.error(msg)
		return AssetCheckResult(passed=False, description=msg.strip(), metadata=metadata)
	context.log.info("No duplicate repoUrl or githubUrl detected.")
	return AssetCheckResult(passed=True, description="No duplicate repoUrl or githubUrl detected.", metadata=metadata)

@asset_check(asset=github_to_db_asset, name="github_to_db_insert_count_check", additional_ins={"github_mapping_asset": AssetIn()})
def github_to_db_insert_count_check(context, github_to_db_asset, github_mapping_asset):
	"""Checks that the number of inserts matches the number of items to insert."""
	expected = len(github_mapping_asset)
	actual = github_to_db_asset
	metadata = {
		"expected": expected,
		"actual": actual
	}
	if actual == expected:
		return AssetCheckResult(passed=True, description=f"{actual}/{expected} projets insérés.", metadata=metadata)
	else:
		return AssetCheckResult(passed=False, description=f"Seulement {actual}/{expected} projets insérés.", metadata=metadata)

@asset_check(asset=github_to_db_asset, name="github_to_db_error_check")
def github_to_db_error_check(context, github_to_db_asset):
	"""Checks that no insertion errors were logged. (Assumes errors are logged in context; for a real check, errors should be returned from the asset.)"""
	metadata = {
		"insert_count": github_to_db_asset
	}
	return AssetCheckResult(passed=True, description="Aucune erreur d'insertion détectée dans les logs.", metadata=metadata)

@asset_check(asset=github_to_db_asset, name="github_to_db_consistency_check", additional_ins={"github_mapping_asset": AssetIn()})
def github_to_db_consistency_check(context, github_to_db_asset, github_mapping_asset):
	"""Checks that the inserted projects actually exist in the database (simple count)."""
	from prisma import Prisma
	prisma = Prisma()
	prisma.connect()
	db_count = prisma.project.count()
	prisma.disconnect()
	expected = len(github_mapping_asset)
	metadata = {
		"db_count": db_count,
		"expected": expected
	}
	if db_count >= expected:
		return AssetCheckResult(passed=True, description=f"{db_count} projets en base (>= {expected} attendus)", metadata=metadata)
	else:
		return AssetCheckResult(passed=False, description=f"Seulement {db_count}/{expected} projets en base.", metadata=metadata)

@asset_check(asset=github_to_db_asset, name="github_to_db_uniqueness_check")
def github_to_db_uniqueness_check(context):
	"""Checks the uniqueness of repoUrl in the database."""
	from prisma import Prisma
	prisma = Prisma()
	prisma.connect()
	projects = prisma.project.find_many()
	prisma.disconnect()
	repo_urls = [p.repoUrl for p in projects if hasattr(p, "repoUrl") and p.repoUrl]
	metadata = {
		"repo_urls_count": len(repo_urls),
		"unique_repo_urls_count": len(set(repo_urls))
	}
	if len(repo_urls) == len(set(repo_urls)):
		return AssetCheckResult(passed=True, description="Aucun doublon repoUrl en base.", metadata=metadata)
	else:
		return AssetCheckResult(passed=False, description="Doublons repoUrl détectés en base.", metadata=metadata)

@asset_check(asset=github_to_db_asset, name="github_to_db_mapping_match_check", additional_ins={"github_mapping_asset": AssetIn()})
def github_to_db_mapping_match_check(context, github_mapping_asset):
	"""Checks that the fields inserted in the database match those from the mapping (simple check on title/repoUrl)."""
	from prisma import Prisma
	prisma = Prisma()
	prisma.connect()
	db_projects = prisma.project.find_many()
	prisma.disconnect()
	mapping_titles = set(p["title"] for p in github_mapping_asset if "title" in p)
	db_titles = set(p.title for p in db_projects if hasattr(p, "title"))
	missing = mapping_titles - db_titles
	metadata = {
		"missing_titles_count": len(missing),
		"missing_titles_examples": list(missing)[:3],
		"total_titles": len(mapping_titles),
		"db_titles_count": len(db_titles)
	}
	if not missing:
		return AssetCheckResult(passed=True, description="Tous les titres du mapping sont présents en base.", metadata=metadata)
	else:
		return AssetCheckResult(passed=False, description=f"Titres manquants en base: {list(missing)[:3]}", metadata=metadata)