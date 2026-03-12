package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

const trendingPageURL = "https://github.com/trending?since=daily&spoken_language_code=en"

// trendingSummary is the JSON object written to stdout for Dagster to parse.
type trendingSummary struct {
	Collected       int     `json:"collected"`
	Upserted        int     `json:"upserted"`
	Failed          int     `json:"failed"`
	TrendingDate    string  `json:"trending_date"`
	Status          string  `json:"status"`
	DurationSeconds float64 `json:"duration_seconds"`
}

// lookupRequiredEnv returns the value of the named env var and whether it was set.
// Exported as a named function so it can be tested independently.
func lookupRequiredEnv(key string) (string, bool) {
	v, ok := os.LookupEnv(key)
	return v, ok && v != ""
}

// trendingDateNow returns today's date formatted as YYYY-MM-DD.
func trendingDateNow() string {
	return time.Now().UTC().Format("2006-01-02")
}

// fetchTrendingPage fetches the GitHub Trending HTML page and returns parsed repos.
func fetchTrendingPage(ctx context.Context, pageURL string) ([]trendingRepo, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, pageURL, nil)
	if err != nil {
		return nil, fmt.Errorf("build trending page request: %w", err)
	}
	req.Header.Set("User-Agent", userAgent)

	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("fetch trending page: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("trending page returned status %d", resp.StatusCode)
	}

	return parseTrendingPage(resp.Body)
}

// upsertBatch inserts/updates all repos into github.raw_trending_project in one batch.
// Returns the number of successfully upserted rows and failed rows.
func upsertBatch(ctx context.Context, pool *pgxpool.Pool, repos []trendingRepo, ghClient *gitHubClient, trendingDate string) (int, int) {
	const upsertSQL = `
		INSERT INTO "github"."raw_trending_project"
			("project_id", "trending_date", "repo_url", "data", "stars_today", "createdAt", "updatedAt")
		VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
		ON CONFLICT ("project_id", "trending_date") DO UPDATE
		SET "data"       = EXCLUDED."data",
		    "stars_today" = EXCLUDED."stars_today",
		    "updatedAt"  = NOW()
	`

	batch := &pgx.Batch{}
	skipped := 0

	for _, repo := range repos {
		rawJSON, err := ghClient.fetchRepoDetails(ctx, repo.Owner, repo.Repo)
		if err != nil {
			log.Printf("[WARN] fetchRepoDetails %s/%s: %v — skipping", repo.Owner, repo.Repo, err)
			skipped++
			continue
		}

		projectID := uuid.NewSHA1(uuid.NameSpaceURL, []byte(repo.RepoURL))

		batch.Queue(upsertSQL,
			projectID.String(),
			trendingDate,
			repo.RepoURL,
			rawJSON,
			repo.StarsToday,
		)
	}

	upserted := 0
	failed := skipped

	if batch.Len() > 0 {
		dbCtx, dbCancel := context.WithTimeout(ctx, 30*time.Second)
		defer dbCancel()

		br := pool.SendBatch(dbCtx, batch)
		for i := 0; i < batch.Len(); i++ {
			if _, err := br.Exec(); err != nil {
				log.Printf("[ERROR] upsert batch item %d: %v", i, err)
				failed++
			} else {
				upserted++
			}
		}
		br.Close()
	}

	return upserted, failed
}

func main() {
	dbURL, ok := lookupRequiredEnv("DATABASE_URL")
	if !ok {
		log.Fatal("DATABASE_URL is required")
	}

	token := os.Getenv("GITHUB_ACCESS_TOKEN") // optional
	if token == "" {
		log.Println("[WARN] GITHUB_ACCESS_TOKEN not set; may hit rate limits")
	}

	start := time.Now()
	trendingDate := trendingDateNow()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()

	// Fetch and parse the trending page
	repos, err := fetchTrendingPage(ctx, trendingPageURL)
	if err != nil {
		log.Fatalf("fetch trending page: %v", err)
	}
	log.Printf("[INFO] Parsed %d trending repos for %s", len(repos), trendingDate)

	// Connect to the database
	pool, err := pgxpool.New(ctx, dbURL)
	if err != nil {
		log.Fatalf("create DB connection pool: %v", err)
	}
	defer pool.Close()

	ghClient := newGitHubClient(token, "")

	upserted, failed := upsertBatch(ctx, pool, repos, ghClient, trendingDate)

	summary := trendingSummary{
		Collected:       len(repos),
		Upserted:        upserted,
		Failed:          failed,
		TrendingDate:    trendingDate,
		DurationSeconds: time.Since(start).Seconds(),
		Status:          "success",
	}
	if failed > 0 {
		summary.Status = "partial"
	}

	if err := json.NewEncoder(os.Stdout).Encode(summary); err != nil {
		log.Fatalf("encode summary: %v", err)
	}
}
