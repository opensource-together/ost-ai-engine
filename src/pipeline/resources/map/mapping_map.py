# Centralized mappings for GitHub and GitLab scrapers to Prisma Project model
# Each mapping is a separate dict for clarity and maintainability

GITHUB_TO_PROJECT_MAPPING = {
    "title": "name",                     # GitHub repo name
    "description": "description",        # Repo description
    "repoUrl": "html_url",               # GitHub URL (repoUrl = html_url)
    "provider": lambda repo: "GITHUB",   # Provider type
    "githubUrl": "html_url",             # GitHub URL
    "gitlabUrl":  None,                  # Not available from GitHub scraper
    "twitterUrl": None,                  # Not available from GitHub scraper
    "linkedinUrl": None,                 # Not available from GitHub scraper
    "discordUrl": None,                  # Not available from GitHub scraper
    "websiteUrl": "homepage",            # Repo homepage
    "published": lambda repo: True,      # Always published (example)
    "trending": lambda repo: True,       # True by default because is trending projects
    "logoUrl": "owner.avatar_url",       # Owner avatar
    "imagesUrls": lambda repo: [],       # Fill as needed
    "createdAt": "created_at",           # Creation date
    "updatedAt": "updated_at",           # Update date
}

GITLAB_TO_PROJECT_MAPPING = {
    "title": "name",                           # Project name
    "description": "description",              # Project description
    "repoUrl": "web_url",                      # GitLab project URL
    "provider": lambda repo: "GITLAB",         # Provider type
    "githubUrl": None,                         # Not available from GitLab scraper
    "gitlabUrl": "web_url",                    # GitLab URL
    "twitterUrl": None,                        # Not available from GitLab scraper
    "linkedinUrl": None,                       # Not available from GitLab scraper
    "discordUrl": None,                        # Not available from GitLab scraper
    "websiteUrl": "homepage",                  # Project homepage (if set)
    "published": lambda repo: repo.get("visibility") == "public",  # Published if public
    "trending": None,                          # Not available from GitLab scraper
    "logoUrl": "avatar_url",                   # Project avatar (if available)
    "imagesUrls": lambda repo: [],             # Fill as needed
    "createdAt": "created_at",                 # Creation date
    "updatedAt": "last_activity_at",           # Last activity date
}
