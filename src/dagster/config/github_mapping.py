# Mapping between GitHub scraper fields and the Project model from Prisma schema
# Adapt the keys/values according to your needs and the structure of the scraper data.

GITHUB_TO_PROJECT_MAPPING = {
	"githubUsername": "owner.login",    # Github name of owner
	"title": "name",                    # GitHub repo name
	"description": "description",       # Repo description
	"repoUrl": "html_url",  			# GitHub URL (repoUrl = html_url)
	"provider": lambda repo: "GITHUB",  # Provider type
	"githubUrl": "html_url",  			# GitHub URL
	"gitlabUrl":  None,  				# Not available from GitHub scraper
	"twitterUrl": None,  				# Not available from GitHub scraper
	"linkedinUrl": None,  				# Not available from GitHub scraper
	"discordUrl": None,  				# Not available from GitHub scraper
	"websiteUrl": "homepage",  			# Repo homepage
	"published": lambda repo: True,  	# Always published (example)
	"trending": lambda repo: True,  	# True by default because is trending projects
	"logoUrl": "owner.avatar_url",  	# Owner avatar
	"imagesUrls": lambda repo: [],  	# Fill as needed
	"createdAt": "created_at",  		# Creation date
	"updatedAt": "updated_at",  		# Update date
}