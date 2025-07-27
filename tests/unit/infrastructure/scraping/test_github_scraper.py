"""
Unit tests for GitHub scraper infrastructure.

Tests critical production functionality: configuration, rate limiting,
data formatting, error handling, and API responses.
"""

import pytest
from unittest.mock import patch, MagicMock
from github import Github, GithubException, RateLimitExceededException

from src.infrastructure.scraping.github_scraper import GithubScraper


class TestGithubScraperConfiguration:
    """Test critical configuration for production."""

    @patch('src.infrastructure.scraping.github_scraper.settings')
    def test_initializes_with_github_token(self, mock_settings):
        """Test that scraper initializes with GitHub access token."""
        mock_settings.GITHUB_ACCESS_TOKEN = "test_token_123"
        
        with patch('src.infrastructure.scraping.github_scraper.Github') as mock_github:
            scraper = GithubScraper()
            
            # Should initialize Github API with token
            mock_github.assert_called_once_with("test_token_123")
            assert scraper.github_api is not None

    @patch('src.infrastructure.scraping.github_scraper.settings')
    def test_github_api_initialization(self, mock_settings):
        """Test that GitHub API is properly initialized."""
        mock_settings.GITHUB_ACCESS_TOKEN = "test_token"
        
        with patch('src.infrastructure.scraping.github_scraper.Github') as mock_github:
            mock_github_instance = MagicMock()
            mock_github.return_value = mock_github_instance
            
            scraper = GithubScraper()
            
            assert scraper.github_api == mock_github_instance


class TestGithubScraperDataFormatting:
    """Test critical data formatting for ML pipeline."""

    def setup_method(self):
        """Setup test fixtures."""
        with patch('src.infrastructure.scraping.github_scraper.settings') as mock_settings:
            mock_settings.GITHUB_ACCESS_TOKEN = "test_token"
            with patch('src.infrastructure.scraping.github_scraper.Github'):
                self.scraper = GithubScraper()

    def test_format_repo_data_structure(self):
        """Test that formatted repo data has required structure for ML."""
        mock_repo = MagicMock()
        mock_repo.full_name = "owner/repo"
        mock_repo.description = "Test description"
        mock_repo.language = "Python"
        mock_repo.html_url = "https://github.com/owner/repo"
        mock_repo.stargazers_count = 100
        mock_repo.forks_count = 50
        mock_repo.open_issues_count = 10
        mock_repo.pushed_at = "2023-01-01T00:00:00Z"
        mock_repo.get_topics.return_value = ["python", "ml"]
        
        # Mock README
        mock_readme = MagicMock()
        mock_readme.decoded_content.decode.return_value = "# Test README"
        mock_repo.get_readme.return_value = mock_readme
        
        result = self.scraper._format_repo_data(mock_repo)
        
        # Required fields for ML pipeline
        required_fields = [
            'title', 'description', 'readme', 'topics', 'language',
            'html_url', 'stargazers_count', 'forks_count', 
            'open_issues_count', 'pushed_at'
        ]
        
        for field in required_fields:
            assert field in result, f"Required field '{field}' missing"
        
        # Check data types
        assert isinstance(result['title'], str)
        assert isinstance(result['description'], str) or result['description'] is None
        assert isinstance(result['readme'], str)
        assert isinstance(result['topics'], list)
        assert isinstance(result['stargazers_count'], int)
        assert isinstance(result['forks_count'], int)
        assert isinstance(result['open_issues_count'], int)

    def test_format_repo_data_readme_error_handling(self):
        """Test that README errors don't break data formatting."""
        mock_repo = MagicMock()
        mock_repo.full_name = "owner/repo"
        mock_repo.description = "Test description"
        mock_repo.language = "Python"
        mock_repo.html_url = "https://github.com/owner/repo"
        mock_repo.stargazers_count = 100
        mock_repo.forks_count = 50
        mock_repo.open_issues_count = 10
        mock_repo.pushed_at = "2023-01-01T00:00:00Z"
        mock_repo.get_topics.return_value = ["python"]
        
        # Mock README error
        mock_repo.get_readme.side_effect = GithubException(404, "README not found")
        
        result = self.scraper._format_repo_data(mock_repo)
        
        # Should still return data with fallback README
        assert result['readme'] == "README not found or could not be decoded."
        assert result['title'] == "owner/repo"
        assert result['description'] == "Test description"


