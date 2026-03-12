package main

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

// TestFetchRepoDetails verifies that a 200 response returns the raw JSON body.
func TestFetchRepoDetails(t *testing.T) {
	payload := `{"id":1,"full_name":"owner/repo","stargazers_count":42}`
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("User-Agent") != "ost-linker-trending" {
			t.Errorf("expected User-Agent ost-linker-trending, got %q", r.Header.Get("User-Agent"))
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(payload))
	}))
	defer srv.Close()

	client := newGitHubClient("", srv.URL)
	body, err := client.fetchRepoDetails(context.Background(), "owner", "repo")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if string(body) != payload {
		t.Errorf("expected body %q, got %q", payload, string(body))
	}
}

// TestFetchRepoDetails_Retry verifies that the client retries on 5xx responses
// and eventually succeeds when the server recovers.
func TestFetchRepoDetails_Retry(t *testing.T) {
	attempts := 0
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		attempts++
		if attempts < 3 {
			w.WriteHeader(http.StatusServiceUnavailable) // 503
			return
		}
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"id":2}`))
	}))
	defer srv.Close()

	client := newGitHubClient("", srv.URL)
	body, err := client.fetchRepoDetails(context.Background(), "owner", "repo")
	if err != nil {
		t.Fatalf("unexpected error after retries: %v", err)
	}
	if !strings.Contains(string(body), `"id":2`) {
		t.Errorf("unexpected body: %s", body)
	}
	if attempts != 3 {
		t.Errorf("expected 3 attempts (2 failures + 1 success), got %d", attempts)
	}
}

// TestFetchRepoDetails_404 verifies that a 404 response returns an error
// immediately without retrying.
func TestFetchRepoDetails_404(t *testing.T) {
	attempts := 0
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		attempts++
		w.WriteHeader(http.StatusNotFound)
	}))
	defer srv.Close()

	client := newGitHubClient("", srv.URL)
	_, err := client.fetchRepoDetails(context.Background(), "owner", "repo")
	if err == nil {
		t.Fatal("expected error for 404, got nil")
	}
	if attempts != 1 {
		t.Errorf("expected exactly 1 attempt for 404 (no retry), got %d", attempts)
	}
}

// TestFetchRepoDetails_AuthHeader verifies that the Authorization header is set
// when a token is provided.
func TestFetchRepoDetails_AuthHeader(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		auth := r.Header.Get("Authorization")
		if auth != "token mytoken" {
			t.Errorf("expected Authorization: token mytoken, got %q", auth)
		}
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{}`))
	}))
	defer srv.Close()

	client := newGitHubClient("mytoken", srv.URL)
	_, err := client.fetchRepoDetails(context.Background(), "owner", "repo")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
}
