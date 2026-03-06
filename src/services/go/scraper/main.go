package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"net/http"
	"os"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type queryResult struct {
	Query          string `json:"query"`
	CollectedCount int    `json:"collected_count"`
	UpsertedCount  int    `json:"upserted_count"`
	FailedUpserts  int    `json:"failed_upserts"`
}

type scrapeSummary struct {
	Queries         []queryResult `json:"queries"`
	TotalCollected  int           `json:"total_collected"`
	TotalUpserted   int           `json:"total_upserted"`
	TotalFailed     int           `json:"total_failed"`
	Status          string        `json:"status"`
	DurationSeconds float64       `json:"duration_seconds"`
}

// scrapeQuery runs the paginated scrape+upsert loop for a single GitHub search query.
func scrapeQuery(ctx context.Context, pool *pgxpool.Pool, client *http.Client, rl *searchRateLimiter,
	token, apiURL, query string, maxRepos, perPage int) queryResult {

	res := queryResult{Query: query}
	const maxRetries = 3

	for page := 1; res.CollectedCount < maxRepos; page++ {
		var ghRes githubSearchResponse
		var fetchErr error
		for attempt := 1; attempt <= maxRetries; attempt++ {
			ghRes, fetchErr = fetchGitHubRepos(ctx, client, rl, token, apiURL, query, perPage, page)
			if fetchErr == nil {
				break
			}

			var rlErr *rateLimitError
			if errors.As(fetchErr, &rlErr) {
				log.Printf("[WARN] [%s] Rate limited, sleeping %s before retry", query, rlErr.RetryAfter)
				time.Sleep(rlErr.RetryAfter)
				continue
			}

			if attempt < maxRetries {
				backoff := time.Duration(attempt) * 2 * time.Second
				log.Printf("[WARN] [%s] GitHub fetch attempt %d/%d failed: %v, retrying in %s",
					query, attempt, maxRetries, fetchErr, backoff)
				time.Sleep(backoff)
			}
		}
		if fetchErr != nil {
			log.Printf("[ERROR] [%s] GitHub fetch failed after %d retries: %v, stopping with partial results",
				query, maxRetries, fetchErr)
			break
		}

		if len(ghRes.Items) == 0 {
			break
		}

		if ghRes.IncompleteResults {
			log.Printf("[WARN] [%s] GitHub returned incomplete results for page %d", query, page)
		}

		// Batch upsert via SendBatch
		batch := &pgx.Batch{}
		for _, repo := range ghRes.Items {
			repoData, err := json.Marshal(repo)
			if err != nil {
				log.Printf("[ERROR] [%s] Error marshaling repo %s: %v", query, repo.Name, err)
				res.FailedUpserts++
				continue
			}

			repoURL := repo.HTMLURL
			if repoURL == "" {
				continue
			}

			id := uuid.NewSHA1(uuid.NameSpaceURL, []byte(repoURL))

			batch.Queue(`
				INSERT INTO "github"."raw_github_project" ("id", "data", "createdAt", "updatedAt")
				VALUES ($1, $2, NOW(), NOW())
				ON CONFLICT ("id") DO UPDATE
				SET "data" = EXCLUDED."data",
				    "updatedAt" = NOW()
			`, id.String(), repoData)
		}

		if batch.Len() > 0 {
			dbCtx, dbCancel := context.WithTimeout(ctx, 30*time.Second)
			br := pool.SendBatch(dbCtx, batch)
			for i := 0; i < batch.Len(); i++ {
				_, err := br.Exec()
				if err != nil {
					log.Printf("[ERROR] [%s] Failed to upsert repo (batch item %d): %v", query, i, err)
					res.FailedUpserts++
				} else {
					res.UpsertedCount++
				}
			}
			br.Close()
			dbCancel()
		}

		res.CollectedCount += len(ghRes.Items)
		log.Printf("[INFO] [%s] Collected %d / %d", query, res.CollectedCount, maxRepos)
	}

	return res
}

// parseQueriesFromEnv resolves the list of queries from env vars.
// Priority: GITHUB_SCRAPING_QUERIES (JSON array) > GITHUB_SCRAPING_QUERY (single string).
// Returns an error instead of calling log.Fatal so it can be tested.
func parseQueriesFromEnv() ([]string, error) {
	if raw := os.Getenv("GITHUB_SCRAPING_QUERIES"); raw != "" {
		var queries []string
		if err := json.Unmarshal([]byte(raw), &queries); err != nil {
			return nil, fmt.Errorf("failed to parse GITHUB_SCRAPING_QUERIES as JSON array: %w", err)
		}
		if len(queries) == 0 {
			return nil, fmt.Errorf("GITHUB_SCRAPING_QUERIES is an empty array")
		}
		return queries, nil
	}
	if q := os.Getenv("GITHUB_SCRAPING_QUERY"); q != "" {
		return []string{q}, nil
	}
	return nil, fmt.Errorf("either GITHUB_SCRAPING_QUERIES or GITHUB_SCRAPING_QUERY must be set")
}

func main() {
	queries, err := parseQueriesFromEnv()
	if err != nil {
		log.Fatal(err)
	}
	log.Printf("[INFO] Running %d queries", len(queries))
	for i, q := range queries {
		log.Printf("[INFO]   query[%d]: %s", i, q)
	}

	token := os.Getenv("GITHUB_ACCESS_TOKEN")
	if token == "" {
		log.Println("[WARN] GITHUB_ACCESS_TOKEN not set; may hit rate limits")
	}

	apiURL := os.Getenv("GITHUB_API_URL")
	if apiURL == "" {
		apiURL = "https://api.github.com/search/repositories"
	}

	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		log.Fatal("DATABASE_URL is required")
	}

	maxRepos := 1000 // GitHub Search API hard limit per query
	perPage := 100   // GitHub API per_page limit

	// Top-level context — generous timeout for parallel queries
	ctx, cancel := context.WithTimeout(context.Background(), 8*time.Minute)
	defer cancel()

	pool, err := pgxpool.New(ctx, dbURL)
	if err != nil {
		log.Fatalf("Unable to create connection pool: %v", err)
	}
	defer pool.Close()

	client := newHTTPClient()
	rl := newSearchRateLimiter()
	start := time.Now()

	results := make([]queryResult, len(queries))
	var wg sync.WaitGroup

	for idx, q := range queries {
		wg.Add(1)
		go func(i int, query string) {
			defer wg.Done()
			results[i] = scrapeQuery(ctx, pool, client, rl, token, apiURL, query, maxRepos, perPage)
		}(idx, q)
	}

	wg.Wait()

	// Aggregate
	summary := scrapeSummary{
		Queries:         results,
		DurationSeconds: time.Since(start).Seconds(),
	}
	for _, r := range results {
		summary.TotalCollected += r.CollectedCount
		summary.TotalUpserted += r.UpsertedCount
		summary.TotalFailed += r.FailedUpserts
	}

	summary.Status = "success"
	if summary.TotalFailed > 0 {
		summary.Status = "partial"
	}

	if err := json.NewEncoder(os.Stdout).Encode(summary); err != nil {
		log.Fatalf("json encode: %v", err)
	}
}