class TestGithubScraperErrorHandling:
    """Test critical error handling for production."""

    def setup_method(self):
        """Setup test fixtures."""
        with patch('src.infrastructure.scraping.github_scraper.settings') as mock_settings:
            mock_settings.GITHUB_ACCESS_TOKEN = "test_token"
            with patch('src.infrastructure.scraping.github_scraper.Github') as mock_github:
                self.mock_github_api = MagicMock()
                mock_github.return_value = self.mock_github_api
                self.scraper = GithubScraper()

    def test_rate_limit_exceeded_handling(self):
        """Test handling of GitHub API rate limit exceeded."""
        self.mock_github_api.search_repositories.side_effect = RateLimitExceededException(
            403, "API rate limit exceeded"
        )
        
        result = self.scraper.get_repositories("python", limit=10)
        
        # Should return empty list on rate limit
        assert result == []

    def test_github_exception_handling(self):
        """Test handling of general GitHub API errors."""
        self.mock_github_api.search_repositories.side_effect = GithubException(
            500, "Internal server error"
        )
        
        result = self.scraper.get_repositories("python", limit=10)
        
        # Should return empty list on API error
        assert result == []

    def test_individual_repo_error_handling(self):
        """Test that individual repo errors don't break batch fetching."""
        # Mock successful search
        mock_search = MagicMock()
        mock_repo1 = MagicMock()
        mock_repo1.full_name = "owner/repo1"
        mock_repo1.description = "Repo 1"
        mock_repo1.language = "Python"
        mock_repo1.html_url = "https://github.com/owner/repo1"
        mock_repo1.stargazers_count = 100
        mock_repo1.forks_count = 50
        mock_repo1.open_issues_count = 10
        mock_repo1.pushed_at = "2023-01-01T00:00:00Z"
        mock_repo1.get_topics.return_value = ["python"]
        
        # Mock README for successful repo
        mock_readme1 = MagicMock()
        mock_readme1.decoded_content.decode.return_value = "# Repo 1 README"
        mock_repo1.get_readme.return_value = mock_readme1
        
        # Mock failed repo
        mock_repo2 = MagicMock()
        mock_repo2.get_readme.side_effect = GithubException(404, "Not found")
        mock_repo2.full_name = "owner/repo2"
        mock_repo2.description = "Repo 2"
        mock_repo2.language = "Python"
        mock_repo2.html_url = "https://github.com/owner/repo2"
        mock_repo2.stargazers_count = 200
        mock_repo2.forks_count = 100
        mock_repo2.open_issues_count = 20
        mock_repo2.pushed_at = "2023-01-01T00:00:00Z"
        mock_repo2.get_topics.return_value = ["python"]
        
        mock_search.__iter__.return_value = [mock_repo1, mock_repo2]
        self.mock_github_api.search_repositories.return_value = mock_search
        
        result = self.scraper.get_repositories("python", limit=2)
        
        # Should return both repos, with fallback README for failed one
        assert len(result) == 2
        assert result[0]['title'] == "owner/repo1"
        assert result[1]['title'] == "owner/repo2"
        assert result[1]['readme'] == "README not found or could not be decoded."


