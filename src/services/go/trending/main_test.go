package main

import (
	"encoding/json"
	"os"
	"testing"
	"time"
)

// TestSummaryJSON verifies that trendingSummary serialises to the expected JSON keys.
func TestSummaryJSON(t *testing.T) {
	s := trendingSummary{
		Collected:       25,
		Upserted:        24,
		Failed:          1,
		TrendingDate:    "2026-03-12",
		Status:          "partial",
		DurationSeconds: 3.14,
	}
	data, err := json.Marshal(s)
	if err != nil {
		t.Fatalf("json.Marshal: %v", err)
	}

	var m map[string]any
	if err := json.Unmarshal(data, &m); err != nil {
		t.Fatalf("json.Unmarshal: %v", err)
	}

	for _, key := range []string{"collected", "upserted", "failed", "trending_date", "status", "duration_seconds"} {
		if _, ok := m[key]; !ok {
			t.Errorf("missing key %q in JSON output", key)
		}
	}

	if got := m["collected"].(float64); got != 25 {
		t.Errorf("collected: want 25, got %v", got)
	}
	if got := m["status"].(string); got != "partial" {
		t.Errorf("status: want partial, got %v", got)
	}
}

// TestRequireEnv verifies that requireEnv returns the env var value when set
// and returns an empty string (signalling missing) when unset.
func TestRequireEnv(t *testing.T) {
	const key = "_TEST_OST_TRENDING_ENV_VAR"
	os.Unsetenv(key)

	val, ok := lookupRequiredEnv(key)
	if ok {
		t.Errorf("expected ok=false for unset env var, got val=%q", val)
	}

	os.Setenv(key, "testvalue")
	defer os.Unsetenv(key)

	val, ok = lookupRequiredEnv(key)
	if !ok {
		t.Error("expected ok=true for set env var")
	}
	if val != "testvalue" {
		t.Errorf("expected val=testvalue, got %q", val)
	}
}

// TestTrendingDateFormat verifies that trendingDateNow returns a valid YYYY-MM-DD string.
func TestTrendingDateFormat(t *testing.T) {
	d := trendingDateNow()
	if len(d) != 10 {
		t.Errorf("expected date string of length 10, got %q (len %d)", d, len(d))
	}
	// Verify it parses as a date
	if _, err := time.Parse("2006-01-02", d); err != nil {
		t.Errorf("date %q does not parse as YYYY-MM-DD: %v", d, err)
	}
}
