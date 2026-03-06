package main

import (
	"context"
	"flag"
	"log"
	"os"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/joho/godotenv"
)

type Config struct {
	DatabaseURL string
	GithubToken string
}

func loadConfig() *Config {
	_ = godotenv.Load()

	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		log.Fatal("DATABASE_URL is required")
	}

	return &Config{
		DatabaseURL: dbURL,
		GithubToken: os.Getenv("GITHUB_ACCESS_TOKEN"),
	}
}

func main() {
	mode := flag.String("mode", "", "Fetch mode: readme, languages, topics")
	limit := flag.Int("limit", 0, "Limit number of projects to process (0 = no limit)")
	concurrency := flag.Int("concurrency", 10, "Number of concurrent workers")
	flag.Parse()

	// Validate mode before connecting to DB so log.Fatal doesn't skip defer db.Close()
	validModes := map[string]bool{"readme": true, "languages": true, "topics": true}
	if *mode == "" {
		log.Fatal("Please specify --mode (readme, languages, topics)")
	}
	if !validModes[*mode] {
		log.Fatalf("Unknown mode: %s (valid: readme, languages, topics)", *mode)
	}

	cfg := loadConfig()

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Minute)
	defer cancel()

	db, err := pgxpool.New(ctx, cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("Unable to connect to database: %v", err)
	}
	defer db.Close()

	log.Printf("Starting fetcher in mode: %s (concurrency: %d)", *mode, *concurrency)

	fetcher := NewGitHubFetcher(db, cfg.GithubToken, *concurrency)

	start := time.Now()
	var count int
	var errFetch error

	switch *mode {
	case "readme":
		count, errFetch = fetcher.FetchReadmes(ctx, *limit)
	case "languages":
		count, errFetch = fetcher.FetchLanguages(ctx, *limit)
	case "topics":
		count, errFetch = fetcher.FetchTopics(ctx, *limit)
	}

	if errFetch != nil {
		log.Printf("[ERROR] Job failed: %v", errFetch)
		os.Exit(1)
	}

	duration := time.Since(start)
	log.Printf("[SUCCESS] Processed %d items in %s", count, duration)
}
