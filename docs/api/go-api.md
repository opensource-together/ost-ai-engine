# Go API Implementation

## Overview

The Go API is a high-performance REST server that serves project recommendations by querying pre-calculated similarity scores from PostgreSQL.

## Architecture

```
HTTP Request → Go Handler → PostgreSQL Query → JSON Response
```

## Key Features

- **High Performance**: Direct SQL queries with optimized indexes
- **Environment Configuration**: All settings via environment variables
- **Error Handling**: Comprehensive error handling and logging
- **Array Parsing**: Proper PostgreSQL array parsing
- **SSL Configuration**: Configurable database SSL settings

## Code Structure

### Main Components

1. **Configuration Management** (`loadConfig()`)
2. **Database Connection** (PostgreSQL with pgvector)
3. **HTTP Handlers** (`recommendationsHandler()`)
4. **Query Logic** (`getRecommendations()`)
5. **Array Parsing** (`parseArray()`)

### Key Functions

#### Configuration Loading
```go
func loadConfig() Config {
    topN, _ := strconv.Atoi(getEnv("RECOMMENDATION_TOP_N", "5"))
    minSim, _ := strconv.ParseFloat(getEnv("RECOMMENDATION_MIN_SIMILARITY", "0.1"), 64)
    // ... more configuration
}
```

#### Database Query
```go
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
    // ... query execution
}
```

#### Array Parsing
```go
func parseArray(arrayStr string) []string {
    if arrayStr == "" || arrayStr == "{}" {
        return []string{}
    }
    clean := strings.Trim(arrayStr, "{}")
    return strings.Split(clean, ",")
}
```

## Database Schema

The API queries the following tables:

### USER_PROJECT_SIMILARITY
```sql
CREATE TABLE "USER_PROJECT_SIMILARITY" (
    user_id UUID REFERENCES "USER"(id),
    project_id UUID REFERENCES "PROJECT"(id),
    similarity_score FLOAT NOT NULL,
    semantic_similarity FLOAT,
    category_similarity FLOAT,
    language_similarity FLOAT,
    popularity_similarity FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, project_id)
);
```

### Indexes
```sql
CREATE INDEX idx_user_project_similarity_score ON "USER_PROJECT_SIMILARITY" (user_id, similarity_score);
CREATE INDEX idx_user_project_similarity_user ON "USER_PROJECT_SIMILARITY" (user_id);
CREATE INDEX idx_user_project_similarity_project ON "USER_PROJECT_SIMILARITY" (project_id);
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://user:password@localhost:port/db_name?sslmode=disable` | PostgreSQL connection string |
| `RECOMMENDATION_TOP_N` | — | Number of recommendations to return (required) |
| `RECOMMENDATION_MIN_SIMILARITY` | — | Minimum similarity threshold (required) |
| `GO_API_PORT` | — | API server port (required) |

Note: The API does not use default values in production/dev; all required variables must be provided at runtime (Docker/K8s/systemd/shell). The process will exit with a clear error if any are missing or invalid.


## Build and Run

### Development
```bash
cd src/api/go
go run recommendations.go
```

### Production
```bash
cd src/api/go
go build -o recommendations-api recommendations.go
./recommendations-api
```

### Docker (if needed)
```dockerfile
FROM golang:1.24-alpine
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o recommendations-api recommendations.go
EXPOSE 8080
CMD ["./recommendations-api"]
```

## Performance Optimizations

1. **Indexed Queries**: All queries use indexed columns
2. **Connection Pooling**: SQL driver handles connection pooling
3. **Prepared Statements**: Queries are prepared for reuse
4. **Efficient Parsing**: Optimized array parsing
5. **Memory Management**: Proper resource cleanup

## Error Handling

### Database Errors
- Connection failures
- Query execution errors
- User not found errors

### HTTP Errors
- Missing required parameters
- Invalid user IDs
- Internal server errors

### Logging
```go
log.Printf("Configuration loaded: TOP_N=%d, MIN_SIM=%.2f", config.RecommendationTopN, config.RecommendationMinSim)
log.Printf("Error getting recommendations: %v", err)
```

## Security Considerations

1. **Input Validation**: User ID validation
2. **SQL Injection**: Parameterized queries
3. **Error Exposure**: Generic error messages in production
4. **SSL Configuration**: Configurable database SSL

## Monitoring

### Health Check Endpoint
Consider adding a health check endpoint:
```go
http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
    if err := db.Ping(); err != nil {
        http.Error(w, "Database connection failed", http.StatusServiceUnavailable)
        return
    }
    w.WriteHeader(http.StatusOK)
    w.Write([]byte("OK"))
})
```

### Metrics
Consider adding Prometheus metrics for:
- Request count
- Response time
- Error rate
- Database connection status

## Future Enhancements

1. **Caching**: In-memory or external caching for frequently accessed data
2. **Rate Limiting**: Request rate limiting
3. **Authentication**: JWT or API key authentication
4. **Pagination**: Support for large result sets
5. **Filtering**: Additional query parameters for filtering
