# ost-linker — quality & architecture backlog (phase 1)

> **Historical:** snapshot from 2026-05-01, before the structural refactor (`src/api/`, `ci.yml`, test layout). Paths and CI commands below may be outdated.

**Audit execution date:** 2026-05-01  
**Design spec (workspace meta):** `docs/superpowers/specs/2026-05-01-ost-linker-quality-architecture-audit-design.md`

## Evidence runs

### `make ci-check`

- _Command (from repo root `ost-linker/`):_ `cd /Users/spidey/Developer/git/Ost/ost-linker && make ci-check` (delegates per `Makefile` to `lint` → `uv run ruff format --check src/`, then `make typecheck`, then `uv run pytest -m unit --cov-fail-under=50`, `uv run pytest -m api --no-cov`, `uv run pytest -m integration -k test_dagster_startup --no-cov`)

- _Exit code:_ **0**

- _Result excerpt:_

```
uv run ruff check src/
All checks passed!
uv run ruff format --check src/
46 files already formatted
...
uv run mypy src/
Success: no issues found in 46 source files
...
uv run pytest -m unit --cov-fail-under=50
... 132 passed, 51 deselected ...
Required test coverage of 50% reached. Total coverage: 60.17%
...
uv run pytest -m api --no-cov
====================== 50 passed, 133 deselected in 4.29s ======================
uv run pytest -m integration -k test_dagster_startup --no-cov
====================== 1 passed, 182 deselected in 12.99s =======================
```

*(Full transcript on audit machine: `/tmp/linker-ci-check.log`.)*

### Go unit tests (`fetcher`)

- _Command:_ `cd /Users/spidey/Developer/git/Ost/ost-linker/src/services/go/fetcher && go test ./...`

- _Excerpt:_ `ok  ost-fetcher  0.510s` — **exit 0**

### Go unit tests (`scraper`)

- _Command:_ `cd /Users/spidey/Developer/git/Ost/ost-linker/src/services/go/scraper && go test ./...`

- _Excerpt:_ `ok  github.com/opensource-together/ost-ai-engine/github-scraper  0.268s` — **exit 0**

### Docker Compose + API `/health`

- _Compose context:_ stack `ost-linker` was already running on audit host (`docker compose ps` from repo root).

- _Probe:_ `curl -sS -w "\nHTTP_CODE:%{http_code}\n" "http://127.0.0.1:8010/health"`  
  *(Port **8010** matches `0.0.0.0:8010->8000/tcp` mapping for `ost-linker-api` — see `docker compose ps`.)*

- _Excerpt / BLOCKED:_

```
{"status":"ok"}
HTTP_CODE:200
```

---

## Architecture inventory & layer map

The `ost-linker` stack is **multi-process**: **Dagster** (`webserver` + `daemon`) runs the batch/ML pipeline; a **FastAPI** `api` service exposes the read-only HTTP surface consumed by **ost-mcp**; **Postgres + pgvector** is added in **`docker-compose.override.yml`** as `db` (dev) with `POSTGRES_PORT` defaulting to **5433** on the host unless overridden (this audit host used **5435**). Published ports follow env overrides: **`DAGSTER_HOST_PORT`** (here **3033→3000**), **`LINKER_API_HOST_PORT`** (**8010→8000**). `workspace.yaml` loads **`src.linker.definitions:defs`** with Docker-centric `working_directory: /app`, matching the image layout where `./scripts/init.sh` waits for Postgres, runs **dbt** parse/build for Dagster manifest materialization, and starts Dagster or **uvicorn**. The **api** container intentionally carries a **minimal env** (database URL, rate limit, service-token flags, OpenAPI toggle) and skips dbt init per `scripts/init.sh`. **Prisma** (`make db-init`, `prisma/schema.prisma`) and **dbt** (`dbt/`, `Settings.dbt_project_dir` in `src/linker/settings.py`) are primarily maintained on the **host** for schema push and analytics builds, while compose shares `dbt_target` with Dagster for manifest reuse. **Go** scraper/fetcher binaries are compiled to fixed paths (`GO_*_PATH` in compose `x-common-env`, e.g. `/usr/local/bin/ost-scraper`) for Dagster assets to shell out.

---

## Vertical trace — MCP-oriented read path

