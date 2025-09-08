package main

import (
	"fmt"
	"os"
	"strconv"
)

// Configuration from environment variables
type Config struct {
	DatabaseURL          string
	RecommendationTopN   int
	RecommendationMinSim float64
	CacheEnabled         bool
	CacheTTL             int
	Port                 int
	Env                  string
}

// Get environment variable with default
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// defaultIfEmpty returns d if v is empty, otherwise v
func defaultIfEmpty(v, d string) string {
	if v == "" {
		return d
	}
	return v
}

// Load configuration from environment variables (strict validation)
func loadConfig() (Config, error) {
	env := getEnv("ENVIRONMENT", "development")

	// Recommendation parameters
	topNStr := os.Getenv("RECOMMENDATION_TOP_N")
	topN, err := strconv.Atoi(defaultIfEmpty(topNStr, "5"))
	if err != nil || topN <= 0 {
		return Config{}, fmt.Errorf("invalid RECOMMENDATION_TOP_N: %q", topNStr)
	}

	minSimStr := os.Getenv("RECOMMENDATION_MIN_SIMILARITY")
	minSim, err := strconv.ParseFloat(defaultIfEmpty(minSimStr, "0.1"), 64)
	if err != nil || minSim < 0 || minSim > 1 {
		return Config{}, fmt.Errorf("invalid RECOMMENDATION_MIN_SIMILARITY: %q", minSimStr)
	}

	cacheTTLStr := os.Getenv("CACHE_TTL")
	cacheTTL, err := strconv.Atoi(defaultIfEmpty(cacheTTLStr, "3600"))
	if err != nil || cacheTTL < 0 {
		return Config{}, fmt.Errorf("invalid CACHE_TTL: %q", cacheTTLStr)
	}

	// Database URL: required in non-development
	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		if env != "development" {
			return Config{}, fmt.Errorf("DATABASE_URL is required in %s", env)
		}
		// Build database URL from individual components for better compatibility in dev
		dbHost := getEnv("POSTGRES_HOST", "localhost")
		dbPort := getEnv("POSTGRES_PORT", "5434")
		dbUser := getEnv("POSTGRES_USER", "user")
		dbPassword := getEnv("POSTGRES_PASSWORD", "password")
		dbName := getEnv("POSTGRES_DB", "OST_PROD")
		dbURL = fmt.Sprintf("postgresql://%s:%s@%s:%s/%s?sslmode=disable", dbUser, dbPassword, dbHost, dbPort, dbName)
	}

	// Port: required in non-development
	portStr := os.Getenv("GO_API_PORT")
	if portStr == "" && env != "development" {
		return Config{}, fmt.Errorf("GO_API_PORT is required in %s", env)
	}
	port, err := strconv.Atoi(defaultIfEmpty(portStr, "8080"))
	if err != nil || port <= 0 {
		return Config{}, fmt.Errorf("invalid GO_API_PORT: %q", portStr)
	}

	return Config{
		DatabaseURL:          dbURL,
		RecommendationTopN:   topN,
		RecommendationMinSim: minSim,
		CacheEnabled:         getEnv("CACHE_ENABLED", "true") == "true",
		CacheTTL:             cacheTTL,
		Port:                 port,
		Env:                  env,
	}, nil
}
