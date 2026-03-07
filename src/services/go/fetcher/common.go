package main

import (
	"context"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"sync"
	"time"
	"unicode/utf8"

	"github.com/jackc/pgx/v5/pgxpool"
)

type rateLimiter struct {
	mu        sync.Mutex
	remaining int
	resetAt   time.Time
}

func newRateLimiter() *rateLimiter {
	return &rateLimiter{remaining: 5000}
}

func (rl *rateLimiter) wait() {
	rl.mu.Lock()
	if rl.remaining <= 1 && time.Now().Before(rl.resetAt) {
		sleepDur := time.Until(rl.resetAt) + time.Second
		log.Printf("[RATE-LIMIT] Exhausted, sleeping %s until reset", sleepDur)
		rl.mu.Unlock()
		time.Sleep(sleepDur)
		rl.mu.Lock()
	}
	rl.mu.Unlock()
}

func (rl *rateLimiter) update(resp *http.Response) {
	rl.mu.Lock()
	defer rl.mu.Unlock()
	if v := resp.Header.Get("X-RateLimit-Remaining"); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			rl.remaining = n
		}
	}
	if v := resp.Header.Get("X-RateLimit-Reset"); v != "" {
		if ts, err := strconv.ParseInt(v, 10, 64); err == nil {
			rl.resetAt = time.Unix(ts, 0)
		}
	}
}

type GitHubFetcher struct {
	db          *pgxpool.Pool
	client      *http.Client
	githubToken string
	maxWorkers  int
	rl          *rateLimiter
}

type Project struct {
	ID      string
	RepoURL string
	Owner   string
	Repo    string
}

func NewGitHubFetcher(db *pgxpool.Pool, token string, workers int) *GitHubFetcher {
	return &GitHubFetcher{
		db:          db,
		client:      &http.Client{Timeout: 30 * time.Second},
		githubToken: token,
		maxWorkers:  workers,
		rl:          newRateLimiter(),
	}
}

// extractOwnerRepo parses a GitHub URL and returns (owner, repo).
func extractOwnerRepo(rawURL string) (string, string) {
	parsed, err := url.Parse(strings.TrimSpace(rawURL))
	if err != nil {
		return "", ""
	}
	path := strings.Trim(parsed.Path, "/")
	path = strings.TrimSuffix(path, ".git")
	parts := strings.SplitN(path, "/", 3)
	if len(parts) < 2 || parts[0] == "" || parts[1] == "" {
		return "", ""
	}
	return parts[0], parts[1]
}

// validTargetTables is an allowlist of mode keys to fully-qualified table names used by
// getNewProjects. Only these values may be interpolated into the SQL query.
var validTargetTables = map[string]string{
	"readme":    "github.raw_github_readme",
	"languages": "github.raw_github_languages",
	"topics":    "github.raw_github_topics",
}

// getNewProjects fetches only projects not yet present in the table identified by modeKey
// (incremental fetch). modeKey must be one of the keys in validTargetTables.
func (f *GitHubFetcher) getNewProjects(ctx context.Context, limit int, modeKey string) ([]Project, error) {
	targetTable, ok := validTargetTables[modeKey]
	if !ok {
		return nil, fmt.Errorf("getNewProjects: unknown mode key %q", modeKey)
	}
	query := fmt.Sprintf(`
		SELECT d.project_id, d.repo_url
		FROM github.int_github_detection d
		LEFT JOIN %s t ON t.project_id = d.project_id
		WHERE d.repo_url IS NOT NULL AND d.repo_url != ''
		  AND t.project_id IS NULL
	`, targetTable)
	if limit > 0 {
		query += fmt.Sprintf(" LIMIT %d", limit)
	}

	rows, err := f.db.Query(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("query new projects: %w", err)
	}
	defer rows.Close()

	var projects []Project
	for rows.Next() {
		var p Project
		if err := rows.Scan(&p.ID, &p.RepoURL); err != nil {
			continue
		}
		owner, repo := extractOwnerRepo(p.RepoURL)
		if owner != "" && repo != "" {
			p.Owner = owner
			p.Repo = repo
			projects = append(projects, p)
		}
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterating projects: %w", err)
	}
	return projects, nil
}

