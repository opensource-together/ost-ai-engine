
# Mapping between GitHub scraper fields and the Project model from Prisma schema
# Adapt the keys/values according to your needs and the structure of the scraper data.

GITHUB_TO_PROJECT_MAPPING = {
	# Project model key : source in the scraper dict
	"title": "name",  # GitHub repo name
	"description": "description",  # Repo description
	"repoUrl": "url",  # GitHub repo URL
	"githubUrl": "html_url",  # GitHub URL
	"websiteUrl": "homepage",  # Repo homepage
	"published": lambda repo: True,  # Always published (example)
    "trending": lambda repo: True,  # Default to True, set True because is trending projects
	"logoUrl": "owner.avatar_url",  # Owner avatar
	"imagesUrls": lambda repo: [],  # Fill as needed
	"createdAt": "created_at",  # Creation date
	"updatedAt": "updated_at",  # Update date
}
