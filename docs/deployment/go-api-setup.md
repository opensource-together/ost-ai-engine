# Go API Setup

## Overview

The OST Data Engine uses a Go API for serving project recommendations. The Go API is designed for high performance and low latency, serving pre-calculated similarity scores from the ML pipeline.

## Project Structure

```
src/api/go/
├── Dockerfile              # Multi-stage Docker build
├── go.mod                  # Go module definition
├── go.sum                  # Go dependencies checksum
└── recommendations.go      # Main API implementation
```

## Prerequisites

- **Go 1.24+**
- **PostgreSQL 15+** with pgvector extension
- **Docker** (optional, for containerized deployment)

## Local Development

### 1. Install Go

```bash
# macOS
brew install go

# Ubuntu/Debian
sudo apt-get install golang-go

# Windows
# Download from https://golang.org/dl/
```

### 2. Setup Go Environment

```bash
# Set GOPATH (if not already set)
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin

# Verify installation
go version
```

### 3. Build and Run

```bash
# Navigate to Go API directory
cd src/api/go

# Download dependencies
go mod download

# Build the application
go build -o recommendations-api recommendations.go

# Run the API
./recommendations-api
```

## Docker Deployment

### 1. Build Docker Image

```bash
# From project root
docker-compose build go-api

# Or manually
cd src/api/go
docker build -t ost-go-api .
```

### 2. Run with Docker Compose

```bash
# Start all services
docker-compose up -d

# Start only Go API
docker-compose up go-api

# View logs
docker-compose logs -f go-api
```

### 3. Environment Variables

The Go API uses these environment variables:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5434/OST_PROD

# API Configuration
GO_API_PORT=8080

# GitHub (for future features)
GITHUB_ACCESS_TOKEN=your_github_token

# Logging
LOG_LEVEL=INFO
```

## API Endpoints

### Health Check

```bash
curl http://localhost:8080/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Get Recommendations

```bash
curl "http://localhost:8080/recommendations?user_id=user123"
```

Response:
```json
{
  "user_id": "user123",
  "recommendations": [
    {
      "project_id": "proj1",
      "project_title": "Example Project",
      "similarity_score": 0.85,
      "semantic_similarity": 0.75,
      "category_similarity": 0.90,
      "tech_similarity": 0.80,
      "popularity_score": 0.70
    }
  ],
  "generated_at": "2024-01-15T10:30:00Z"
}
```

## Configuration

### Database Connection

The Go API connects to PostgreSQL using the `DATABASE_URL` environment variable:

```env
DATABASE_URL=postgresql://username:password@host:port/database?sslmode=disable
```

### Port Configuration

Default port is 8080, but can be changed via `GO_API_PORT`:

```env
GO_API_PORT=8080
```

### Logging

Configure logging level:

```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

## Performance Optimization

### 1. Go Runtime Settings

```bash
# Set number of CPU cores
export GOMAXPROCS=4

# Garbage collection tuning
export GOGC=100

# Memory allocation
export GO_MEMLIMIT=1GiB
```

### 2. Database Optimization

```sql
-- Increase connection pool
SET max_connections = 100;

-- Optimize for vector operations
SET work_mem = '256MB';
SET shared_buffers = '1GB';
```

### 3. Docker Optimization

```dockerfile
# Use multi-stage build
FROM golang:1.24-alpine AS builder
# ... build steps

FROM alpine:latest
# ... runtime steps

# Set resource limits
ENV GOMAXPROCS=4
ENV GOGC=100
```

## Monitoring

### Health Checks

The API includes built-in health checks:

```bash
# Basic health check
curl http://localhost:8080/health

# With timeout
curl --max-time 5 http://localhost:8080/health
```

### Logging

Logs are written to stdout/stderr for Docker compatibility:

```bash
# View logs
docker-compose logs -f go-api

# Filter by level
docker-compose logs go-api | grep "ERROR"
```

### Metrics (Future)

Planned metrics endpoints:

```bash
# Metrics endpoint (future)
curl http://localhost:8080/metrics
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check database URL
   echo $DATABASE_URL
   
   # Test connection
   psql $DATABASE_URL -c "SELECT 1;"
   ```

2. **Port Already in Use**
   ```bash
   # Check port usage
   lsof -i :8080
   
   # Change port
   export GO_API_PORT=8081
   ```

3. **Go Module Issues**
   ```bash
   # Clean module cache
   go clean -modcache
   
   # Re-download dependencies
   go mod download
   ```

4. **Docker Build Issues**
   ```bash
   # Clean Docker cache
   docker system prune -a
   
   # Rebuild without cache
   docker-compose build --no-cache go-api
   ```

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
./recommendations-api
```

## Security Considerations

1. **Database Security**
   - Use strong passwords
   - Enable SSL connections in production
   - Use connection pooling

2. **API Security**
   - Implement rate limiting (future)
   - Add authentication (future)
   - Validate all inputs

3. **Container Security**
   - Run as non-root user
   - Use minimal base images
   - Scan for vulnerabilities

## Development Workflow

### 1. Code Changes

```bash
# Make changes to recommendations.go
nano src/api/go/recommendations.go

# Test locally
go run recommendations.go

# Build and test
go build -o recommendations-api recommendations.go
./recommendations-api
```

### 2. Docker Testing

```bash
# Rebuild and test
docker-compose build go-api
docker-compose up go-api

# Test API
curl http://localhost:8080/health
```

### 3. Integration Testing

```bash
# Test with real data
curl "http://localhost:8080/recommendations?user_id=test_user"

# Verify response format
curl "http://localhost:8080/recommendations?user_id=test_user" | jq
```

## Next Steps

1. **Add Authentication**: Implement API key or JWT authentication
2. **Add Rate Limiting**: Protect against abuse
3. **Add Metrics**: Prometheus metrics endpoint
4. **Add Caching**: In-memory or external caching for frequently accessed data
5. **Add Load Balancing**: Multiple API instances behind a load balancer
