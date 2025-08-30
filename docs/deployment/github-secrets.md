# GitHub Secrets Configuration

## Overview

The CI/CD pipeline uses GitHub Secrets to securely store sensitive configuration values. This ensures that no sensitive information is exposed in the codebase.

## Required Secrets

### Database Configuration

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `POSTGRES_USER` | PostgreSQL username | `user` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `secure_password_123` |
| `POSTGRES_DB` | PostgreSQL database name | `OST_PROD` |
| `DATABASE_URL` | Complete database connection string | `postgresql://user:password@localhost:5434/OST_PROD` |

### Model Configuration

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `MODEL_NAME` | Hugging Face model name | `sentence-transformers/all-MiniLM-L6-v2` |
| `MODEL_DIMENSIONS` | Model embedding dimensions | `384` |

### API Configuration

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `GO_API_PORT` | Go API server port | `8080` |

### Cache Configuration

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `REDIS_CACHE_URL` | Redis connection URL | `redis://localhost:6379/0` |

### Recommendation Configuration

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `RECOMMENDATION_TOP_N` | Number of recommendations | `5` |
| `RECOMMENDATION_MIN_SIMILARITY` | Minimum similarity threshold | `0.1` |

### API Keys

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `GITHUB_ACCESS_TOKEN` | GitHub API access token | `github_pat_...` |

### Environment-Specific

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `ENVIRONMENT` | Deployment environment | `staging` or `production` |
| `SECRET_KEY` | Application secret key | `your_secret_key_here` |

## Local Testing with Act

### Prerequisites

- **Act**: Install Act for local GitHub Actions testing
- **Docker**: Ensure Docker Desktop is running
- **Secrets File**: Create `.secrets` file with test values

### Installation

```bash
# Install Act
brew install act

# Verify installation
act --version
```

### Configuration

Create a `.secrets` file with test values (never commit this file):

```bash
# Database Configuration
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=OST_PROD
DATABASE_URL=postgresql://user:password@localhost:5436/OST_PROD

# API Keys
GITHUB_ACCESS_TOKEN=your_test_token

# Model Configuration
MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
MODEL_DIMENSIONS=384

# API Configuration
GO_API_PORT=8082

# Cache Configuration
REDIS_CACHE_URL=redis://localhost:6381/0

# Service Ports (for CI testing)
POSTGRES_PORT=5436
REDIS_PORT=6381

# Recommendation Configuration
RECOMMENDATION_TOP_N=5
RECOMMENDATION_MIN_SIMILARITY=0.1
```

### Running Tests Locally

#### macOS Solution

On macOS, use this specific command to avoid Docker socket issues:

```bash
act -j test --secret-file .secrets --pull=false --container-daemon-socket /var/run/docker.sock
```

#### Alternative Commands

```bash
# List available jobs
act --list

# Run specific job
act -j test --secret-file .secrets

# Run with specific event
act push --secret-file .secrets

# Run without pulling images
act -j test --secret-file .secrets --pull=false
```

### Troubleshooting Act

#### Common Issues

1. **Docker Socket Error on macOS**
   ```bash
   # Use the specific socket path
   act -j test --secret-file .secrets --pull=false --container-daemon-socket /var/run/docker.sock
   ```

2. **Port Conflicts**
   ```bash
   # Use different ports in .secrets file
   POSTGRES_PORT=5436
   REDIS_PORT=6381
   GO_API_PORT=8082
   ```

3. **Image Pull Issues**
   ```bash
   # Skip image pulling
   act -j test --secret-file .secrets --pull=false
   ```

#### Debug Mode

```bash
# Run with verbose output
act -j test --secret-file .secrets --verbose

# Run with debug logging
act -j test --secret-file .secrets --debug
```

### Integration with Development Workflow

```bash
# 1. Make changes to CI configuration
nano .github/workflows/ci.yml

# 2. Test locally with Act
act -j test --secret-file .secrets --pull=false --container-daemon-socket /var/run/docker.sock

# 3. If tests pass, commit and push
git add .
git commit -m "test: update CI configuration"
git push origin main
```

