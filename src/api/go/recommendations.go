package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	_ "github.com/lib/pq"
)

// Configuration from environment variables
type Config struct {
	DatabaseURL          string
	RecommendationTopN   int
	RecommendationMinSim float64
	CacheEnabled         bool
	CacheTTL             int
}

// Project recommendation structure
type ProjectRecommendation struct {
	ProjectID          string   `json:"project_id"`
	Title              string   `json:"title"`
	Description        string   `json:"description"`
	SimilarityScore    float64  `json:"similarity_score"`
	SemanticSimilarity float64  `json:"semantic_similarity"`
	CategorySimilarity float64  `json:"category_similarity"`
	TechSimilarity     float64  `json:"tech_similarity"`
	PopularityScore    float64  `json:"popularity_score"`
	StargazersCount    int      `json:"stargazers_count"`
	PrimaryLanguage    string   `json:"primary_language"`
	Categories         []string `json:"categories"`
	TechStacks         []string `json:"tech_stacks"`
}

// API response structure
type RecommendationsResponse struct {
	UserID          string                  `json:"user_id"`
	Username        string                  `json:"username"`
	Recommendations []ProjectRecommendation `json:"recommendations"`
	TotalCount      int                     `json:"total_count"`
	GeneratedAt     string                  `json:"generated_at"`
}

// Load configuration from environment variables
func loadConfig() Config {
	topN, _ := strconv.Atoi(getEnv("RECOMMENDATION_TOP_N", "5"))
	minSim, _ := strconv.ParseFloat(getEnv("RECOMMENDATION_MIN_SIMILARITY", "0.1"), 64)
	cacheTTL, _ := strconv.Atoi(getEnv("CACHE_TTL", "3600"))

	// Build database URL from individual components for better compatibility
	dbHost := getEnv("POSTGRES_HOST", "localhost")
	dbPort := getEnv("POSTGRES_PORT", "5434")
	dbUser := getEnv("POSTGRES_USER", "user")
	dbPassword := getEnv("POSTGRES_PASSWORD", "password")
	dbName := getEnv("POSTGRES_DB", "OST_PROD")

	databaseURL := fmt.Sprintf("postgresql://%s:%s@%s:%s/%s?sslmode=disable",
		dbUser, dbPassword, dbHost, dbPort, dbName)

	return Config{
		DatabaseURL:          getEnv("DATABASE_URL", databaseURL),
		RecommendationTopN:   topN,
		RecommendationMinSim: minSim,
		CacheEnabled:         getEnv("CACHE_ENABLED", "true") == "true",
		CacheTTL:             cacheTTL,
	}
}

// Get environment variable with default
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// Parse PostgreSQL array string to slice
func parseArray(arrayStr string) []string {
	if arrayStr == "" || arrayStr == "{}" {
		return []string{}
	}
	// Remove curly braces and split by comma
	clean := strings.Trim(arrayStr, "{}")
	if clean == "" {
		return []string{}
	}
	return strings.Split(clean, ",")
}

// Get recommendations for a user
func getRecommendations(db *sql.DB, config Config, userID string) (*RecommendationsResponse, error) {
	query := `
		SELECT 
			ups.project_id,
			p.title,
			p.description,
			ups.similarity_score,
			ups.semantic_similarity,
			ups.category_similarity,
			ups.language_similarity as tech_similarity,
			ups.popularity_similarity as popularity_score,
			p.stargazers_count,
			p.primary_language,
			array_agg(DISTINCT c.name) as categories,
			array_agg(DISTINCT ts.name) as tech_stacks
		FROM "USER_PROJECT_SIMILARITY" ups
		JOIN "PROJECT" p ON ups.project_id = p.id
		LEFT JOIN "PROJECT_CATEGORY" pc ON p.id = pc.project_id
		LEFT JOIN "CATEGORY" c ON pc.category_id = c.id
		LEFT JOIN "PROJECT_TECH_STACK" pts ON p.id = pts.project_id
		LEFT JOIN "TECH_STACK" ts ON pts.tech_stack_id = ts.id
		WHERE ups.user_id = $1 
		AND ups.similarity_score >= $2
		GROUP BY ups.project_id, p.title, p.description, ups.similarity_score, 
				 ups.semantic_similarity, ups.category_similarity, ups.language_similarity, 
				 ups.popularity_similarity, p.stargazers_count, p.primary_language
		ORDER BY ups.similarity_score DESC
		LIMIT $3
	`

	rows, err := db.Query(query, userID, config.RecommendationMinSim, config.RecommendationTopN)
	if err != nil {
		return nil, fmt.Errorf("database query error: %v", err)
	}
	defer rows.Close()

	var recommendations []ProjectRecommendation
	for rows.Next() {
		var rec ProjectRecommendation
		var categories, techStacks sql.NullString

		err := rows.Scan(
			&rec.ProjectID,
			&rec.Title,
			&rec.Description,
			&rec.SimilarityScore,
			&rec.SemanticSimilarity,
			&rec.CategorySimilarity,
			&rec.TechSimilarity,
			&rec.PopularityScore,
			&rec.StargazersCount,
			&rec.PrimaryLanguage,
			&categories,
			&techStacks,
		)
		if err != nil {
			return nil, fmt.Errorf("row scan error: %v", err)
		}

		// Parse arrays properly
		if categories.Valid {
			rec.Categories = parseArray(categories.String)
		}
		if techStacks.Valid {
			rec.TechStacks = parseArray(techStacks.String)
		}

		recommendations = append(recommendations, rec)
	}

	// Get user info
	var username string
	err = db.QueryRow("SELECT username FROM \"USER\" WHERE id = $1", userID).Scan(&username)
	if err != nil {
		return nil, fmt.Errorf("user lookup error: %v", err)
	}

	return &RecommendationsResponse{
		UserID:          userID,
		Username:        username,
		Recommendations: recommendations,
		TotalCount:      len(recommendations),
		GeneratedAt:     time.Now().UTC().Format(time.RFC3339),
	}, nil
}

// HTTP handler for health check endpoint
func healthHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"status":    "healthy",
			"timestamp": time.Now().UTC().Format(time.RFC3339),
		})
	}
}

// HTTP handler for recommendations endpoint
func recommendationsHandler(db *sql.DB, config Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Extract user_id from URL path
		userID := r.URL.Query().Get("user_id")
		if userID == "" {
			http.Error(w, "user_id parameter is required", http.StatusBadRequest)
			return
		}

		// Get recommendations
		response, err := getRecommendations(db, config, userID)
		if err != nil {
			log.Printf("Error getting recommendations: %v", err)
			http.Error(w, "Internal server error", http.StatusInternalServerError)
			return
		}

		// Return JSON response
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(response)
	}
}

func main() {
	// Load configuration
	config := loadConfig()
	log.Printf("Configuration loaded: TOP_N=%d, MIN_SIM=%.2f", config.RecommendationTopN, config.RecommendationMinSim)

	// Connect to database
	db, err := sql.Open("postgres", config.DatabaseURL)
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer db.Close()

	// Test database connection
	err = db.Ping()
	if err != nil {
		log.Fatalf("Failed to ping database: %v", err)
	}
	log.Println("✅ Database connection established")

	// Setup HTTP routes
	http.HandleFunc("/health", healthHandler())
	http.HandleFunc("/recommendations", recommendationsHandler(db, config))

	// Start server
	port := getEnv("GO_API_PORT", "8080")
	log.Printf("🚀 Starting recommendation API server on port %s", port)
	log.Printf("📊 Using RECOMMENDATION_TOP_N=%d from environment", config.RecommendationTopN)

	err = http.ListenAndServe(":"+port, nil)
	if err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
