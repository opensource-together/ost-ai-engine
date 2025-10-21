# Mapping between Gitlab scraper fields and the Project model from Prisma schema
# Adapt the keys/values according to your needs and the structure of the scraper data.

GITLAB_TO_PROJECT_MAPPING = {
    "title": "name",                          # Project name
    "description": "description",             # Project description
    "repoUrl": "web_url",                     # GitLab project URL
    "provider": lambda repo: "GITLAB",        # Provider type
    "githubUrl": None,                        
    "gitlabUrl": "web_url",                   # GitLab URL
    "twitterUrl": None,                        
    "linkedinUrl": None,                       
    "discordUrl": None,                        
    "websiteUrl": "homepage",                 # Project homepage (if set)
    "published": lambda repo: repo.get("visibility") == "public",  # Published if public
    "trending": None,                         
    "logoUrl": "avatar_url",                  # Project avatar (if available)
    "imagesUrls": lambda repo: [],            
    "createdAt": "created_at",                # Creation date
    "updatedAt": "last_activity_at",          # Last activity date
}