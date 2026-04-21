package main

import (
	"os"
	"strings"
	"testing"
)

// TestParseTrendingPage verifies that the parser extracts all trending repos
// from the real GitHub Trending HTML snapshot.
func TestParseTrendingPage(t *testing.T) {
	f, err := os.Open("testdata/trending.html")
	if err != nil {
		t.Fatalf("open testdata/trending.html: %v", err)
	}
	defer f.Close()

	repos, err := parseTrendingPage(f)
	if err != nil {
		t.Fatalf("parseTrendingPage error: %v", err)
	}
	if len(repos) == 0 {
		t.Fatal("expected at least one trending repo, got 0")
	}
	// The snapshot has 24 repos
	if len(repos) < 20 {
		t.Errorf("expected >= 20 repos, got %d", len(repos))
	}

	// Verify structure of the first repo
	first := repos[0]
	if first.Owner == "" {
		t.Error("first repo Owner is empty")
	}
	if first.Repo == "" {
		t.Error("first repo Repo is empty")
	}
	if first.RepoURL == "" {
		t.Error("first repo RepoURL is empty")
	}
	if !strings.HasPrefix(first.RepoURL, "https://github.com/") {
		t.Errorf("expected RepoURL to start with https://github.com/, got %q", first.RepoURL)
	}
	// Owner and Repo must match what's in the URL
	expectedURL := "https://github.com/" + first.Owner + "/" + first.Repo
	if first.RepoURL != expectedURL {
		t.Errorf("RepoURL %q does not match Owner/Repo combination %q", first.RepoURL, expectedURL)
	}
}

// TestParseTrendingPage_StarsToday verifies that stars-today counts are parsed
// as non-negative integers from the real snapshot.
func TestParseTrendingPage_StarsToday(t *testing.T) {
	f, err := os.Open("testdata/trending.html")
	if err != nil {
		t.Fatalf("open testdata/trending.html: %v", err)
	}
	defer f.Close()

	repos, err := parseTrendingPage(f)
	if err != nil {
		t.Fatalf("parseTrendingPage error: %v", err)
	}

	nonZero := 0
	for _, r := range repos {
		if r.StarsToday < 0 {
			t.Errorf("repo %s/%s has negative StarsToday: %d", r.Owner, r.Repo, r.StarsToday)
		}
		if r.StarsToday > 0 {
			nonZero++
		}
	}
	// At least half the repos should have a non-zero stars-today count
	if nonZero < len(repos)/2 {
		t.Errorf("expected most repos to have StarsToday > 0; only %d/%d do", nonZero, len(repos))
	}
}

// TestParseTrendingPage_EmptyHTML verifies that an empty document returns
// no repos and no error.
func TestParseTrendingPage_EmptyHTML(t *testing.T) {
	r := strings.NewReader("<html><body></body></html>")
	repos, err := parseTrendingPage(r)
	if err != nil {
		t.Fatalf("unexpected error on empty HTML: %v", err)
	}
	if len(repos) != 0 {
		t.Errorf("expected 0 repos for empty HTML, got %d", len(repos))
	}
}
