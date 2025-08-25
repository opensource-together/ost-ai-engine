# GitHub Scraper Service (Go)

Go service for scraping GitHub repositories with Dagster integration.

## Architecture

```
github-scraper/
├── main.go          # Entry point, CLI parsing, orchestration
├── scraper.go       # Business logic, GitHub API, enrichment
├── go.mod           # Dependencies and module configuration
├── go.sum           # Version locking
└── README.md        # Documentation
```

## Configuration

### Environment Variables (.env)

The service automatically uses the `.env` file at the project root:

```bash
# GitHub API
GITHUB_ACCESS_TOKEN=your_github_token_here

# Optional configuration
GITHUB_RATE_LIMIT=5000
GITHUB_TIMEOUT=30s
```

### Command Line Arguments

```bash
./main --query "language:javascript stars:>500" --max-repos 30 --token $GITHUB_TOKEN
```

## Dagster Integration

The service is called as a subprocess from the `github_repositories` asset:

```python
# In github_assets.py
cmd = [
    "./src/infrastructure/services/go/github-scraper/main",
    "--query", config.query,
    "--max-repos", str(config.max_repositories),
    "--output", "json"
]
```

## Best Practices Implemented

✅ **Separation of Concerns**
- `main.go`: Orchestration and configuration
- `scraper.go`: Business logic and API calls

✅ **Robust Error Handling**
- Retry logic for API calls
- Graceful degradation if enrichment fails

✅ **Flexible Configuration**
- Environment variables via `.env`
- CLI arguments for override
- Fallback to default values

✅ **Structured Logging**
- Informative logs with emojis
- Appropriate log levels
- End-of-execution statistics

✅ **Performance Optimized**
- Automatic pagination (100 repos per page)
- Parallel enrichment
- GitHub rate limit management

## Development

### Compilation

```bash
cd src/infrastructure/services/go/github-scraper
go mod tidy
go build -o main .
```

### Local Testing

```bash
# Test with GitHub token
./main --query "language:python stars:>1000" --max-repos 5

# Test without authentication (low rate limit)
./main --query "language:go" --max-repos 3
```

### Dependencies

- `github.com/google/go-github/v57`: Official GitHub client
- `github.com/joho/godotenv`: Environment variable loading
- `golang.org/x/oauth2`: OAuth2 authentication

## Metrics and Monitoring

The service generates structured logs for:
- Number of repositories processed
- Language distribution
- Star statistics
- Execution time
- Errors and warnings

## Future Improvements

- [ ] Unit tests with `testing`
- [ ] Prometheus metrics
- [ ] YAML configuration file
- [ ] Redis cache to avoid duplicates
- [ ] GitHub webhooks support
