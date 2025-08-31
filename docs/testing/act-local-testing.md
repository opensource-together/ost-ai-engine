# Testing CI Locally with Act

This document explains how to test GitHub Actions workflows locally using [act](https://github.com/nektos/act).

## Prerequisites

1. **Install act**:
   ```bash
   # macOS
   brew install act
   
   # Linux
   curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
   
   # Windows
   choco install act-cli
   ```

2. **Docker running**: Make sure Docker is running on your system.

3. **Environment file**: Ensure `.env` file exists with all required variables.

## Configuration Files

### `.actrc`
Global configuration for act:
```bash
--container-architecture=linux/amd64
--container-options=--privileged
--env-file .env
```

### `scripts/tests/ci_local.py`
Unified script for testing CI jobs locally:
```bash
python scripts/tests/ci_local.py [job_name|all]
```

## Available Jobs

Our CI workflow has the following jobs:

1. **`setup`** - Initial setup with database and services
2. **`tests-unit`** - Unit tests
3. **`tests-integration`** - Integration tests with database
4. **`tests-performance`** - Performance tests with Go API
5. **`go-lint`** - Go code linting
6. **`coverage`** - Test coverage report

## Usage Examples

### Test a specific job
```bash
# Test unit tests only
python scripts/tests/ci_local.py tests-unit

# Test Go linter
python scripts/tests/ci_local.py go-lint

# Test integration tests
python scripts/tests/ci_local.py tests-integration
```

### Test all jobs
```bash
# Test all jobs in sequence
python scripts/tests/ci_local.py all

# Or test a specific job
python scripts/tests/ci_local.py tests-unit
```

### Direct act usage
```bash
# Test setup job
act -j setup --env-file .env

# Test with specific secrets
act -j tests-unit --secret-file .env --env-file .env
```

## Troubleshooting

### Common Issues

1. **Docker not running**:
   ```bash
   # Start Docker Desktop or Docker daemon
   sudo systemctl start docker  # Linux
   ```

2. **Permission issues**:
   ```bash
   # Make script executable
   chmod +x scripts/tests/ci_local.py
   ```

3. **Environment variables missing**:
   ```bash
   # Check if .env exists and has required variables
   cat .env
   ```

4. **Container architecture issues**:
   ```bash
   # For M1/M2 Macs, ensure you're using the right architecture
   # The .actrc file should handle this automatically
   ```

### Debug Mode

Run act with verbose output:
```bash
act -j tests-unit --verbose --env-file .env
```

### Clean Up

Remove act containers and images:
```bash
# Remove act containers
docker rm -f $(docker ps -aq --filter "label=com.docker.compose.project=act")

# Remove act images
docker rmi $(docker images -q --filter "label=com.docker.compose.project=act")
```

## Notes

- **Services**: Some jobs require external services (PostgreSQL, Redis) which may not be available locally
- **Performance**: Local testing may be slower than GitHub Actions
- **Dependencies**: All dependencies are installed in containers, so no local Python/Go setup required
- **Secrets**: Use `.env` file for secrets instead of GitHub secrets

## Best Practices

1. **Test incrementally**: Start with unit tests, then integration, then performance
2. **Use specific jobs**: Don't test all jobs unless necessary
3. **Check logs**: Use `--verbose` flag for detailed output
4. **Clean up**: Remove containers after testing to save disk space
