//go:build integration

package main

import (
	"os"
	"path/filepath"
	"strconv"
	"testing"

	"github.com/joho/godotenv"
)

// TestEnvLoaded validates that the minimal set of environment variables
// required by the GitLab scraper are present and well-formed.
func TestEnvLoaded(t *testing.T) {
	// Load .env from repo root if present; ignore error to allow CI overrides.
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
		"GITLAB_ACCESS_TOKEN",
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