## How to Configure Secrets

### 1. Go to Repository Settings

1. Navigate to your GitHub repository
2. Click on **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**

### 2. Add Repository Secrets

1. Click **New repository secret**
2. Enter the secret name (e.g., `POSTGRES_USER`)
3. Enter the secret value
4. Click **Add secret**

### 3. Environment-Specific Secrets

For different environments, you can create environment-specific secrets:

1. Go to **Settings** → **Environments**
2. Create environments (e.g., `staging`, `production`)
3. Add environment-specific secrets

## CI/CD Usage

### In Workflow Files

```yaml
env:
  POSTGRES_USER: ${{ secrets.POSTGRES_USER }}
  POSTGRES_PASSWORD: ${{ secrets.POSTGRES_PASSWORD }}
  DATABASE_URL: ${{ secrets.DATABASE_URL }}

jobs:
  test:
    steps:
      - name: Run tests
        env:
          GITHUB_ACCESS_TOKEN: ${{ secrets.GITHUB_ACCESS_TOKEN }}
        run: poetry run python -m pytest
```

### Environment-Specific Secrets

```yaml
jobs:
  deploy:
    environment: production
    steps:
      - name: Deploy to production
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

## Security Best Practices

### 1. Never Commit Secrets

- Never add secrets to `.env` files that are committed
- Never hardcode secrets in workflow files
- Always use GitHub Secrets for sensitive data

### 2. Rotate Secrets Regularly

- Rotate database passwords monthly
- Rotate API keys quarterly
- Use different secrets for different environments

### 3. Principle of Least Privilege

- Use minimal required permissions for API tokens
- Use dedicated database users for CI/CD
- Limit access to production secrets

### 4. Audit Access

- Regularly review who has access to secrets
- Monitor secret usage in GitHub audit logs
- Remove access for inactive users

## Local Development

### Using .env for Local Development

Create a `.env` file for local development (never commit this file):

```env
# Database
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=OST_PROD
DATABASE_URL=postgresql://user:password@localhost:5434/OST_PROD

# API Keys
GITHUB_ACCESS_TOKEN=your_github_token

# Application
SECRET_KEY=your_secret_key
```

### .env.example

Create a `.env.example` file with placeholder values:

```env
# Database
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=your_db_name
DATABASE_URL=postgresql://user:password@localhost:5434/dbname

# API Keys
GITHUB_ACCESS_TOKEN=your_github_token_here

# Application
SECRET_KEY=your_secret_key_here
```

## Troubleshooting

### Common Issues

1. **Secret Not Found**
   ```
   Error: Secret 'POSTGRES_USER' not found
   ```
   - Check if the secret name is correct
   - Ensure the secret is added to the repository

2. **Permission Denied**
   ```
   Error: Permission denied for secret
   ```
   - Check if the workflow has access to the secret
   - Verify environment restrictions

3. **Environment Not Found**
   ```
   Error: Environment 'production' not found
   ```
   - Create the environment in repository settings
   - Add required protection rules

### Debugging

1. **Check Secret Names**
   - Verify secret names match exactly (case-sensitive)
   - Check for typos in workflow files

2. **Test Locally**
   - Use `.env` file for local testing
   - Verify environment variables are loaded correctly

3. **Check Workflow Logs**
   - Review GitHub Actions logs for detailed error messages
   - Check if secrets are being passed correctly

## Migration Guide

### From Hardcoded Values

If you have hardcoded values in your workflow files:

1. **Identify sensitive values**
   ```yaml
   # Before
   env:
     DATABASE_URL: postgresql://user:password@localhost:5434/OST_PROD
   ```

2. **Add to GitHub Secrets**
   - Add `DATABASE_URL` as a repository secret

3. **Update workflow**
   ```yaml
   # After
   env:
     DATABASE_URL: ${{ secrets.DATABASE_URL }}
   ```

4. **Test the changes**
   - Run the workflow to ensure it works
   - Verify no sensitive data is exposed in logs

