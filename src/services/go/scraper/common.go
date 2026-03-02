package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"strconv"
	"time"
)

type githubRepo struct {
	ID          int64   `json:"id"`
	Name        string  `json:"name"`
	FullName    string  `json:"full_name"`
	HTMLURL     string  `json:"html_url"`
	Description *string `json:"description"`
	Stargazers  int     `json:"stargazers_count"`
	Forks       int     `json:"forks_count"`
	Language    *string `json:"language"`
	Homepage    *string `json:"homepage"`
	DefaultBr   *string `json:"default_branch"`
	Private     *bool   `json:"private"`
	Owner       *struct {
		Login     string  `json:"login"`
		AvatarURL *string `json:"avatar_url"`
	} `json:"owner"`
	CreatedAt string `json:"created_at"`
	UpdatedAt string `json:"updated_at"`
	PushedAt  string `json:"pushed_at"`
}

type githubSearchResponse struct {
	TotalCount        int          `json:"total_count"`
	IncompleteResults bool         `json:"incomplete_results"`
	Items             []githubRepo `json:"items"`
}

// rateLimitError is returned when GitHub responds with 403 due to rate limiting.
type rateLimitError struct {
	RetryAfter time.Duration
}

func (e *rateLimitError) Error() string {
	return fmt.Sprintf("rate limited, retry after %s", e.RetryAfter)
}

func newHTTPClient() *http.Client {
	return &http.Client{Timeout: 30 * time.Second}
}

func fetchGitHubRepos(ctx context.Context, client *http.Client, token string, apiURL string, query string, perPage, page int) (githubSearchResponse, error) {
	var result githubSearchResponse
	if apiURL == "" {
		return result, fmt.Errorf("GITHUB_API_URL is required but not set")
	}
	base, err := url.Parse(apiURL)
	if err != nil {
		return result, fmt.Errorf("invalid github api url: %v", err)
	}
	q := base.Query()
	q.Set("q", query)
	q.Set("sort", "stars")
	q.Set("order", "desc")
	q.Set("per_page", strconv.Itoa(perPage))
	q.Set("page", strconv.Itoa(page))
	base.RawQuery = q.Encode()

	req, err := http.NewRequestWithContext(ctx, "GET", base.String(), nil)
	if err != nil {
		return result, fmt.Errorf("creating request: %w", err)
	}
	req.Header.Set("Accept", "application/vnd.github+json")
	req.Header.Set("User-Agent", "ost-linker-scraper")
	req.Header.Set("X-GitHub-Api-Version", "2022-11-28")
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}

	resp, err := client.Do(req)
	if err != nil {
		return result, err
	}
	defer resp.Body.Close()

	if resp.StatusCode == 403 {
		retryAfter := resp.Header.Get("Retry-After")
		if retryAfter != "" {
			seconds, parseErr := strconv.Atoi(retryAfter)
			if parseErr == nil {
				return result, &rateLimitError{RetryAfter: time.Duration(seconds) * time.Second}
			}
		}
		return result, &rateLimitError{RetryAfter: 60 * time.Second}
	}

	if resp.StatusCode != 200 {
		return result, fmt.Errorf("github api status %d", resp.StatusCode)
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return result, err
	}
	return result, nil
}
