//go:build integration

package main

import (
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"testing"
	"time"

	"github.com/joho/godotenv"
)

// TestEnvLoaded validates that the minimal set of environment variables
// required by the scraper are present and well-formed.
func TestEnvLoaded(t *testing.T) {
	// Load .env from repo root if present; ignore error to allow CI overrides.
	// Try current dir and walk up a few parents to reach repo root regardless of cwd.
	candidatePaths := []string{".env"}
	up := ".."
	for i := 0; i < 8; i++ {
		candidatePaths = append(candidatePaths, filepath.Join(up, ".env"))
		up = filepath.Join("..", up)
	}
	for _, p := range candidatePaths {
		_ = godotenv.Overload(p)
	}

	required := []string{
		"PGHOST",
		"PGPORT",
		"PGUSER",
		"PGPASSWORD",
		"PGDATABASE",
		"GITHUB_ACCESS_TOKEN",
	}

	for _, k := range required {
		v := os.Getenv(k)
		if v == "" {
			t.Fatalf("required env %s is empty (cwd=%s)", k, must(os.Getwd()))
		}
	}

	if _, err := strconv.Atoi(os.Getenv("PGPORT")); err != nil {
		t.Fatalf("PGPORT must be numeric: %v", err)
	}
}

func must[T any](v T, _ error) T { return v }

// TestGitHubAPIHealthy performs a minimal API call with a strict timeout
// to ensure the GitHub API is reachable and responds successfully.
func TestGitHubAPIHealthy(t *testing.T) {
	// Load env as above (tokens may be set via secrets in CI or .env locally)
	// Quick sanity: do not require DB vars for this test
	token := os.Getenv("GITHUB_ACCESS_TOKEN")

	client := &http.Client{Timeout: 5 * time.Second}
	req, _ := http.NewRequest("GET", "https://api.github.com/rate_limit", nil)
	req.Header.Set("User-Agent", "ost-ai-engine-ci-check")
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	resp, err := client.Do(req)
	if err != nil {
		t.Fatalf("github api request failed: %v", err)
	}
	defer resp.Body.Close()
	// Retry once with legacy scheme if bearer is rejected
	if resp.StatusCode == 401 && token != "" {
		// retry with "token" scheme
		req2, _ := http.NewRequest("GET", "https://api.github.com/rate_limit", nil)
		req2.Header.Set("User-Agent", "ost-ai-engine-ci-check")
		req2.Header.Set("Authorization", "token "+token)
		resp.Body.Close()
		resp, err = client.Do(req2)
		if err != nil {
			t.Fatalf("github api retry failed: %v", err)
		}
		defer resp.Body.Close()
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		t.Fatalf("unexpected status from github: %d", resp.StatusCode)
	}
}
