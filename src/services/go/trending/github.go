package main

import (
	"context"
	"fmt"
	"io"
	"log"
	"net/http"
	"strconv"
	"time"
)

const (
	defaultAPIBaseURL = "https://api.github.com"
	maxRetries        = 3
	userAgent         = "ost-linker-trending"
)

// gitHubClient wraps an HTTP client for GitHub REST API calls.
type gitHubClient struct {
	token      string
	apiBaseURL string
	http       *http.Client
}

// newGitHubClient creates a gitHubClient.
// apiBaseURL overrides the default "https://api.github.com" (useful for tests).
// Pass an empty string to use the default.
func newGitHubClient(token, apiBaseURL string) *gitHubClient {
	if apiBaseURL == "" {
		apiBaseURL = defaultAPIBaseURL
	}
	return &gitHubClient{
		token:      token,
		apiBaseURL: apiBaseURL,
		http:       &http.Client{Timeout: 30 * time.Second},
	}
}

// fetchRepoDetails calls GET /repos/{owner}/{repo} and returns the raw JSON body.
// It retries up to maxRetries times with exponential backoff on 5xx and 403.
// It does NOT retry on 404 or 422.
func (c *gitHubClient) fetchRepoDetails(ctx context.Context, owner, repo string) ([]byte, error) {
	reqURL := fmt.Sprintf("%s/repos/%s/%s", c.apiBaseURL, owner, repo)

	for attempt := 1; attempt <= maxRetries; attempt++ {
		body, status, err := c.doRequest(ctx, reqURL)
		if err != nil {
			// Network-level error — retry with backoff
			if attempt < maxRetries {
				backoff := time.Duration(attempt) * time.Second
				log.Printf("[WARN] [%s/%s] network error (attempt %d/%d): %v — retrying in %s",
					owner, repo, attempt, maxRetries, err, backoff)
				time.Sleep(backoff)
				continue
			}
			return nil, fmt.Errorf("fetch %s/%s: %w", owner, repo, err)
		}

		switch {
		case status == http.StatusOK:
			return body, nil
		case status == http.StatusNotFound || status == http.StatusUnprocessableEntity:
			// No point retrying — the resource doesn't exist or the request is bad
			return nil, fmt.Errorf("fetch %s/%s: status %d (no retry)", owner, repo, status)
		case status == http.StatusForbidden:
			// Rate-limited; check for Retry-After (body is nil here because we handle
			// this case before reading the body in doRequest on error status codes)
			backoff := time.Duration(attempt) * 2 * time.Second
			log.Printf("[WARN] [%s/%s] 403 rate-limited (attempt %d/%d) — backing off %s",
				owner, repo, attempt, maxRetries, backoff)
			if attempt < maxRetries {
				time.Sleep(backoff)
				continue
			}
			return nil, fmt.Errorf("fetch %s/%s: rate-limited (status 403)", owner, repo)
		case status >= 500:
			backoff := time.Duration(attempt) * time.Second
			log.Printf("[WARN] [%s/%s] server error %d (attempt %d/%d) — retrying in %s",
				owner, repo, status, attempt, maxRetries, backoff)
			if attempt < maxRetries {
				time.Sleep(backoff)
				continue
			}
			return nil, fmt.Errorf("fetch %s/%s: server error (status %d)", owner, repo, status)
		default:
			return nil, fmt.Errorf("fetch %s/%s: unexpected status %d", owner, repo, status)
		}
	}

	return nil, fmt.Errorf("fetch %s/%s: exhausted %d retries", owner, repo, maxRetries)
}

// doRequest performs a single HTTP GET and returns (body, statusCode, networkError).
// The body is nil when status != 200.
func (c *gitHubClient) doRequest(ctx context.Context, reqURL string) ([]byte, int, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, reqURL, nil)
	if err != nil {
		return nil, 0, fmt.Errorf("build request: %w", err)
	}
	req.Header.Set("Accept", "application/vnd.github+json")
	req.Header.Set("User-Agent", userAgent)
	req.Header.Set("X-GitHub-Api-Version", "2022-11-28")
	if c.token != "" {
		req.Header.Set("Authorization", "token "+c.token)
	}

	resp, err := c.http.Do(req)
	if err != nil {
		return nil, 0, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		// If there is a Retry-After header, honour it (best-effort parse)
		if ra := resp.Header.Get("Retry-After"); ra != "" {
			if secs, parseErr := strconv.Atoi(ra); parseErr == nil {
				log.Printf("[RATE-LIMIT] Retry-After: %ds", secs)
				time.Sleep(time.Duration(secs) * time.Second)
			}
		}
		return nil, resp.StatusCode, nil
	}

	body, err := io.ReadAll(io.LimitReader(resp.Body, 10*1024*1024))
	if err != nil {
		return nil, resp.StatusCode, fmt.Errorf("read body: %w", err)
	}
	return body, resp.StatusCode, nil
}
