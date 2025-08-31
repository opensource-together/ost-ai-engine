package main

import (
	"encoding/json"
	"flag"
	"log"
	"os"
	"runtime"
	"strconv"
	"time"

	"github.com/joho/godotenv"
)

func init() {
	// Redirect logs to stderr so they don't interfere with JSON output
	log.SetOutput(os.Stderr)
}

// Config holds the scraper configuration
type Config struct {
	Query        string
	MaxRepos     int
	OutputFormat string
	Token        string
	DBURL        string
	UpsertToDB   bool
}

// Repository represents a GitHub repository with optimized memory layout
type Repository struct {
	FullName        string         `json:"full_name"`
	Name            string         `json:"name"`
	Owner           string         `json:"owner"`
	Description     string         `json:"description"`
	Fork            bool           `json:"fork"`
	Language        string         `json:"language"`
	StargazersCount int            `json:"stargazers_count"`
	WatchersCount   int            `json:"watchers_count"`
	ForksCount      int            `json:"forks_count"`
	OpenIssuesCount int            `json:"open_issues_count"`
	Topics          []string       `json:"topics"`
	Archived        bool           `json:"archived"`
	Disabled        bool           `json:"disabled"`
	CreatedAt       time.Time      `json:"created_at"`
	UpdatedAt       time.Time      `json:"updated_at"`
	PushedAt        time.Time      `json:"pushed_at"`
	Homepage        string         `json:"homepage"`
	License         string         `json:"license"`
	LanguagesMap    map[string]int `json:"languages_map"`
	Readme          string         `json:"readme"`
}

func main() {
	startTime := time.Now()

	// Set GOMAXPROCS for optimal performance
	runtime.GOMAXPROCS(runtime.NumCPU())

	// Load environment variables first
	loadEnv()

	// Parse command line flags (after env vars are loaded)
	config := parseFlags()

	// Create GitHub scraper with optimized settings
	scraper := NewGitHubScraper(config.Token)

	// Scrape repositories with error handling
	repositories, err := scraper.ScrapeRepositories(config.Query, config.MaxRepos)
	if err != nil {
		log.Fatalf("Failed to scrape repositories: %v", err)
	}

	// Upsert to DB if requested
	if config.UpsertToDB && config.DBURL != "" {
		if err := upsertRepositories(config.DBURL, repositories); err != nil {
			log.Fatalf("Failed to upsert repositories to DB: %v", err)
		}
		log.Printf("✅ Upserted %d repositories into database", len(repositories))
	}

	// Always output results as JSON for observability
	outputResults(repositories, config.OutputFormat)

	// Log execution time
	log.Printf("🚀 Total execution time: %v", time.Since(startTime))
}

// parseFlags parses command line arguments with validation
func parseFlags() *Config {
	// Get default max repos from environment variable
	defaultMaxRepos := 30
	if envMaxRepos := os.Getenv("GITHUB_MAX_REPOSITORIES"); envMaxRepos != "" {
		if parsed, err := strconv.Atoi(envMaxRepos); err == nil && parsed > 0 {
			defaultMaxRepos = parsed
		}
	}

	query := flag.String("query", "language:javascript stars:>500", "GitHub search query")
	maxRepos := flag.Int("max-repos", defaultMaxRepos, "Maximum number of repositories to scrape")
	outputFormat := flag.String("output", "json", "Output format (json)")
	token := flag.String("token", "", "GitHub access token")
	// DB flags
	dbURL := flag.String("db-url", "", "Postgres connection URL")
	upsert := flag.Bool("upsert", false, "Upsert scraped repositories directly into the database")

	flag.Parse()

	// Validate input parameters with higher limit for environment-based config
	maxLimit := 2000
	if *maxRepos <= 0 || *maxRepos > maxLimit {
		log.Fatalf("max-repos must be between 1 and %d", maxLimit)
	}

	return &Config{
		Query:        *query,
		MaxRepos:     *maxRepos,
		OutputFormat: *outputFormat,
		Token:        *token,
		DBURL:        *dbURL,
		UpsertToDB:   *upsert,
	}
}

// loadEnv loads environment variables with error handling
func loadEnv() {
	// Load .env file if it exists
	if _, err := os.Stat(".env"); err == nil {
		if err := godotenv.Load(); err != nil {
			log.Printf("Warning: Failed to load .env file: %v", err)
		} else {
			log.Println("✅ Environment variables loaded from .env")
		}
	}

	// Validate GitHub token if provided
	if token := os.Getenv("GITHUB_ACCESS_TOKEN"); token != "" && token != "your_github_token_here" { // nolint:gosec // test token placeholder
		log.Println("✅ GitHub token found in environment")
	} else {
		log.Println("⚠️ No valid GitHub token found - using unauthenticated client")
	}
}

// outputResults outputs results in the specified format with error handling
func outputResults(repositories []Repository, format string) {
	switch format {
	case "json":
		// Use streaming JSON encoder for large datasets
		encoder := json.NewEncoder(os.Stdout)
		encoder.SetIndent("", "  ")

		if err := encoder.Encode(repositories); err != nil {
			log.Fatalf("Failed to marshal JSON: %v", err)
		}

		log.Printf("✅ Output %d repositories in JSON format", len(repositories))
	default:
		log.Fatalf("Unsupported output format: %s", format)
	}
}
