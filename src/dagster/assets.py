import os
from dagster import asset, MetadataValue, Output
import subprocess
import json

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

# ========================================
# GITHUB SCRAPER
# ========================================
@asset(
    kinds={"go", "github"},
    owners=DEFAULT_OWNERS,
    config_schema={"env_file": str}
)
def github_scraper_asset(context):
	"""Run the GitHub Go scraper and emit results as metadata."""
	env_file = context.op_config["env_file"]
	env = os.environ.copy()
	env["ENV_PATH"] = env_file
	try:
		result = subprocess.run([
			"go", "run", "src/infrastructure/services/go/github/main.go"
		], capture_output=True, text=True, check=True, env=env)
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
	except Exception as e:
		context.log.error(f"Erreur exécution scraper GitHub: {e}")
		return Output(value=[], metadata={"count": MetadataValue.int(0), "error": MetadataValue.text(str(e))})

# ========================================
# GITLAB SCRAPER
# ========================================
@asset(kinds={"go", "gitlab"}, owners=DEFAULT_OWNERS)
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
