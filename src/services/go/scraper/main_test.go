package main

import (
	"testing"
)

func TestParseQueriesFromEnv(t *testing.T) {
	tests := []struct {
		name        string
		envQueries  string // GITHUB_SCRAPING_QUERIES
		envQuery    string // GITHUB_SCRAPING_QUERY
		wantQueries []string
		wantErr     bool
	}{
		{
			name:        "valid JSON array",
			envQueries:  `["stars:>1000","stars:500..1000"]`,
			envQuery:    "",
			wantQueries: []string{"stars:>1000", "stars:500..1000"},
			wantErr:     false,
		},
		{
			name:       "empty JSON array returns error",
			envQueries: `[]`,
			envQuery:   "",
			wantErr:    true,
		},
		{
			name:       "invalid JSON returns error",
			envQueries: `not-json`,
			envQuery:   "",
			wantErr:    true,
		},
		{
			name:        "single query fallback",
			envQueries:  "",
			envQuery:    "stars:>5000",
			wantQueries: []string{"stars:>5000"},
			wantErr:     false,
		},
		{
			name:        "JSON array takes priority over single query",
			envQueries:  `["stars:>100"]`,
			envQuery:    "stars:>5000",
			wantQueries: []string{"stars:>100"},
			wantErr:     false,
		},
		{
			name:       "neither set returns error",
			envQueries: "",
			envQuery:   "",
			wantErr:    true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			t.Setenv("GITHUB_SCRAPING_QUERIES", tt.envQueries)
			t.Setenv("GITHUB_SCRAPING_QUERY", tt.envQuery)

			queries, err := parseQueriesFromEnv()

			if tt.wantErr {
				if err == nil {
					t.Fatalf("expected error, got nil with queries=%v", queries)
				}
				return
			}
			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			if len(queries) != len(tt.wantQueries) {
				t.Fatalf("got %d queries, want %d", len(queries), len(tt.wantQueries))
			}
			for i, q := range queries {
				if q != tt.wantQueries[i] {
					t.Errorf("query[%d] = %q, want %q", i, q, tt.wantQueries[i])
				}
			}
		})
	}
}
