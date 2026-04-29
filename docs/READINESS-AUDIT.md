# OST Linker — readiness audit

**Date:** 2026-04-29  
**Follow-up (same day):** `API_RATE_LIMIT` wired to SlowAPI (`rate_limit.py`); optional `API_ENABLE_OPENAPI` for `/docs` and OpenAPI JSON; `docker-compose.yml` + `.env.example` document strict token and OpenAPI; README license paragraph clarifies CC BY-NC vs OSI.
**Scope:** Full repository (`ost-linker`): OSS posture, contribution flow, onboarding, dev/prod split, recommendations (dbt + API), CI/tests, code hygiene, API security, system design.  
**Local truth gate:** `make ci-check` passed (ruff, format, mypy, unit + api + Dagster startup smoke).

---

## Executive summary

| Area | Verdict | Notes |
|------|---------|--------|
| **Contributor experience** | Strong | `CONTRIBUTING.md` + `AGENTS.md` split is clear; PR template and branch rules are explicit. |
| **“Open source” licensing** | Needs product clarity | Code is under **CC BY-NC 4.0** (`LICENSE`, README badge). That is **not** an OSI-approved “open source” license; fine for source-available / community builds, misleading if marketed as OSS in the OSI sense. |
| **Security** | Solid baseline; gaps actionable | Timing-safe token compare; optional auth has an **open mode** when token unset; `API_RATE_LIMIT` env drift vs hardcoded SlowAPI limits; OpenAPI/docs exposure in default FastAPI. |
| **Recommendations** | Coherent pipeline | `match_*` marts + dbt tests cover bounds, duplicates, bookmarks, ignored projects; freshness omits feedback tables; CI only `dbt parse`, not `dbt build`. |
| **Dev / Prod** | Well separated | `docker-compose.override.yml` documents prod path (`docker compose -f docker-compose.yml`); dev adds `db`, bind-mounts, local `dagster.yaml`. |
| **CI / tests** | Broad CI; local parity partial | GitHub runs Python, dbt parse, Go, Docker build, Prisma validate, pip-audit, gitleaks, docs submodule; **`make ci-check` is Python-only** (same gap as documented in parallel audit). |
| **Legacy / verbose comments** | Low debt | No `TODO`/`FIXME` in `src/`; minor redundant comments and Prisma template header. |

---

## Methodology / workers

Parallel **Explore** tasks (scoped read-only) + file review + **`make ci-check`**:

| Task | Worker | Model |
|------|--------|--------|
| OSS & onboarding | Task (Explore) | composer-2-fast |
| CI & tests | Task (Explore) | composer-2-fast |
| API & security | Task (Explore) | claude-4.6-sonnet-medium-thinking |
| dbt recommendations | Task (Explore) | composer-2-fast |
| Dev / prod environments | Task (Explore) | composer-2-fast |
| Code hygiene | Task (Explore) | composer-2-fast |
| Synthesis | Composer | — |

---

## OSS and licensing

- **LICENSE / README:** [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). **Recommendation:** State in README/CONTRIBUTING whether the intent is **source-available with NC restriction** vs migrating to **OSI-approved license** for stricter “open source” claims.
- **`CONTRIBUTING.md`:** Prerequisites table, fork/clone, `AGENTS.md` deep link, conventional commits, PR target `staging` — **light onboarding** without duplicating all of `AGENTS.md`.
- **`.github`:** Issue templates (`bug_report`, `feature_request`), PR checklist aligned with CI, **`CODEOWNERS`** → `@spideystreet` (bus factor risk — document co-maintainers when added).
- **`SECURITY.md`:** Exists; private disclosure via email; supports production reporting expectations.

---

## Onboarding burden

- **Heavy parts (acceptable):** Go compile, Docker, Node/Prisma, optional full pipeline — all documented; seed explicitly does **not** fill projects/embeddings/recos (correct expectation setting).
- **Duplication:** README → CONTRIBUTING → AGENTS is layered, not contradictory. Optional improvement: single “5-minute smoke” vs “full reco path” TOC in README.

---

## Dev vs production environments

| Concern | Development (default compose) | Staging/production-style |
|--------|-------------------------------|---------------------------|
| Compose files | Base + **`docker-compose.override.yml`** auto-loaded | **`docker compose -f docker-compose.yml`** skips override (`override.yml` header) |
| Postgres | **`db` service**, host port `POSTGRES_PORT` (default **5433**) | Use external DB / operator config |
| Dagster storage | **`dagster.yaml`** bind-mounted SQLite config | **`dagster.prod.yaml`** / Postgres-oriented layout in prod images |
| `DBT_TARGET` | **`docker`** in container shared env (`docker-compose.yml` `common-env`) | Host tools often `local` per `profiles.yml` + `.env` |
| API secrets | Compose passes `OST_LINKER_SERVICE_TOKEN`; may be empty | Operators must set token + **`OST_LINKER_REQUIRE_SERVICE_TOKEN=true`** for strict deployments |

---

## Recommendations pipeline (dbt + API)

**Strengths:**

- Personalized: preference overlap → embeddings similarity → hybrid score → **`reco_top_n`** cap; exclusions for bookmarks and “shown but ignored” events.
- **Data tests:** max rows per user, uniqueness, score bounds, bookmark/ignore invariants (`dbt/tests/`).
- **Source freshness:** GitHub/ml/public Project tables have warn/error horizons in `sources.yml`.

**Gaps:**

