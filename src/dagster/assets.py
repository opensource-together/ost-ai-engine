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
		context.log.info(f"GitHub scraper: {count} projets scrapés.")
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
		kinds={"go", "python"},
        owners=DEFAULT_OWNERS, 
		ins={"github_scraper_asset": AssetIn()})
def github_mapping_asset(context, github_scraper_asset):
	"""Transform GitHub scraper output to match Prisma Project model using mapping config."""
	# Get the output from the GitHub scraper asset
	# This assumes the asset is used in a job with github_scraper_asset as an input
	scraped_repos = github_scraper_asset
	if scraped_repos is None:
		context.log.warning("No data found from github_scraper_asset. Returning empty list.")
		return []

	def map_repo(repo):
		mapped = {}
		for prisma_field, source in GITHUB_TO_PROJECT_MAPPING.items():
			if callable(source):
				mapped[prisma_field] = source(repo)
			elif isinstance(source, str) and "." in source:
				# For nested keys like "owner.avatar_url"
				keys = source.split(".")
				value = repo
				for k in keys:
					value = value.get(k, None) if isinstance(value, dict) else None
				mapped[prisma_field] = value
			elif isinstance(source, str):
				mapped[prisma_field] = repo.get(source)
			else:
				mapped[prisma_field] = source  # None ou valeur par défaut
		return mapped

	projects = [map_repo(repo) for repo in scraped_repos]

	return projects

@asset(
    owners=DEFAULT_OWNERS,
    ins={"github_mapping_asset": AssetIn()}
)
def github_to_db_asset(context, github_mapping_asset):
	"""Insert mapped projects into the Project table using Prisma Python client."""
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

@asset_check(
    asset=github_mapping_asset, 
    name="github_mapping_type_check"
)
def github_mapping_type_check(context, github_mapping_asset):
    """Check that the mapping output is a non-empty list."""
    if not isinstance(github_mapping_asset, list):
        context.log.error("Mapping output is not a list.")
        return AssetCheckResult(passed=False, description="Mapping output is not a list.")
    if len(github_mapping_asset) == 0:
        context.log.error("Mapping output is empty.")
        return AssetCheckResult(passed=False, description="Mapping output is empty.")
    context.log.info("Mapping output is a non-empty list.")
    return AssetCheckResult(passed=True, description="Mapping output is a non-empty list.")

@asset_check(
    asset=github_mapping_asset, 
    name="github_mapping_required_fields_check"
)
def github_mapping_required_fields_check(context, github_mapping_asset):
	"""Check that each project has required fields and correct types (title, repoUrl, provider, published, trending)."""
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
	if missing_fields or type_errors:
		msg = f"Missing or invalid required fields in {len(missing_fields)} project(s), type errors in {len(type_errors)} project(s): {missing_fields[:5]} {type_errors[:5]}"
		context.log.error(msg)
		return AssetCheckResult(passed=False, description=msg)
	context.log.info("All projects have required fields and correct types.")
	return AssetCheckResult(passed=True, description="All projects have required fields and correct types.")

@asset_check(
    asset=github_mapping_asset, 
    name="github_mapping_duplicate_url_check"
)
def github_mapping_duplicate_url_check(context, github_mapping_asset):
    """Check for duplicate repoUrl or githubUrl."""
    repo_urls = [p.get("repoUrl") for p in github_mapping_asset if "repoUrl" in p and p.get("repoUrl")]
    github_urls = [p.get("githubUrl") for p in github_mapping_asset if "githubUrl" in p and p.get("githubUrl")]
    duplicate_repo_urls = len(repo_urls) != len(set(repo_urls))
    duplicate_github_urls = len(github_urls) != len(set(github_urls))
    if duplicate_repo_urls or duplicate_github_urls:
        msg = "Duplicate repoUrl detected." if duplicate_repo_urls else ""
        if duplicate_github_urls:
            msg += " Duplicate githubUrl detected."
        context.log.error(msg)
        return AssetCheckResult(passed=False, description=msg.strip())
    context.log.info("No duplicate repoUrl or githubUrl detected.")
    return AssetCheckResult(passed=True, description="No duplicate repoUrl or githubUrl detected.")

# ========================================
# GITLAB SCRAPER
# ========================================

@asset(
		kinds={"go", "gitlab"}, 
		owners=DEFAULT_OWNERS
)
def gitlab_scraper_asset(context):
	"""Run the GitLab Go scraper and emit results as metadata."""
	try:
		result = subprocess.run([
			"go", "run", "src/infrastructure/services/go/gitlab/main.go"
		], capture_output=True, text=True, check=True)
		projects = json.loads(result.stdout)
		count = len(projects)
		context.log.info(f"GitLab scraper: {count} projets scrapés.")
		return Output(
			value=projects,
			metadata={
				"count": MetadataValue.int(count),
				"example": MetadataValue.text(str(projects[:1]))
			}
		)
	except Exception as e:
		context.log.error(f"Erreur exécution scraper GitLab: {e}")
		return Output(value=[], metadata={"count": MetadataValue.int(0)})
