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

// mustGetEnv returns the env var or an error if empty
func mustGetEnv(key string) (string, error) {
	v := os.Getenv(key)
	if v == "" {
		return "", fmt.Errorf("%s is required", key)
	}
	return v, nil
}

// Load configuration from environment variables (strict, no defaults)
func loadConfig() (Config, error) {
	// Optional: environment name (for logs only)
	env := os.Getenv("ENVIRONMENT")

	// Required variables (no defaults)
	dbURL, err := mustGetEnv("DATABASE_URL")
	if err != nil {
		return Config{}, err
	}

	portStr, err := mustGetEnv("GO_API_PORT")
	if err != nil {
		return Config{}, err
	}
	port, err := strconv.Atoi(portStr)
	if err != nil || port <= 0 {
		return Config{}, fmt.Errorf("invalid GO_API_PORT: %q", portStr)
	}

	topNStr, err := mustGetEnv("RECOMMENDATION_TOP_N")
	if err != nil {
		return Config{}, err
	}
	topN, err := strconv.Atoi(topNStr)
	if err != nil || topN <= 0 {
		return Config{}, fmt.Errorf("invalid RECOMMENDATION_TOP_N: %q", topNStr)
	}

	minSimStr, err := mustGetEnv("RECOMMENDATION_MIN_SIMILARITY")
	if err != nil {
		return Config{}, err
	}
	minSim, err := strconv.ParseFloat(minSimStr, 64)
	if err != nil || minSim < 0 || minSim > 1 {
		return Config{}, fmt.Errorf("invalid RECOMMENDATION_MIN_SIMILARITY: %q", minSimStr)
	}

	cacheTTLStr, err := mustGetEnv("CACHE_TTL")
	if err != nil {
		return Config{}, err
	}
	cacheTTL, err := strconv.Atoi(cacheTTLStr)
	if err != nil || cacheTTL < 0 {
		return Config{}, fmt.Errorf("invalid CACHE_TTL: %q", cacheTTLStr)
	}

	cacheEnabledStr, err := mustGetEnv("CACHE_ENABLED")
	if err != nil {
		return Config{}, err
	}
	cacheEnabled := cacheEnabledStr == "true" || cacheEnabledStr == "1"

	return Config{
		DatabaseURL:          dbURL,
		RecommendationTopN:   topN,
		RecommendationMinSim: minSim,
		CacheEnabled:         cacheEnabled,
		CacheTTL:             cacheTTL,
		Port:                 port,
		Env:                  env,
	}, nil
}
