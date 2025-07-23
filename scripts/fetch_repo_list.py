#!/usr/bin/env python3
"""
Temporary script to fetch a list of GitHub repositories and format them 
for the GITHUB_REPO_LIST environment variable.

Usage:
    python scripts/fetch_repo_list.py --count 100 --languages python,javascript,go
    python scripts/fetch_repo_list.py --count 50 --topics machine-learning,web-development
"""

import argparse
import random
from datetime import datetime, timedelta
import os
import sys
import time

from dotenv import load_dotenv
from github import Github, GithubException, RateLimitExceededException

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.config import settings


def fetch_repositories_by_language(github_api, language, count, min_stars):
    """Fetches a list of repository names for a given language."""
    print(f"Searching: language:{language} stars:>{min_stars}")
    query = f"language:{language} stars:>{min_stars}"

    try:
        search_results = github_api.search_repositories(query=query, sort="stars", order="desc")
        # Get more than needed to allow for filtering duplicates later
        repo_list = list(search_results[:count])
    except GithubException as e:
        if e.status == 403:
            print(
                f"WARN: GitHub API rate limit hit for query '{query}'. "
                "The script will continue, but the total number of repos might be lower. "
                "Waiting 60s before next request..."
            )
            time.sleep(60)
            return []  # Return empty list for this language
        else:
            print(f"ERROR: An unexpected GitHub API error occurred: {e}")
            return []
    except IndexError:
        # This can happen if the API returns an empty result set after a 403
        print(f"WARN: Caught an IndexError, likely from an empty API response for query '{query}'.")
        return []

    if len(repo_list) < count:
        print(f"Warning: Found only {len(repo_list)} repositories for {language} (less than requested {count}).")
    
    return [repo.full_name for repo in repo_list]


def fetch_repositories_by_topic(github_api, topic: str, count: int, min_stars: int = 50):
    """Fetch repositories for a specific topic."""
    repos = []
    try:
        query = f"topic:{topic} stars:>{min_stars}"
        print(f"Searching: {query}")
        
        search_results = github_api.search_repositories(query=query)
        
        # Take a random sample from results
        repo_list = list(search_results[:min(200, count * 3)])
        random.shuffle(repo_list)
        
        for repo in repo_list[:count]:
            repos.append(repo.full_name)
            
    except (GithubException, RateLimitExceededException) as e:
        print(f"Error fetching {topic} repos: {e}")
    
    return repos


def fetch_trending_repositories(github_api, count: int):
    """Fetch recently updated repositories."""
    repos = []
    try:
        # Repositories updated in the last 30 days
        recent_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        languages = ["python", "javascript", "typescript", "go", "rust"]
        
        for language in languages:
            if len(repos) >= count:
                break
                
            query = f"language:{language} pushed:>{recent_date} stars:>100"
            print(f"Searching trending: {query}")
            
            search_results = github_api.search_repositories(query=query)
            
            repo_list = list(search_results[:50])
            random.shuffle(repo_list)
            
            for repo in repo_list[:count//len(languages) + 2]:
                if len(repos) >= count:
                    break
                repos.append(repo.full_name)
                
    except (GithubException, RateLimitExceededException) as e:
        print(f"Error fetching trending repos: {e}")
    
    return repos


def main():
    parser = argparse.ArgumentParser(description="Fetch GitHub repositories for GITHUB_REPO_LIST")
    parser.add_argument("--count", type=int, default=100, help="Number of repositories to fetch (default: 100)")
    parser.add_argument("--languages", type=str, default="python,javascript,typescript,go,rust,java", 
                       help="Comma-separated list of programming languages")
    parser.add_argument("--topics", type=str, default="machine-learning,web-development,api,cli,framework", 
                       help="Comma-separated list of topics")
    parser.add_argument("--min-stars", type=int, default=100, help="Minimum star count (default: 100)")
    parser.add_argument("--include-trending", action="store_true", help="Include trending repositories")
    parser.add_argument("--output-file", type=str, help="Save output to file instead of printing")
    
    args = parser.parse_args()
    
    if not settings.GITHUB_ACCESS_TOKEN or settings.GITHUB_ACCESS_TOKEN == "your_github_token_here":
        print("Error: Please set GITHUB_ACCESS_TOKEN in your .env file")
        return
    
    print(f"Fetching {args.count} repositories...")
    print(f"Languages: {args.languages}")
    print(f"Topics: {args.topics}")
    print(f"Minimum stars: {args.min_stars}")
    print("-" * 50)
    
    github_api = Github(settings.GITHUB_ACCESS_TOKEN)
    all_repos = []
    
    # Fetch by languages
    languages = [lang.strip() for lang in args.languages.split(",")]
    repos_per_language = max(1, args.count // (len(languages) + (2 if args.include_trending else 1)))
    
    for language in languages:
        print(f"\nFetching {repos_per_language} {language} repositories...")
        repos = fetch_repositories_by_language(github_api, language, repos_per_language, args.min_stars)
        all_repos.extend(repos)
        print(f"Found {len(repos)} {language} repositories")
    
    # Fetch by topics
    topics = [topic.strip() for topic in args.topics.split(",")]
    repos_per_topic = max(1, (args.count - len(all_repos)) // (len(topics) + (1 if args.include_trending else 0)))
    
    for topic in topics:
        if len(all_repos) >= args.count:
            break
        print(f"\nFetching {repos_per_topic} repositories for topic '{topic}'...")
        repos = fetch_repositories_by_topic(github_api, topic, repos_per_topic, args.min_stars)
        all_repos.extend(repos)
        print(f"Found {len(repos)} repositories for '{topic}'")
    
    # Fetch trending if requested
    if args.include_trending and len(all_repos) < args.count:
        remaining = args.count - len(all_repos)
        print(f"\nFetching {remaining} trending repositories...")
        trending_repos = fetch_trending_repositories(github_api, remaining)
        all_repos.extend(trending_repos)
        print(f"Found {len(trending_repos)} trending repositories")
    
    # Remove duplicates and shuffle
    unique_repos = list(set(all_repos))
    random.shuffle(unique_repos)
    
    # Limit to requested count
    final_repos = unique_repos[:args.count]
    
    # Format output (no spaces after commas)
    repo_list_string = ",".join(final_repos)
    
    print("\n" + "="*50)
    print(f"FOUND {len(final_repos)} REPOSITORIES")
    print("="*50)
    
    output_content = "\n".join(final_repos)
    output_filename = args.output_file if args.output_file else "data/repo_list.txt"
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    
    with open(output_filename, "w") as f:
        f.write(output_content)
        
    print(f"Repository list saved to: {output_filename}")
    print(f"\nThis file can now be used with populate_db.py using the --repo-file argument.")
    print(f"Example: python scripts/populate_db.py --repo-file {output_filename}")


if __name__ == "__main__":
    main() 