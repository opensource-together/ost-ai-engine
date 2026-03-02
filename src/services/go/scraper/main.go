package main

import (
	"context"
	"encoding/json"
	"errors"
	"log"
	"os"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"gopkg.in/yaml.v3"
)

type scraperConfig struct {
	DatabaseURL         string `yaml:"DATABASE_URL"`
	GitHubAccessToken   string `yaml:"GITHUB_ACCESS_TOKEN"`
	GitHubScrapingQuery string `yaml:"GITHUB_SCRAPING_QUERY"`
	GitHubTopN          int    `yaml:"GITHUB_TOP_N"`
	GitHubApiUrl        string `yaml:"GITHUB_API_URL"`
	GitHubPerPage       int    `yaml:"GITHUB_PER_PAGE"`
}

func main() {
	configPath := os.Getenv("OST_CONFIG_PATH")
	if configPath == "" {
		log.Println("[WARN] OST_CONFIG_PATH not set, using default config/cfg.yaml logic or env vars might be needed.")
	}

	var config scraperConfig

	if configPath != "" {
		configBytes, err := os.ReadFile(configPath)
		if err == nil {
			if err := yaml.Unmarshal(configBytes, &config); err != nil {
				log.Printf("[WARN] Config file parse error: %v", err)
			} else {
				log.Println("[INFO] Loaded config from file.")
			}
		}
	}

	if dbURL := os.Getenv("DATABASE_URL"); dbURL != "" {
		config.DatabaseURL = dbURL
	}
	if token := os.Getenv("GITHUB_ACCESS_TOKEN"); token != "" {
		config.GitHubAccessToken = token
	}
	if query := os.Getenv("GITHUB_SCRAPING_QUERY"); query != "" {
		config.GitHubScrapingQuery = query
	}

	log.Printf("[INFO] Query: %s", config.GitHubScrapingQuery)

	token := config.GitHubAccessToken
	if token == "" {
		log.Println("warning: GITHUB_ACCESS_TOKEN not set; may hit rate limits")
	}
	query := config.GitHubScrapingQuery
	if query == "" {
		log.Fatal("GITHUB_SCRAPING_QUERY is required")
	}
	apiURL := config.GitHubApiUrl
	if apiURL == "" {
		apiURL = "https://api.github.com/search/repositories"
	}

	maxRepos := config.GitHubTopN
	if maxRepos <= 0 {
		maxRepos = 1000
	}
	if maxRepos > 1000 {
		maxRepos = 1000 // GitHub Search API hard limit
	}

	if config.DatabaseURL == "" {
		log.Fatal("DATABASE_URL is required")
	}

	// Top-level context with 4min timeout (Python subprocess timeout is 5min)
	ctx, cancel := context.WithTimeout(context.Background(), 4*time.Minute)
	defer cancel()

	conn, err := pgx.Connect(ctx, config.DatabaseURL)
	if err != nil {
		log.Fatalf("Unable to connect to database: %v", err)
	}
	defer conn.Close(context.Background())

	client := newHTTPClient()
	perPage := config.GitHubPerPage
	if perPage <= 0 {
		perPage = 100
	}
	if perPage > 100 {
		perPage = 100 // GitHub API limit
	}

	collected := 0
	upserted := 0
	failedUpserts := 0
	start := time.Now()

	log.Println("[INFO] Starting scrape loop...")

	const maxRetries = 3

	for page := 1; collected < maxRepos; page++ {
		var res githubSearchResponse
		var fetchErr error
		for attempt := 1; attempt <= maxRetries; attempt++ {
			res, fetchErr = fetchGitHubRepos(ctx, client, token, apiURL, query, perPage, page)
			if fetchErr == nil {
				break
			}

			var rlErr *rateLimitError
			if errors.As(fetchErr, &rlErr) {
				log.Printf("[WARN] Rate limited, sleeping %s before retry", rlErr.RetryAfter)
				time.Sleep(rlErr.RetryAfter)
				continue
			}

			if attempt < maxRetries {
				backoff := time.Duration(attempt) * 2 * time.Second
				log.Printf("[WARN] GitHub fetch attempt %d/%d failed: %v, retrying in %s", attempt, maxRetries, fetchErr, backoff)
				time.Sleep(backoff)
			}
		}
		if fetchErr != nil {
			log.Printf("[ERROR] GitHub fetch failed after %d retries: %v, stopping with partial results", maxRetries, fetchErr)
			break
		}

		if len(res.Items) == 0 {
			break
		}

		if res.IncompleteResults {
			log.Printf("[WARN] GitHub returned incomplete results for page %d", page)
		}

		// Batch upsert via SendBatch
		batch := &pgx.Batch{}
		for _, repo := range res.Items {
			repoData, err := json.Marshal(repo)
			if err != nil {
				log.Printf("Error marshaling repo %s: %v", repo.Name, err)
				failedUpserts++
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
			br := conn.SendBatch(dbCtx, batch)
			for i := 0; i < batch.Len(); i++ {
				_, err := br.Exec()
				if err != nil {
					log.Printf("Failed to upsert repo (batch item %d): %v", i, err)
					failedUpserts++
				} else {
					upserted++
				}
			}
			br.Close()
			dbCancel()
		}

		collected += len(res.Items)
		log.Printf("[INFO] Collected %d / %d", collected, maxRepos)
	}

	status := "success"
	if failedUpserts > 0 {
		status = "partial"
	}

	summary := map[string]interface{}{
		"collected_count":  collected,
		"upserted_count":   upserted,
		"failed_upserts":   failedUpserts,
		"status":           status,
		"duration_seconds": time.Since(start).Seconds(),
	}
	if err := json.NewEncoder(os.Stdout).Encode(summary); err != nil {
		log.Fatalf("json encode: %v", err)
	}
}
