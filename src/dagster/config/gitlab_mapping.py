# Mapping between Gitlab scraper fields and the Project model from Prisma schema
# Adapt the keys/values according to your needs and the structure of the scraper data.

GITLAB_TO_PROJECT_MAPPING = {
    "githubUsername": "namespace.path",       # Namespace (group/user) identifier (GitLab equivalent)
    "title": "name",                          # Project name
    "description": "description",             # Project description
    "repoUrl": "web_url",                     # GitLab project URL
    "provider": lambda repo: "GITLAB",        # Provider type
    "githubUrl": None,                        # Not available from GitLab scraper
    "gitlabUrl": "web_url",                   # GitLab URL
    "twitterUrl": None,                       # Not available from GitLab scraper
    "linkedinUrl": None,                      # Not available from GitLab scraper
    "discordUrl": None,                       # Not available from GitLab scraper
    "websiteUrl": "homepage",                 # Project homepage (if set)
    "published": lambda repo: repo.get("visibility") == "public",  # Published if public
    "trending": None,                         # Not available from GitLab scraper
    "logoUrl": "avatar_url",                  # Project avatar (if available)
    "imagesUrls": lambda repo: [],            # Fill as needed
    "createdAt": "created_at",                # Creation date
    "updatedAt": "last_activity_at",          # Last activity date
}