1. **CI:** `dbt parse` only — no Postgres job for `dbt build` / data tests on critical models.
2. **Vars:** reco weights / `ignored_*` defaults live in SQL `var(..., default)` — centralize in `dbt_project.yml` or Dagster for parity across envs.
3. **Feedback data:** Limited freshness monitoring for **`recommendation_event`** / **`project_bookmark`** compared to embeddings.
4. **Product semantics:** **`DISMISSED`** in events may need suppression logic if product demands it (staging lists values; mart logic may omit).
5. **API vs mart ordering:** Trending endpoint re-sorts global recos (`stars`) — documented mismatch risk between materialized order and HTTP response order.
6. **Cold users:** Personalized mart can be empty; ensure product/API fallback to global trending is explicit (document + test).

---

## API and security

**Route inventory (authenticated except `/health`):** references (`/categories`, `/domains`, `/techstacks`), projects search/detail/similarity, semantic search, recommendations trending — all behind **`require_service_token`** at router level except health.

| ID | Severity | Finding | Mitigation |
|----|----------|---------|------------|
| F1 | High | **Unset token ⇒ open “protected” API** (`auth.py`) | Production: set token + **`OST_LINKER_REQUIRE_SERVICE_TOKEN=true`** |
| F2 | Medium | Compose does not set **`OST_LINKER_REQUIRE_SERVICE_TOKEN`** | Add to prod templates |
| F3 | Medium | **`API_RATE_LIMIT`** documented but routes use **`60/minute`** literals | Wire config into SlowAPI or document |
| F4 | Medium | **`/docs` / `/openapi.json`** exposed by default | Disable or restrict in production |
| F5–F7 | Low | Health DB probe; proxy-unaware rate limit client key; semantic search CPU on large `q` | Network controls; max query length |

**Hygiene:** `secrets.compare_digest` for token check; parameterized SQL in audited routes; **gitleaks** + **pip-audit** in CI per `quality-checks.yml`.

---

## CI and tests

**GitHub Actions (`quality-checks.yml`):** Python quality (ruff, mypy, unit with coverage ≥50%, api, Dagster startup), **`dbt deps` + `parse`**, Go vet/build/test (scraper/fetcher/trending), Docker image build (no push in check job), **`prisma validate`**, **`pip-audit`**, **`gitleaks`** (`--no-git` working-tree), conditional docs submodule check (fork skips).

**Gaps:**

- **`make ci-check`:** Python parity only — label as such or add optional targets (`dbt-parse`, `go-check`) for maintainer prep.
- **dbt:** No `sqlfluff` in CI despite dev dependency; no `dbt build` against real DB.
- **performance** marker unused in workflows.
- **Pre-commit:** ruff + mypy only.

**Local verification (2026-04-29):** `make ci-check` — **passed** (128 unit, 50 api, 1 integration).

---

## Code hygiene

- **Markers:** No `TODO`/`FIXME`/`HACK` in Python `src/` or tests (Explore scan).
- **Noise:** Prisma boilerplate header; `definitions.py` import layout; occasional “comment repeats next line” in scraper assets — **P2** trim when touching files.
- **Coverage:** Overall ~60% with 50% floor; scraping/embedding paths under-covered (expected cost).

---

## System design lens (concise)

- **Interfaces:** FastAPI JSON, Prisma-managed schema, dbt **`match_*`** tables — stable for MCP if versioned externally.
- **Data flow:** Ingest → enrich → embeddings → dbt → API read path; writes isolated to pipeline/runtime, API read-mostly.
- **Failure modes:** Open auth mode fails “closed” only when strict env set; stale data surfaced partly via dbt freshness, not uniformly on events.
- **Observability:** Dagster schedules, pytest markers, CI security jobs — adequate for OSS; prod needs log/metric policy outside this audit.

---

## Prioritized backlog

### P0 (before claiming “secured production API”)

1. Enforce **`OST_LINKER_SERVICE_TOKEN`** in real deployments (**`OST_LINKER_REQUIRE_SERVICE_TOKEN=true`**).
2. Align **`API_RATE_LIMIT`** with SlowAPI behavior or fix docs.

### P1

1. **`docker-compose` / Helm / docs:** Add strict token requirement for prod-like stacks.
2. **dbt:** Centralize reco **`vars`**; add Postgres CI job OR document why `parse` suffices.
3. **Product/docs:** Clarify **CC BY-NC** vs “open source”; link **`SECURITY.md`** from README optionally.
4. **OpenAPI:** Disable or fence docs in prod.

### P2

1. **`make ci-check`:** Rename or extend for optional full parity.
2. **Fork PR docs** in workflow or `AGENTS.md` (which jobs need secrets).
3. **DISMISSED** handling, freshness on event/bookmark sources, **`sqlfluff`** in CI optional.
4. Comment cleanup in **`raw_github__extract_projects.py`** / Prisma header when convenient.

---

## PR readiness

- **Audit-only PR:** Add/commit **`docs/READINESS-AUDIT.md`** (this file) → ready for review; no CI change required for merge.
- **Remediation PRs:** Prefer one theme per PR (security config vs dbt vars vs CI), keep **`make ci-check`** green and match PR template checklist; add **`dbt parse`**/`dbt test` steps when touching SQL.

---

## Appendix: Related paths

| Topic | Paths |
|--------|--------|
| API entry | `src/services/api/main.py`, `routes/` |
| Auth | `src/services/api/auth.py` |
| Recommendations API | `src/services/api/routes/recommendations.py` |
| dbt marts | `dbt/models/marts/match_user_recommendation.sql`, `match_global_recommendation.sql` |
| Compose | `docker-compose.yml`, `docker-compose.override.yml` |
| CI | `.github/workflows/quality-checks.yml`, `publish-develop.yml`, `Makefile` |
