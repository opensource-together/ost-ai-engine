# CI/CD & Docker

## GitHub Actions

### Workflow triggers

- `pull_request: branches: [X]` filters on the **base** branch — only triggers when the PR targets branch X
- `issue_comment`, `issues`, `pull_request_review` events only trigger from workflows on the **default branch** (`staging`)
- New workflow files in a PR won't trigger on the target branch until they're merged there

### Permissions

- Claude Code Action (`claude.yml`) needs `write` on `contents`, `pull-requests`, and `issues` to post comments
- Claude Code Review (`claude-code-review.yml`) only needs `read` (it posts via the OAuth token, not GITHUB_TOKEN)
- Sync workflows need a repo-scoped PAT (`OST_LINKER_SYNC_TOKEN`) for cross-repo operations (ost-docs + ost-backend)

### Branch CI strategy

| Branch | Workflows that run on PRs |
|--------|---------------------------|
| `develop` | `claude-code-review` only |
| `staging` / `main` | `publish-develop` (quality checks) + `sync-docs` + `sync-prisma` + `claude-code-review` |

### Secrets

| Secret | Used by |
|--------|---------|
| `CLAUDE_CODE_OAUTH_TOKEN` | `claude.yml`, `claude-code-review.yml` |
| `OST_RELEASE_PAT` | `publish-develop.yml`, `publish-prod.yml` (GHCR push) |
| `OST_LINKER_SYNC_TOKEN` | `sync-docs-submodule.yml`, `sync-prisma-backend.yml`, `quality-checks.yml` (cross-repo sync) |

## Docker

### Build stages

1. **Go builder** (`golang:1.24-alpine`) — compiles scraper + fetcher
2. **Python builder** (`python:3.11-slim`) — `uv export` to `requirements.txt`
3. **Runtime** (`python:3.11-slim`) — pip install, copy Go binaries, run Dagster

### Compose services

| Service | Image | Ports |
|---------|-------|-------|
| `webserver` | Built from Dockerfile | 3000 (Dagster UI) |
| `daemon` | Built from Dockerfile | — (depends on webserver) |
| `db` (dev override only) | `ankane/pgvector:v0.4.1` | 5433→5432 |

`docker-compose.override.yml` adds local dev overrides (db service, volume mounts, env files).
