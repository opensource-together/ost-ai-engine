package main

import (
	"context"
	"encoding/json"
	"log"
	"os"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"gopkg.in/yaml.v3"
)

func main() {
	configPath := os.Getenv("OST_CONFIG_PATH")
	if configPath == "" {
		log.Println("[WARN] OST_CONFIG_PATH not set, using default config/cfg.yaml logic or env vars might be needed.")
	}

	var config struct {
		DatabaseURL         string `yaml:"DATABASE_URL"`
		GitHubAccessToken   string `yaml:"GITHUB_ACCESS_TOKEN"`
		GitHubScrapingQuery string `yaml:"GITHUB_SCRAPING_QUERY"`
		GitHubTopN          int    `yaml:"GITHUB_TOP_N"`
		GitHubApiUrl        string `yaml:"GITHUB_API_URL"`
		GitHubPerPage       int    `yaml:"GITHUB_PER_PAGE"`
	}

	// Attempt to load from file if present
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

	// Override/Fallback with Env Vars if set
	if dbURL := os.Getenv("DATABASE_URL"); dbURL != "" {
		config.DatabaseURL = dbURL
	}
	if token := os.Getenv("GITHUB_ACCESS_TOKEN"); token != "" {
		config.GitHubAccessToken = token
	}
	// GITHUB_SCRAPING_QUERY is often passed in generated cfg.yaml, but can be env
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
		maxRepos = 1000 // Github API limit is 1000
	}

	// Connect to DB
	if config.DatabaseURL == "" {
		log.Fatal("DATABASE_URL is required")
	}
	conn, err := pgx.Connect(context.Background(), config.DatabaseURL)
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

	log.Println("[INFO] Starting scrape loop...")

	for page := 1; collected < maxRepos; page++ {
		res, err := fetchGitHubRepos(client, token, apiURL, query, perPage, page)
		if err != nil {
			log.Fatalf("github fetch: %v", err)
		}
		if len(res.Items) == 0 {
			break
		}

		// Batch insert/upsert
		// We do one by one or batch? one by one is fine for 1000 items.
		for _, repo := range res.Items {
			repoData, err := json.Marshal(repo)
			if err != nil {
				log.Printf("Error marshaling repo %s: %v", repo.Name, err)
				continue
			}

			// Generate UUID v5 from URL
			// NamespaceURL is 6ba7b811-9dad-11d1-80b4-00c04fd430c8
			// Project logic: uuid.uuid5(uuid.NAMESPACE_URL, url)
			url := repo.HTMLURL
			if url == "" {
				continue
			}

			id := uuid.NewSHA1(uuid.NameSpaceURL, []byte(url))

			sql := `
                INSERT INTO "github"."raw_github_project" ("id", "data", "createdAt", "updatedAt")
                VALUES ($1, $2, NOW(), NOW())
                ON CONFLICT ("id") DO UPDATE 
                SET "data" = EXCLUDED."data",
                    "updatedAt" = NOW()
            `
			_, err = conn.Exec(context.Background(), sql, id.String(), repoData)
			if err != nil {
				log.Printf("Failed to upsert repo %s: %v", repo.Name, err)
			} else {
				upserted++
			}
		}

		collected += len(res.Items)
		log.Printf("[INFO] Collected %d / %d", collected, maxRepos)
	}

	summary := map[string]interface{}{
		"collected_count": collected,
		"upserted_count":  upserted,
		"status":          "success",
	}
	if err := json.NewEncoder(os.Stdout).Encode(summary); err != nil {
		log.Fatalf("json encode: %v", err)
	}
}
