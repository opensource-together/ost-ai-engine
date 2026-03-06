package main

import (
	"net/http"
	"testing"
	"time"
)

func TestSearchRateLimiterUpdate(t *testing.T) {
	tests := []struct {
		name              string
		headers           map[string]string
		wantRemaining     int
		wantResetChanged  bool
	}{
		{
			name: "both headers present",
			headers: map[string]string{
				"X-RateLimit-Remaining": "25",
				"X-RateLimit-Reset":     "1700000000",
			},
			wantRemaining:    25,
			wantResetChanged: true,
		},
		{
			name: "only remaining header",
			headers: map[string]string{
				"X-RateLimit-Remaining": "10",
			},
			wantRemaining:    10,
			wantResetChanged: false,
		},
		{
			name: "only reset header",
			headers: map[string]string{
				"X-RateLimit-Reset": "1700000000",
			},
			wantRemaining:    30,
			wantResetChanged: true,
		},
		{
			name:              "no rate limit headers",
			headers:           map[string]string{},
			wantRemaining:     30,
			wantResetChanged:  false,
		},
		{
			name: "non-numeric remaining ignored",
			headers: map[string]string{
				"X-RateLimit-Remaining": "abc",
			},
			wantRemaining:    30,
			wantResetChanged: false,
		},
		{
			name: "non-numeric reset ignored",
			headers: map[string]string{
				"X-RateLimit-Reset": "not-a-number",
			},
			wantRemaining:    30,
			wantResetChanged: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			rl := newSearchRateLimiter()
			initialResetAt := rl.resetAt

			resp := &http.Response{Header: http.Header{}}
			for k, v := range tt.headers {
				resp.Header.Set(k, v)
			}

			rl.update(resp)

			if rl.remaining != tt.wantRemaining {
				t.Errorf("remaining = %d, want %d", rl.remaining, tt.wantRemaining)
			}

			resetChanged := !rl.resetAt.Equal(initialResetAt)
			if resetChanged != tt.wantResetChanged {
				t.Errorf("resetAt changed = %v, want %v (resetAt=%v, initial=%v)",
					resetChanged, tt.wantResetChanged, rl.resetAt, initialResetAt)
			}

			if tt.wantResetChanged {
				expected := time.Unix(1700000000, 0)
				if !rl.resetAt.Equal(expected) {
					t.Errorf("resetAt = %v, want %v", rl.resetAt, expected)
				}
			}
		})
	}
}
