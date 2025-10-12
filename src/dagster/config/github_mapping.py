
# Example mapping between GitHub scraper fields and the Project model from Prisma schema
# You can adapt the keys/values according to your needs and the structure of the scraper data.

GITHUB_TO_PROJECT_MAPPING = {
	# Project model key : source in the scraper dict
	"title": "name",  # GitHub repo name
	"description": "description",  # Repo description
	"repoUrl": "html_url",  # GitHub repo URL
	"provider": lambda _: "GITHUB",  # Fixed value
	"githubUrl": "html_url",  # GitHub URL
	"websiteUrl": "homepage",  # Repo homepage
	"published": lambda repo: True,  # Always published (example)
	"owner": lambda repo: repo.get("owner", {}).get("login"),  # Owner login
	"logoUrl": "owner.avatar_url",  # Owner avatar
	"imagesUrls": lambda repo: [],  # Fill as needed
	"createdAt": "created_at",  # Creation date
	"updatedAt": "updated_at",  # Update date
	# Add other fields if needed
}