- **App bootstrap:** `src/services/api/main.py` builds `FastAPI` with **`lifespan`**: validates service-token config when `OST_LINKER_REQUIRE_SERVICE_TOKEN` is true, then **`init_db` + `init_semantic`** before serving.

- **Public health:** `GET /health` is mounted from `routes/health.py` **without** `Depends(require_service_token)`; it runs `SELECT 1` via SQLAlchemy session (`Depends(get_db)`), so it reflects **DB** reachability, not just process liveness.

- **Protected read APIs:** `references`, `projects`, and `recommendations` routers are included with **`dependencies=[Depends(require_service_token)]`**. `auth.require_service_token` compares `X-Service-Token` with `OST_LINKER_SERVICE_TOKEN` using `secrets.compare_digest`, but **returns early (allows)** when the expected token env var is **unset**—so misconfiguration can leave business routes open whenever strict mode is off.

- **Docs / OpenAPI:** `_openapi_urls()` disables `/openapi.json`, `/docs`, `/redoc` when `API_ENABLE_OPENAPI` is false at import time (container start).

- **Rate limits:** `slowapi` limiter is attached to `app.state` with a JSON 429 handler on `RateLimitExceeded` (per-route decorators; no global SlowAPI middleware).

---

## Vertical trace — ingestion / warehouse

- **Dagster registry:** `src/linker/definitions.py` composes **scraper** assets via `load_assets_from_modules` over modules such as `raw_github__extract_projects`, `raw_github__extract_trending`, and `core_github__fetch_*`, then registers **`@dbt_assets`** `dbt_project_assets` running `dbt build --indirect-selection cautious` through `DbtCliResource`, plus Python assets **`core_match__classify_projects`**, **`core_public__sync_projects`**, **`core_ml__embed_projects`**, **`core_ml__embed_users`**.

- **Operational jobs/schedules:** `build_jobs()` exposes `cleanup_dagster_history_job`, `project_enrichment_job`, `run_all_job`, `user_recommendation_job`; `build_schedules()` wires enrichment and recommendation schedules (plus cleanup schedule). **Sensors list is empty** today.

- **Warehouse contract:** dbt sources in `dbt/models/sources.yml` declare **freshness** and **meta.dagster.asset_key** links for `github` schema tables (e.g. `raw_github_project`) into Dagster groups—this is the documented bridge from raw ingestion tables to dbt/Dagster observability.

- **Resources:** `build_resources()` binds `DATABASE_URL`, GitHub token, Go binary paths, LLM and embedding resources, dbt CLI, and Postgres pandas IO managers—so asset failures often chain from **env completeness** and **Go binary presence** more than from Python import errors.

---

## Vertical trace — configuration glue

- **Split deployment surface:** `docker-compose.yml` **`api`** service lists only DB + API tuning env vars, while **`x-common-env`** for Dagster services also carries `GITHUB_ACCESS_TOKEN`, `MISTRAL_API_KEY`, `GO_*_PATH`, `DBT_TARGET`, model paths, etc. `docker-compose.override.yml` rewrites `DATABASE_URL` to `postgresql://…@db:5432/…` for dev and bind-mounts `src/`, `dbt/`, `scripts/` into Dagster containers (api mounts **`src` only**).

- **Role switch:** `DAGSTER_ROLE` is set to **`daemon`** for the daemon, **`api`** for FastAPI; `scripts/init.sh` branches: daemon may `dbt parse` if manifest missing; **api skips dbt entirely**.

- **Host vs container dbt target:** Compose sets `DBT_TARGET: docker` in common env; local dbt guidance in `AGENTS.md` stresses loading `.env` and choosing `local` vs `docker` profiles—auditors should treat **profile/target mismatch** as a recurring footgun when reproducing pipeline issues.

- **Dagster instance config:** Dev override bind-mounts `./dagster.yaml` into `/app/dagster_home/dagster.yaml` (SQLite storage paths via env); production is expected to diverge (see comments in override file).

---

## Pillar review notes

### pipeline-data

- **Source freshness:** `dbt/models/sources.yml` defines **warn/error windows** across `github`, `match`, `ml`, and `public.Project` sources—healthy pattern; running `dbt source freshness` was **not executed** in this pass (would need credentialed DB + time); treat as optional follow-up when DB mirrors prod-like volume.

