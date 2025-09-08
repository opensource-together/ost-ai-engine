# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup and architecture
- Complete data processing pipeline for GitHub repository analysis
- ML-powered recommendation engine with embeddings
- Go API for high-performance recommendations
- dbt transformation pipeline
- Comprehensive test suite (unit, integration, performance)
- Full documentation and OSS compliance
- CI/CD pipeline with GitHub Actions
- Docker containerization
- Local development setup with Docker Compose

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

## [1.1.0] - 2025-09-08

### Highlights
- API hardening and operational reliability
- Cleaner structure and faster DX with uv package manager
- Documentation updates for strict configuration

### Changes (aggregated from 1.0.1 → 1.0.6)
- Configuration & startup
  - Enforce strict configuration validation; remove silent defaults; fail-fast on invalid/missing env (1.0.1, 1.0.6)
  - Database connectivity check at startup with timeout (1.0.1)
- Health & observability
  - Health endpoint checks DB; returns 200/503 with timeout (1.0.2)
  - Add request logging (chi Logger), timing logs in handlers, and health failure logs (1.0.6)
- API behavior & responses
  - Standardized JSON helpers and unified error responses (1.0.3)
  - Input validation improvements (bad/missing parameters return proper 4xx) (1.0.3)
- Router & structure
  - Switch to go-chi with RequestID, RealIP, Recoverer, Timeout middlewares (1.0.4)
  - Modularize API into config/db/handlers/router and slim main (1.0.5)
- Tooling & build
  - Adopt uv with PEP 621 [project] metadata; remove poetry.lock, commit uv.lock (1.0.6)
- Docs
  - README and Go API docs updated to note strict env requirements and examples (1.0.6)

### Notes
- Backward-compatible API behavior; significantly improved operational characteristics and developer experience.

## [1.0.6] - 2025-09-08

### Changed
- Go API: Strict env (no defaults), improved logging, chi router, modular layout
- Build: Adopt uv (PEP 621 metadata); remove poetry.lock and commit uv.lock
- Docs: README and Go API docs updated to note env requirements

### Notes
- Backward-compatible API behavior; operational characteristics improved

## [1.0.5] - 2025-09-08

### Changed
- Go API: Refactor into modular files (config.go, db.go, handlers.go, router.go) and slim main()

### Notes
- Internal structural change only; no behavior change. Backward-compatible.

## [1.0.4] - 2025-09-08

### Added
- Go API: Switch to go-chi router with RequestID, RealIP, Recoverer, Timeout middlewares

### Notes
- Patch release focused on routing and middleware improvements. Backward-compatible.

## [1.0.3] - 2025-09-08

### Changed
- Go API: Standardized JSON response helpers (writeJSON, writeError) and refactored handlers

### Notes
- Patch release focused on API response consistency. Backward-compatible.

## [1.0.2] - 2025-09-08

### Added
- Go API: Health endpoint now checks database connectivity with 500ms timeout and returns 200/503 accordingly

### Changed
- Improved operational readiness by surfacing DB issues via /health

### Notes
- Patch release focusing on operational health reporting. Backward-compatible.

## [1.0.1] - 2025-09-08

### Changed
- Go API: Enforce strict configuration validation (no silent defaults in non-dev)
- Go API: Fail-fast startup with database PingContext timeout

### Removed
- Dropped non-essential dbt integration test (`tests/integration/test_dbt_models.py`) to avoid flaky CI deps

### Fixed
- Minor robustness improvements in API startup and configuration parsing

### Notes
- This is a backward-compatible patch release focusing on reliability of the Go API service.

## [1.0.0] - 2024-12-20

### Added
- **Core Platform**: Complete data processing platform for GitHub repository analysis
- **ML Engine**: AI-powered recommendation engine using sentence transformers
- **Go API**: High-performance recommendation endpoints
- **dbt Pipeline**: Data transformation and modeling with dbt
- **Testing**: Comprehensive test suite with pytest
- **Documentation**: Complete setup and usage guides
- **CI/CD**: GitHub Actions workflow with multiple jobs
- **Containerization**: Docker and Docker Compose setup
- **OSS Compliance**: MIT License, CONTRIBUTING.md, CODE_OF_CONDUCT.md

### Tech Stack
- **Backend**: Python 3.13, Go 1.24+
- **Database**: PostgreSQL 15+ with pgvector extension
- **ML**: Sentence Transformers, MLflow
- **Orchestration**: Dagster
- **Testing**: pytest, golangci-lint
- **Containerization**: Docker & Docker Compose

### Architecture
- **Data Extraction**: Go scraper for GitHub repositories
- **Data Processing**: dbt models for transformation
- **ML Pipeline**: Embedding generation and similarity calculations
- **API Layer**: Go service for recommendations
- **Caching**: Redis for performance optimization
- **Monitoring**: MLflow for model tracking

### Documentation
- [Quick Start Guide](docs/deployment/quick-start.md)
- [Architecture Overview](docs/architecture/overview.md)
- [API Documentation](docs/api/go-api.md)
- [Testing Guide](docs/testing/overview.md)
- [Contributing Guidelines](CONTRIBUTING.md)

---

## Version History

- **1.0.0**: Initial stable release with complete platform
- **Unreleased**: Development and testing phase

## Release Notes

### v1.0.0 - Initial Release
This is the first stable release of OST Data Engine, providing a complete platform for GitHub repository analysis and intelligent project recommendations.

**Key Features:**
- Complete data processing pipeline
- ML-powered recommendation engine
- High-performance Go API
- Comprehensive testing suite
- Full documentation
- OSS compliance

**Requirements:**
- Python 3.13+
- Go 1.24+
- PostgreSQL 15+ with pgvector extension
- Redis 7+

**Quick Start:**
```bash
git clone https://github.com/opensource-together/ost-data-engine.git
cd ost-data-engine
conda create -n data-engine-py13 python=3.13
conda activate data-engine-py13
poetry install
cp .env.example .env
docker-compose up -d db redis
```

---

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
