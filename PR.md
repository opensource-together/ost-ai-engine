PR 1 – Repository hygiene and baseline reset

Summary
- Reset CHANGELOG; remove non-essential OSS docs during refactor; no runtime changes.

Changes
- Reset `CHANGELOG.md` content to start fresh for the refactor series.
- Remove `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md` (to be reintroduced post-refactor).
- No code behavior changes.

Testing
- CI should pass unchanged. No functional paths altered.

Notes
- Follow-up PRs will introduce feature changes and docs.
- Reference: Repo context `dev` branch `opensource-together/ost-ai-engine` (`https://github.com/opensource-together/ost-ai-engine/tree/dev`).

---

PR 2 – License switch to Non-Commercial

Summary
- Switch license to a non-commercial OSS license to discourage commercial reuse.

Changes
- Replace `LICENSE` with Polyform Noncommercial 1.0.0 (proposed). Rationale: clear NC terms, simple compliance.

Testing
- N/A.

Notes
- Applied only after project owners confirm the choice.

---

PR 3 – Orchestration plan: Redis + Dagster + Postgres (no temp tables)

Summary
- Define architecture to avoid temporary tables; clarify contracts between assets, cache, and storage.

Changes
- Add architecture notes in docs: final tables only for embeddings/similarities; Redis for intermediate caching; MLflow for artifacts.
- No code changes yet; purely planning/ADR style doc.
- Define MLflow artifact storage location as `models/` in repo root (all persisted models/metrics live under `models/`).

Testing
- N/A; documentation only.

Notes
- Dagster assets and dependency edges remain as-is for now. See Dagster guides for asset-based modeling and scheduling: `https://docs.dagster.io/etl-pipeline-tutorial`, `https://docs.dagster.io/etl-pipeline-tutorial/transform-data`, `https://docs.dagster.io/tutorial/connecting-to-external-services`.
- MLflow tracking will persist run artifacts under `models/` to centralize persisted outputs in-repo.

---

PR 4 – Go Trending Scraper asset with optional schedule flag

Summary
- Implement Go-based GitHub trending scraper; invoked by Dagster asset (`github_assets.py`). Scheduling flag present but disabled by default.

Changes
- Add Go scraper binary usage in asset with args: `--query`, `--max-repos`, `--db-url`, `--upsert`, `--schedule-disabled`.
- Write directly to final tables; no temp tables.

Testing
- Materialize `github_scraping` locally; verify row counts; logs show upsert summary.

Notes
- Keep token/env usage outside of repo (env only). Future cron/Go routine can flip the scheduling flag.
- Reference: Repo `dev` branch and existing `github_assets.py` integration.

---

PR 5 – Global recommendations materialization job + MLflow persistence

Summary
- Compute global (user-agnostic) trending recommendations and persist for serving; store artifacts in MLflow.

Changes
- New Dagster asset: computes top-N projects based on trending signals; stores in `GLOBAL_PROJECT_RECOMMENDATION`.
- Persist summary artifacts (top-N lists, metrics) to MLflow with artifacts stored under `models/`.

Testing
- Materialize asset; validate table counts and MLflow run created.

Notes
- Preserves current model stack; focuses on aggregation and serving format.
- Ensure MLflow artifact URI is configured to `models/` (local runs) so CI and dev parity is maintained.

---

PR 6 – Per-user pipeline refactor to final tables (preserve cosine similarity)

Summary
- Update per-user similarity pipeline to read/write only final tables; cosine similarity preserved (hybrid vectors).

Changes
- Adjust assets to remove temp table usage; ensure idempotent updates to `embed_USERS`, `embed_PROJECTS`, `USER_PROJECT_SIMILARITY`.
- Maintain MLflow persistence of embeddings and similarity metrics.

Testing
- Materialize full pipeline; validate average similarity stats, counts; ensure existing tests keep passing.

Notes
- Consistent with Dagster asset best practices (assets as durable state, not temp staging) `https://docs.dagster.io/etl-pipeline-tutorial`.

---

PR 7 – API docs: two endpoints + Swagger/OpenAPI

Summary
- Document and expose:
  - GET `/recommendations/global`
  - GET `/recommendations?user_id={id}`
- Add OpenAPI spec and lightweight Swagger UI hosting.

Changes
- Add OpenAPI YAML/JSON under `docs/` and link from README/docs.
- Optional: minimal Go handler wiring if needed (no breaking changes).

Testing
- Validate OpenAPI schema; render via Swagger UI; basic curl examples.

Notes
- Keep strict env config for Go service. Cite docs/Go API page.

---

PR 8 – Docker and .actrc developer experience

Summary
- Simplify local deployment; document private .env overrides for internal DB; update `.actrc` guidance.

Changes
- Compose services decoupled per best practices; healthchecks; environment via `.env` (private overrides not committed).
- Document internal DB override example (do not commit secrets); maintain public placeholders.

Testing
- Run `docker-compose up` for db/redis/api; verify healthchecks; run pipeline materializations.

Notes
- Follow Docker best practices for decoupled services and sorted RUN lines: `https://docs.docker.com/build/building/best-practices/`, `https://docs.docker.com/develop/security-best-practices/`.
- Redis documentation reference: `https://redis.io/docs/`.
- PostgreSQL reference: `https://www.postgresql.org/docs/current/release-17-6.html`.