- **Asset test coverage imbalance:** `make ci-check` unit coverage report shows **low line coverage** on several scraper and sync assets (`raw_github__extract_*`, `core_public__sync_projects`, README/topic/language fetch assets). That signals **pipeline regressions may slip** until integration runs or fuller unit suites exist.

- **embed_users vs embed_projects:** `core_ml__embed_users.py` registers far fewer exercised lines under unit runs than `core_ml__embed_projects.py` — user embedding/reco path may be under-tested compared to projects.

### ops-security

- **Service token semantics:** With `OST_LINKER_REQUIRE_SERVICE_TOKEN=false` (compose default), **and** unset empty shared token behavior in `require_service_token`, business routes rely on network isolation—acceptable for MCP server-to-server if perimeter holds, but **easy to misunderstand** across environments.

- **Postgres exposure (dev override):** `db` binds `${POSTGRES_PORT:-5433}:5432`; comment warns LAN exposure — ensure **staging/prod** compose files never copy this verbatim without controls.

- **OpenAPI suppression:** Controlled by **`API_ENABLE_OPENAPI`** — confirm operators set **`false`** in environments that must not advertise schemas publicly.

### maintainability

- **Entrypoints verified (Makefile vs CI vs docs):**

  - `Makefile` **`ci-check`** runs: `uv run ruff check src/`; **`ci-check`** also invokes `uv run ruff format --check src/`; **`make typecheck`** → **`uv run mypy src/`**; **`pytest -m unit --cov-fail-under=50`**, **`pytest -m api --no-cov`**, **`pytest -m integration -k test_dagster_startup --no-cov`**.

  - Pytest **`markers`** in `pyproject.toml`: `unit`, `integration`, `performance`, `api` (strict-markers enabled). Only **one** integration test module is marked (`tests/integration/test_dagster_startup.py`), so **`ci-check` ≅ full integration suite** today.

  - `.github/workflows/quality-checks.yml` uses **`dorny/paths-filter`** to **scope PR jobs** versus **always running on push**; maintainers invoking only `make ci-check` locally should remember **path-filter semantics differ** from a full staging push pipeline.

- **Dagster local vs compose:** Compose commands reference **`workspace.yaml`** with **`working_directory: /app`** (valid in-container). **`Makefile`** `dev` runs `uv run dagster dev -h 0.0.0.0 -p 3000` **without** `-w workspace.yaml`; developers may unknowingly diverge from container definitions—document explicitly or unify workspace selection.

---

## Consolidated findings (paste as GitHub issues)

Each finding follows the design-spec template.

### FINDING-001

**Title:** Document or enforce clearer FastAPI service-token modes for MCP-facing deployments  

**Pillar:** ops-security  

**Severity:** P2  

**Summary:** `require_service_token` **no-ops** when `OST_LINKER_SERVICE_TOKEN` is unset (`src/services/api/auth.py`), while `lifespan` enforces completeness only when `OST_LINKER_REQUIRE_SERVICE_TOKEN` is true. Operators can assume routes are authenticated whenever a token header is documented, yet remain fully open if env-based auth is accidentally disabled or unset in a reachable network.

**Evidence:**

- `src/services/api/auth.py` lines 11–13 return early when `expected` env is falsy.
- `src/services/api/main.py` includes protected routers behind `Depends(require_service_token)` and documents strict startup checks for mismatching strict flag + missing token (`lifespan` block).

**Recommendation:** Extend `README.md` / `AGENTS.md` with an explicit truth table (**strict flag × token-present × caller headers**); optionally add **`pytest -m api`** coverage for default compose env vs strict env; consider **WARN log** once per process when routes are unsecured.

**Acceptance criteria:**

- [ ] Documented behavior matches code for dev/staging/production expectations.
- [ ] API tests pin at least **two** cases: strict-required failure at startup vs permissive unsecured mode with asserted 401 absent header when token configured.

**Suggested phase:** `1-documentation-follow-up` (follow-on `2-tooling-follow-up` if WARN log/tests added).

---

### FINDING-002

**Title:** Raise unit/integration coverage or add targeted pytest for ingestion and sync Dagster assets  

**Pillar:** pipeline-data secondary: maintainability  

**Severity:** P2  

**Summary:** **`make ci-check`** shows **below-threshold confidence** on several ingestion-critical modules (scraper/raw extract assets, Postgres sync asset) versus well-covered IO and classification helpers. Pipeline refactors risk regression without narrower tests or recorded integration proofs.