class TestGithubScraperSearchFunctionality:
    """Test critical search functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        with patch('src.infrastructure.scraping.github_scraper.settings') as mock_settings:
            mock_settings.GITHUB_ACCESS_TOKEN = "test_token"
            with patch('src.infrastructure.scraping.github_scraper.Github') as mock_github:
                self.mock_github_api = MagicMock()
                mock_github.return_value = self.mock_github_api
                self.scraper = GithubScraper()

    def test_search_repositories_with_limit(self):
        """Test that search respects the limit parameter."""
        # Mock search results
        mock_search = MagicMock()
        mock_repos = []
        for i in range(5):
            mock_repo = MagicMock()
            mock_repo.full_name = f"owner/repo{i}"
            mock_repo.description = f"Repo {i}"
            mock_repo.language = "Python"
            mock_repo.html_url = f"https://github.com/owner/repo{i}"
            mock_repo.stargazers_count = 100 + i
            mock_repo.forks_count = 50 + i
            mock_repo.open_issues_count = 10 + i
            mock_repo.pushed_at = "2023-01-01T00:00:00Z"
            mock_repo.get_topics.return_value = ["python"]
            
            mock_readme = MagicMock()
            mock_readme.decoded_content.decode.return_value = f"# Repo {i} README"
            mock_repo.get_readme.return_value = mock_readme
            
            mock_repos.append(mock_repo)
        
        mock_search.__iter__.return_value = mock_repos
        self.mock_github_api.search_repositories.return_value = mock_search
        
        result = self.scraper.get_repositories("python", limit=3)
        
        # Should return only 3 repos due to limit
        assert len(result) == 3
        assert result[0]['title'] == "owner/repo0"
        assert result[1]['title'] == "owner/repo1"
        assert result[2]['title'] == "owner/repo2"

    def test_get_repositories_by_names(self):
        """Test fetching repositories by specific names."""
        repo_names = ["owner/repo1", "owner/repo2"]
        
        # Mock individual repo fetching
        mock_repo1 = MagicMock()
        mock_repo1.full_name = "owner/repo1"
        mock_repo1.description = "Repo 1"
        mock_repo1.language = "Python"
        mock_repo1.html_url = "https://github.com/owner/repo1"
        mock_repo1.stargazers_count = 100
        mock_repo1.forks_count = 50
        mock_repo1.open_issues_count = 10
        mock_repo1.pushed_at = "2023-01-01T00:00:00Z"
        mock_repo1.get_topics.return_value = ["python"]
        
        mock_readme1 = MagicMock()
        mock_readme1.decoded_content.decode.return_value = "# Repo 1 README"
        mock_repo1.get_readme.return_value = mock_readme1
        
        mock_repo2 = MagicMock()
        mock_repo2.full_name = "owner/repo2"
        mock_repo2.description = "Repo 2"
        mock_repo2.language = "JavaScript"
        mock_repo2.html_url = "https://github.com/owner/repo2"
        mock_repo2.stargazers_count = 200
        mock_repo2.forks_count = 100
        mock_repo2.open_issues_count = 20
        mock_repo2.pushed_at = "2023-01-01T00:00:00Z"
        mock_repo2.get_topics.return_value = ["javascript"]
        
        mock_readme2 = MagicMock()
        mock_readme2.decoded_content.decode.return_value = "# Repo 2 README"
        mock_repo2.get_readme.return_value = mock_readme2
        
        self.mock_github_api.get_repo.side_effect = [mock_repo1, mock_repo2]
        
        result = self.scraper.get_repositories_by_names(repo_names)
        
        # Should return both repos
        assert len(result) == 2
        assert result[0]['title'] == "owner/repo1"
        assert result[1]['title'] == "owner/repo2"
        assert result[0]['language'] == "Python"
        assert result[1]['language'] == "JavaScript"

    def test_get_repositories_by_names_with_errors(self):
        """Test that individual repo errors don't break batch fetching."""
        repo_names = ["owner/repo1", "owner/repo2", "owner/repo3"]
        
        # Mock successful repo
        mock_repo1 = MagicMock()
        mock_repo1.full_name = "owner/repo1"
        mock_repo1.description = "Repo 1"
        mock_repo1.language = "Python"
        mock_repo1.html_url = "https://github.com/owner/repo1"
        mock_repo1.stargazers_count = 100
        mock_repo1.forks_count = 50
        mock_repo1.open_issues_count = 10
        mock_repo1.pushed_at = "2023-01-01T00:00:00Z"
        mock_repo1.get_topics.return_value = ["python"]
        
        mock_readme1 = MagicMock()
        mock_readme1.decoded_content.decode.return_value = "# Repo 1 README"
        mock_repo1.get_readme.return_value = mock_readme1
        
        # Mock failed repos
        self.mock_github_api.get_repo.side_effect = [
            mock_repo1,  # Success
            GithubException(404, "Repo not found"),  # Error
            GithubException(403, "Access denied")  # Error
        ]
        
        result = self.scraper.get_repositories_by_names(repo_names)
        
        # Should return only successful repos
        assert len(result) == 1
        assert result[0]['title'] == "owner/repo1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
