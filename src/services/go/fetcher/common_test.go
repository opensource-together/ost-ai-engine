package main

import (
	"testing"
)

func TestExtractOwnerRepo(t *testing.T) {
	tests := []struct {
		name      string
		rawURL    string
		wantOwner string
		wantRepo  string
	}{
		{
			name:      "standard github url",
			rawURL:    "https://github.com/owner/repo",
			wantOwner: "owner",
			wantRepo:  "repo",
		},
		{
			name:      "url with .git suffix",
			rawURL:    "https://github.com/owner/repo.git",
			wantOwner: "owner",
			wantRepo:  "repo",
		},
		{
			name:      "url with extra path segments",
			rawURL:    "https://github.com/owner/repo/tree/main",
			wantOwner: "owner",
			wantRepo:  "repo",
		},
		{
			name:      "url with trailing slash",
			rawURL:    "https://github.com/owner/repo/",
			wantOwner: "owner",
			wantRepo:  "repo",
		},
		{
			name:      "missing repo segment",
			rawURL:    "https://github.com/owner",
			wantOwner: "",
			wantRepo:  "",
		},
		{
			name:      "empty string",
			rawURL:    "",
			wantOwner: "",
			wantRepo:  "",
		},
		{
			name:      "whitespace only",
			rawURL:    "   ",
			wantOwner: "",
			wantRepo:  "",
		},
		{
			name:      "url with only slashes",
			rawURL:    "https://github.com//",
			wantOwner: "",
			wantRepo:  "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			owner, repo := extractOwnerRepo(tt.rawURL)
			if owner != tt.wantOwner {
				t.Errorf("extractOwnerRepo(%q) owner = %q, want %q", tt.rawURL, owner, tt.wantOwner)
			}
			if repo != tt.wantRepo {
				t.Errorf("extractOwnerRepo(%q) repo = %q, want %q", tt.rawURL, repo, tt.wantRepo)
			}
		})
	}
}

func TestTruncateUTF8(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		maxBytes int
		want     string
	}{
		{
			name:     "ascii within limit",
			input:    "hello",
			maxBytes: 10,
			want:     "hello",
		},
		{
			name:     "ascii truncated",
			input:    "hello world",
			maxBytes: 5,
			want:     "hello",
		},
		{
			name:     "multi-byte rune boundary respected",
			input:    "café",
			maxBytes: 4,
			want:     "caf",
		},
		{
			name:     "cjk 3-byte chars",
			input:    "你好世界",
			maxBytes: 6,
			want:     "你好",
		},
		{
			name:     "empty string",
			input:    "",
			maxBytes: 5,
			want:     "",
		},
		{
			name:     "zero max bytes",
			input:    "hello",
			maxBytes: 0,
			want:     "",
		},
		{
			name:     "exact length",
			input:    "abc",
			maxBytes: 3,
			want:     "abc",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := truncateUTF8(tt.input, tt.maxBytes)
			if got != tt.want {
				t.Errorf("truncateUTF8(%q, %d) = %q, want %q", tt.input, tt.maxBytes, got, tt.want)
			}
		})
	}
}

func TestValidTargetTables(t *testing.T) {
	expectedKeys := []string{"readme", "languages", "topics"}
	for _, key := range expectedKeys {
		if _, ok := validTargetTables[key]; !ok {
			t.Errorf("validTargetTables missing expected key %q", key)
		}
	}

	if _, ok := validTargetTables["nonexistent"]; ok {
		t.Error("validTargetTables should not contain key 'nonexistent'")
	}
}