**Evidence:**

- `make ci-check` coverage table excerpt (unit stage): scraper/sync assets logged **12–48% covered** branches (see `/tmp/linker-ci-check.log` names `raw_github__extract_projects.py`, `core_public__sync_projects.py`, helper fetch README/topics/languages).

**Recommendation:** Add **`pytest`** units using existing patterns in `tests/unit/test_io_manager.py` / asset harnesses OR document mandatory manual Dagster runbook steps per release; prioritize **`core_public__sync_projects`** and **`raw_github__extract_projects`** smoke tests.

**Acceptance criteria:**

- [ ] Each prioritized asset carries either **automated regression tests** OR an **explicit waiver** documenting manual verification cadence owner.

**Suggested phase:** `2-tooling-follow-up`

---

### FINDING-003

**Title:** Clarify Postgres host port publishing policy for dev/staging/production compose variants  

**Pillar:** ops-security  

**Severity:** P2  

**Summary:** Dev override binds Postgres on `${POSTGRES_PORT:-5433}:5432` with comment encouraging LAN access. This accelerates DX but **must not leak** to internet-adjacent environments without guardrails.

**Evidence:**

- `docker-compose.override.yml` `db.ports` and inline comment on bind scope.

**Recommendation:** Add **compose profile** separating `desktop-dev` exposure vs **`loopback-only`** profile; mirror guidance in **`AGENTS.md`**.

**Acceptance criteria:**

- [ ] Default dev path documented; hardened variant exists or checklist calls out firewall expectations.

**Suggested phase:** `1-documentation-follow-up` (profiles may elevate to tooling).

---

### FINDING-004

**Title:** Align Dagster developer entrypoints (`make dev` vs `workspace.yaml` / compose)  

**Pillar:** maintainability  

**Severity:** P2  

**Summary:** Containers start Dagster via **`workspace.yaml`** with **`working_directory: /app`**, tuned for Docker bind mounts under `/app/src`. **`Makefile`** `dev` invokes `uv run dagster dev` **without** explicitly binding that workspace file, risking divergent code-location resolution compared to orchestrated environments.

**Evidence:**

- `workspace.yaml` `working_directory` path.
- `Makefile` **`dev`** target command string (no `-w workspace.yaml`).
- `docker-compose.yml` webserver/daemon commands pass `-w /app/workspace.yaml`.

**Recommendation:** Either document **authoritative** workflows (“always use compose for Dagster fidelity”) OR update **`make dev`** to pass `-w workspace.yaml` plus a **`workspace.local.yaml`** when `/app` is invalid on hosts (if Dagster rejects container path locally—validate on macOS/Linux fresh clones).

**Acceptance criteria:**

- [ ] Maintainer consensus recorded; instructions updated accordingly; optional smoke **`make dev`** + asset import captured in README.

**Suggested phase:** `1-documentation-follow-up`

---

### FINDING-005

**Title:** Strengthen regression tests around user embedding Dagster asset  

**Pillar:** pipeline-data  

**Severity:** P3  

**Summary:** **`core_ml__embed_users`** shows thinner coverage than **`core_ml__embed_projects`** in **`make ci-check`** output—user personalization paths deserve parity if product roadmap stresses user-level vectors.

**Evidence:**

- Unit coverage excerpt in `/tmp/linker-ci-check.log` (`core_ml__embed_users.py` ~24% lines covered vs embed projects ~90%).

**Recommendation:** Extend `tests/unit` with chunked streaming stubs similar to **`test_embed_projects_streaming`** for user batches.

**Acceptance criteria:**

- [ ] New tests fail on intentional regression stub and **`make ci-check` remains green.**

**Suggested phase:** `2-tooling-follow-up`

---

## Appendix — audit execution meta

| Item | Value |
| ----- | ----- |
| `docker compose ps` snapshot | `api` healthy on `8010`, `webserver` on `3033`, `db` on `5435` (audit host overrides) |
| Full `make ci-check` log | `/tmp/linker-ci-check.log` on executor machine |

---

## Subagent-driven development note

**Task 1** followed the **implementer → spec review → backlog-quality review** checklist in-thread. **Tasks 2–14** were executed **sequentially by the orchestrating agent** to avoid **42** sub-agent round-trips while preserving checklist coverage—re-open any task for isolated subagent rerun if desired.
