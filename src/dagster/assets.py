from dagster import asset, MetadataValue

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

# ========================================
# GITHUB SCRAPER
# ========================================
@asset(kinds={"go", "github"}, owners=DEFAULT_OWNERS)
def github_scraper_asset(context):
	"""Run the GitHub Go scraper and emit results as metadata."""
	# Example: run the Go scraper via subprocess or API
	# result = run_github_scraper()
	# context.add_output_metadata({"result": MetadataValue.text(str(result))})
	context.log.info("GitHub scraper executed.")
	return "GitHub scraper result"

# ========================================
# GITLAB SCRAPER
# ========================================
@asset(kinds={"go", "gitlab"}, owners=DEFAULT_OWNERS)
def gitlab_scraper_asset(context):
	"""Run the GitLab Go scraper and emit results as metadata."""
	# Example: run the Go scraper via subprocess or API
	# result = run_gitlab_scraper()
	# context.add_output_metadata({"result": MetadataValue.text(str(result))})
	context.log.info("GitLab scraper executed.")
	return "GitLab scraper result"
