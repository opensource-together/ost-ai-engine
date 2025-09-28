# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2025-09-28

### Added
- ETL pipeline for collecting open source project data
- Go scrapers for GitHub and GitLab APIs
- PostgreSQL database with staging and marts schemas
- dbt transformations for data cleaning and modeling
- Dagster orchestration with web UI
- Docker Compose setup for local development
- Prisma schema and migrations for database management

### Fixed
- PostgreSQL port configuration consistency
- Table naming consistency between scrapers and dbt models
- Missing dbt configuration files

### Technical Details
- Real-time data processing with concurrent scrapers
- Automated data quality validation with dbt tests
- Pipeline monitoring and error handling via Dagster

## [0.1.0] - 2025-09-22

### Added
- Initial project structure
- Basic Docker setup
- Prisma schema foundation
- OSS kickoff baseline
