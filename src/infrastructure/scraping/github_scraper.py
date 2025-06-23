import os
from github import Github, GithubException, RateLimitExceededException
from dotenv import load_dotenv

# Load environment variables at the module level
load_dotenv()


class GithubScraper:
    """
    A scraper to fetch repository data from GitHub.
    """

    def __init__(self):
        """
        Initializes the scraper by connecting to the GitHub API.
        """
        self.github_token = os.getenv("GITHUB_ACCESS_TOKEN")
        if not self.github_token:
            raise ValueError("GITHUB_ACCESS_TOKEN is not set in the .env file.")
        self.github_api = Github(self.github_token)

    def _format_repo_data(self, repo):
        """Helper function to format a PyGithub repository object into a dictionary."""
        try:
            readme_content = repo.get_readme().decoded_content.decode("utf-8")
        except GithubException:
            readme_content = "README not found or could not be decoded."

        return {
            "title": repo.name,
            "description": repo.description or "No description provided.",
            "readme": readme_content,
            "topics": repo.get_topics(),
            "language": repo.language,
            "html_url": repo.html_url,
            "stargazers_count": repo.stargazers_count,
            "forks_count": repo.forks_count,
            "open_issues_count": repo.open_issues_count,
            "pushed_at": repo.pushed_at,
        }

    def get_repositories(
        self, query: str = "language:python stars:>1000", limit: int = 50
    ):
        """
        Fetches a list of repositories matching a search query.

        Args:
            query (str): The GitHub search query.
            limit (int): The maximum number of repositories to fetch.

        Returns:
            list: A list of dictionaries containing repository data.
        """
        print(f"Searching GitHub for repositories with query: '{query}'...")
        try:
            repos = self.github_api.search_repositories(query=query)

            repo_list = []
            for i, repo in enumerate(repos):
                if i >= limit:
                    break
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
        Fetches a list of specific repositories by their full names (e.g., 'owner/repo').

        Args:
            repo_names (list[str]): A list of repository full names.

        Returns:
            list: A list of dictionaries containing repository data.
        """
        print(f"Fetching {len(repo_names)} specific repositories from GitHub...")
        repo_list = []
        for name in repo_names:
            try:
                repo = self.github_api.get_repo(name)
                repo_list.append(self._format_repo_data(repo))
            except GithubException as e:
                print(f"Could not fetch repository '{name}': {e}")
                continue

        print(f"Successfully fetched {len(repo_list)} repositories.")
        return repo_list
