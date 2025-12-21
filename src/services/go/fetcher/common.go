package main

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

type GitHubFetcher struct {
	db          *pgxpool.Pool
	client      *http.Client
	githubToken string
	maxWorkers  int
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
	}
}

// Common function to extract owner/repo from URL
func extractOwnerRepo(url string) (string, string) {
	url = strings.TrimSuffix(url, "/")
	parts := strings.Split(url, "/")
	if len(parts) >= 2 {
		return parts[len(parts)-2], parts[len(parts)-1]
	}
	return "", ""
}

// Get projects from int_github_detection that define what we should fetch
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
	return projects, nil
}

func (f *GitHubFetcher) makeRequest(url string) ([]byte, error) {
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Accept", "application/vnd.github.v3+json")
	if f.githubToken != "" {
		req.Header.Set("Authorization", "token "+f.githubToken)
	}

	resp, err := f.client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode == 404 {
		return nil, fmt.Errorf("not found")
	}
	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("status %d", resp.StatusCode)
	}

	return io.ReadAll(resp.Body)
}