// getProjects fetches projects from int_github_detection.
func (f *GitHubFetcher) getProjects(ctx context.Context, limit int) ([]Project, error) {
	query := `
		SELECT project_id, repo_url
		FROM github.int_github_detection
		WHERE repo_url IS NOT NULL AND repo_url != ''
	`
	if limit > 0 {
		query += fmt.Sprintf(" LIMIT %d", limit)
	}

	rows, err := f.db.Query(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("query projects: %w", err)
	}
	defer rows.Close()

	var projects []Project
	for rows.Next() {
		var p Project
		if err := rows.Scan(&p.ID, &p.RepoURL); err != nil {
			continue
		}
		owner, repo := extractOwnerRepo(p.RepoURL)
		if owner != "" && repo != "" {
			p.Owner = owner
			p.Repo = repo
			projects = append(projects, p)
		}
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterating projects: %w", err)
	}
	return projects, nil
}

// makeRequestWithContext performs a GitHub API request with context, rate limiting, and User-Agent.
func (f *GitHubFetcher) makeRequestWithContext(ctx context.Context, reqURL string) (*http.Response, error) {
	f.rl.wait()

	req, err := http.NewRequestWithContext(ctx, "GET", reqURL, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Accept", "application/vnd.github.v3+json")
	req.Header.Set("User-Agent", "ost-linker-fetcher")
	if f.githubToken != "" {
		req.Header.Set("Authorization", "token "+f.githubToken)
	}

	resp, err := f.client.Do(req)
	if err != nil {
		return nil, err
	}

	f.rl.update(resp)
	return resp, nil
}

// retryRequest performs a GET with retries and exponential backoff.
// Does not retry on 404 or 422.
func (f *GitHubFetcher) retryRequest(ctx context.Context, reqURL string, maxAttempts int) ([]byte, error) {
	for attempt := 1; attempt <= maxAttempts; attempt++ {
		resp, err := f.makeRequestWithContext(ctx, reqURL)
		if err != nil {
			if attempt < maxAttempts {
				time.Sleep(time.Duration(attempt) * time.Second)
				continue
			}
			return nil, err
		}

		body, readErr := io.ReadAll(io.LimitReader(resp.Body, 10*1024*1024))
		resp.Body.Close()

		if resp.StatusCode == 200 {
			if readErr != nil {
				return nil, readErr
			}
			return body, nil
		}
		if resp.StatusCode == 404 || resp.StatusCode == 422 {
			return nil, fmt.Errorf("status %d", resp.StatusCode)
		}
		if resp.StatusCode == 403 {
			retryAfter := resp.Header.Get("Retry-After")
			if retryAfter != "" {
				if seconds, parseErr := strconv.Atoi(retryAfter); parseErr == nil {
					log.Printf("[RATE-LIMIT] 403 received, sleeping %ds", seconds)
					time.Sleep(time.Duration(seconds) * time.Second)
					continue
				}
			}
			time.Sleep(60 * time.Second)
			continue
		}
		if attempt < maxAttempts {
			time.Sleep(time.Duration(attempt) * time.Second)
			continue
		}
		return nil, fmt.Errorf("status %d", resp.StatusCode)
	}
	return nil, fmt.Errorf("request failed after %d attempts", maxAttempts)
}

// truncateUTF8 truncates s to at most maxBytes bytes without breaking a multi-byte rune.
func truncateUTF8(s string, maxBytes int) string {
	if len(s) <= maxBytes {
		return s
	}
	// Back up from maxBytes to the start of a valid rune
	for maxBytes > 0 && !utf8.RuneStart(s[maxBytes]) {
		maxBytes--
	}
	return s[:maxBytes]
}
