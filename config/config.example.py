########################################
# CONFIGURATION MODULE - OST AI ENGINE (EXAMPLE
########################################

"""
This script generates a sample centralized configuration file
for the OST AI ENGINE project. Use it for onboarding, documentation,
or to validate the expected YAML structure.

DO NOT USE IN PRODUCTION OR COMMIT WITH SECRETS!
"""

import os
from datetime import date, timedelta
import yaml

config_dict = {
    "DATABASE_URL": "postgresql://user:pass@host:port/dbname",  # Expected format
    "GITHUB_TOP_N": 30,
    "GITHUB_ACCESS_TOKEN": "your_github_token_here",  # GitHub token
    "GITLAB_ACCESS_TOKEN": "your_gitlab_token_here",  # GitLab token
    "GITHUB_SCRAPING_QUERY": f"stars:>0 stars:<10000 created:>=YYYY-MM-DD is:public archived:false",  # Example query
    "GITHUB_SCRAPER_CRON": "0 * * * *",  # Example cron schedule for Dagster job
}

config_path = os.path.join(os.path.dirname(__file__), "config_example.yaml")
with open(config_path, "w") as f:
    f.write("""
############################################################
#  OST AI ENGINE - CENTRALIZED CONFIG (EXAMPLE)            #
#  This file is a sample to adapt for your usage.           #
############################################################

# ───────────────────────────────────────────────────────── #
# PostgreSQL database connection URL
# Format: postgresql://user:pass@host:port/dbname
DATABASE_URL: {}

# GitHub access token (create a token at https://github.com/settings/tokens)
GITHUB_ACCESS_TOKEN: {}

# GitLab access token (create a token at https://gitlab.com/-/profile/personal_access_tokens)
GITLAB_ACCESS_TOKEN: {}

# GitHub scraping query (see GitHub Search API docs)
GITHUB_SCRAPING_QUERY: {}

# Cron schedule for GitHub scraper Dagster job
GITHUB_SCRAPER_CRON: {}

# Number of top GitHub projects to fetch (integer)
GITHUB_TOP_N: {}
# ───────────────────────────────────────────────────────── #
""".format(
        config_dict["DATABASE_URL"],
        config_dict["GITHUB_ACCESS_TOKEN"],
        config_dict["GITLAB_ACCESS_TOKEN"],
        config_dict["GITHUB_SCRAPING_QUERY"],
        config_dict["GITHUB_SCRAPER_CRON"],
        config_dict["GITHUB_TOP_N"]
    ))