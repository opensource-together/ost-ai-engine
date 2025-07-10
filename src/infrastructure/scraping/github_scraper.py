from github import Github, GithubException, RateLimitExceededException

from src.infrastructure.config import settings


class GithubScraper:
    """
    A scraper to fetch repository data from the GitHub API.
    """

    def __init__(self):
        """
        Initializes the scraper with a GitHub API token.
        """
        self.github_api = Github(settings.GITHUB_ACCESS_TOKEN)

    def _format_repo_data(self, repo):
        """Helper function to format a PyGithub repository object into a dictionary."""
        try:
            readme_content = repo.get_readme().decoded_content.decode("utf-8")
        except GithubException:
            readme_content = "README not found or could not be decoded."

        return {
            "title": repo.full_name,
            "description": repo.description,
            "readme": readme_content,
            "topics": repo.get_topics(),
            "language": repo.language,
            "html_url": repo.html_url,
            "stargazers_count": repo.stargazers_count,
            "forks_count": repo.forks_count,
            "open_issues_count": repo.open_issues_count,
            "pushed_at": repo.pushed_at,
        }

    def get_repositories(self, query: str, limit: int = 20):
        """
        Fetches repositories from GitHub based on a search query.
        """
        print(f"Searching GitHub for repositories with query: '{query}' (limit: {limit})...")
        try:
            repos = self.github_api.search_repositories(query=query)

            repo_list = []
            for i, repo in enumerate(repos):
                if i >= limit:
                    break
                print(f"Scraping repository {i+1}/{limit}: {repo.full_name}")
                repo_list.append(self._format_repo_data(repo))

            print(f"Successfully fetched {len(repo_list)} repositories.")
            return repo_list

        except RateLimitExceededException:
            print("GitHub API rate limit exceeded. Please wait or use an access token.")
            return []
        except GithubException as e:
            print(f"An error occurred while fetching data from GitHub: {e}")
            return []

    def get_repositories_by_names(self, repo_names: list[str]):
        """
        Fetches a list of repositories directly by their names (e.g., 'owner/repo').
        """
        total_repos = len(repo_names)
        print(f"Fetching {total_repos} repositories by name...")
        repo_list = []
        
        for i, name in enumerate(repo_names, 1):
            try:
                print(f"Scraping repository {i}/{total_repos}: {name}")
                repo = self.github_api.get_repo(name)
                repo_list.append(self._format_repo_data(repo))
            except GithubException as e:
                print(f"Could not fetch repository '{name}': {e}")
                continue

        print(f"Successfully fetched {len(repo_list)}/{total_repos} repositories.")
        return repo_list

    def get_repository(self, repo_name: str):
        # This method is not provided in the original file or the refactored file
        # It's assumed to exist as it's called in the get_repositories_by_names method
        pass
