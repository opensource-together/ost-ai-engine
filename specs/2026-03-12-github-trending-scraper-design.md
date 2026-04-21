# GitHub Trending Scraper — Design Spec

## Context

OST Linker scrapes GitHub for open-source projects via the Search API (~3000 repos/day). Users want a complementary "trending" section showing what's hot on GitHub right now. GitHub Trending (`/trending`) surfaces ~25 repos/day that are gaining stars rapidly — a useful discovery signal distinct from our contribution-focused scraper.

## Goal

Add a new Go binary that scrapes GitHub Trending daily, enriches each repo via the GitHub REST API, stores results in a dedicated table, and exposes them through a new API endpoint. The trending scraper runs in parallel with the existing scraper inside the same Dagster job.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Source URL | `/trending?since=daily&spoken_language_code=en` | English filter aligns with existing FastText language detection |
| Architecture | New Go binary (not extend fetcher) | Different flow (HTML scrape → API enrich vs. enrich existing). Clean separation of concerns |
| Data retention | Keep history with `trending_date` | Avoids data loss on scrape failures; enables future trend analysis |
| API endpoint | New `/recommendations/github-trending` | Separate from existing `/recommendations/trending` (different data source) |
| Linkage with existing projects | LEFT JOIN on `repo_url` | Enriches response with category/domain when project exists in base |
| Top 5 vs rest | Consumer decides | API returns ordered list; ost-mcp handles display split |
| dbt model | Not needed for MVP | Raw table consumed directly by API |

## Design

### 1. Go Binary — `src/services/go/trending/`

New independent Go module following the existing scraper pattern (subprocess → JSON stdout → Dagster parses).

**Flow:**
```
GET github.com/trending?since=daily&spoken_language_code=en
  -> parse HTML, extract ~25 owner/repo + stars_today
  -> for each: GET api.github.com/repos/{owner}/{repo}
  -> batch upsert into github.raw_trending_project
  -> JSON summary to stdout
```

**Files:**
- `main.go` — entry point, HTML parsing, API calls, DB upsert, orchestration
- `common.go` — rate limiter (5000 req/h general API), retry logic, shared types
- `go.mod` / `go.sum`
- `main_test.go` / `common_test.go`

**Environment variables:**
- `DATABASE_URL` — PostgreSQL connection string (required)
- `GITHUB_ACCESS_TOKEN` — GitHub token for `/repos/` API calls (optional but recommended — 5000 vs 60 req/h). Not used for HTML scraping

**Stdout JSON output:**
```json
{
  "collected": 25,
  "upserted": 25,
  "failed": 0,
  "trending_date": "2026-03-12",
  "status": "success",
  "duration_seconds": 12.3
}
```

**HTML parsing strategy:**
- Use `goquery` (Go jQuery-like library) to parse the trending page HTML — extract repo links (`/{owner}/{repo}`) and the "X stars today" badge
- `goquery` is more resilient to minor HTML changes than raw regex
- If HTML structure changes fundamentally and parsing returns 0 repos, the binary exits with error status and Dagster retries
- **Risk:** `/trending` is an undocumented HTML page — GitHub can change it without notice. This is a known fragility; monitoring via Dagster asset failure alerts

**Rate limiting:**
- General GitHub API: 5000 req/h authenticated, 60 req/h unauthenticated
- ~25 requests for repo details — well within limits
- Reuse the same retry pattern as fetcher (2 attempts, exponential backoff, respect `Retry-After`)

**DB write pattern:**
- `pgx.Batch` for bulk upsert (same as scraper)
- `project_id` = `uuid.NewSHA1(uuid.NameSpaceURL, []byte(repoURL))` — same as `raw_github_project` for joinability
- Upsert on `(project_id, trending_date)` unique constraint

### 2. Database Table — `github.raw_trending_project`

**Prisma schema addition:**
```prisma
model RawTrendingProject {
  id             String   @id @default(uuid()) @db.Uuid
  project_id     String
  repo_url       String
  data           Json
  trending_date  DateTime @db.Date
  stars_today    Int?
  created_at     DateTime @default(now())

  @@unique([project_id, trending_date])
  @@map("raw_trending_project")
  @@schema("github")
}
```

**Key design choices:**
- `project_id` uses the same SHA1-of-URL scheme as `raw_github_project` — enables joins with raw tables. Join with `public.Project` uses `repo_url` instead (since Project.id is a random v4 UUID)
- `@@unique([project_id, trending_date])` — a repo can only appear once per day; upsert-friendly
- `data` stores the full `/repos/{owner}/{repo}` API response — future-proof
- `stars_today` extracted from HTML — primary sort key for the API

### 3. Dagster Integration

**New asset:** `raw_github__extract_trending`
- File: `src/linker/assets/scraper/raw_github__extract_trending.py`
- Group: `ingestion`
- Same subprocess pattern as `raw_github__extract_projects`
- Timeout: 300 seconds (generous for unauthenticated API fallback at 60 req/h)

**Job integration — parallel execution:**
The new asset belongs to the `ingestion` group. Since `project_enrichment_job` selects `AssetSelection.groups("ingestion", ...)`, the trending asset is automatically included. Both scraper assets run in parallel within the job (no dependency between them — they write to different tables).

```
project_enrichment_job (ingestion group):
  ├── raw_github__extract_projects    (existing, ~3000 repos)
  └── raw_github__extract_trending    (new, ~25 repos)
      (no dependency — parallel)
```

**Config resource changes (`cfg_resource.py`):**
- Add `go_trending_path: str` to `PipelineConfig` with default `""` (empty string) to avoid breaking existing deployments without `GO_TRENDING_PATH` set
- Add `build_trending_env(cfg) -> dict` helper (DATABASE_URL + GITHUB_ACCESS_TOKEN)

**Definitions wiring (`definitions.py`):**
- Import new asset
- Add `GO_TRENDING_PATH` env var resolution

### 4. REST API Endpoint

**New endpoint:** `GET /recommendations/github-trending`

**File:** `src/services/api/routes/recommendations.py` (add to existing router)

**Query parameters:**
- `limit: int` — default 25, min 1, max 50

**SQL query:**
```sql
SELECT
  t.repo_url, t.data, t.stars_today, t.trending_date,
  p.id AS linked_project_id, p.name, p.description,
  p."categoryId", p."domainId"
FROM github.raw_trending_project t
LEFT JOIN public."Project" p
  ON t.repo_url = p."repoUrl"
WHERE t.trending_date = CURRENT_DATE
ORDER BY t.stars_today DESC NULLS LAST
LIMIT %s
```

**Response schema (`schemas.py`):**
```python
class GithubTrendingProjectOut(BaseModel):
    repo_url: str
    stars_today: int | None = None
    trending_date: date
    # From GitHub API (extracted from data JSON)
    name: str
    full_name: str
    description: str | None = None
    stars: int | None = None
    language: str | None = None
    # Enriched from public.Project (nullable — only if project exists in base)
    linked_project_id: str | None = None
    category_id: str | None = None
    domain_id: str | None = None
```

### 5. Docker & Infrastructure

**Dockerfile additions:**
```dockerfile
# In Go builder stage:
WORKDIR /app/src/services/go/trending
RUN CGO_ENABLED=0 go mod download && go build -ldflags="-s -w" -o /app/bin/ost-trending .

# In runtime stage:
COPY --from=go-builder /app/bin/ost-trending /usr/local/bin/ost-trending
```

**docker-compose.yml:** Add `GO_TRENDING_PATH: /usr/local/bin/ost-trending` to `x-common-env`.

**scripts/go_binary_gen.sh:** Add trending binary compilation.

**.env.example:** Add `GO_TRENDING_PATH=`.

**CI (`quality-checks.yml`):** Add `cd src/services/go/trending && go test ./...` alongside existing scraper/fetcher test steps.

### 6. Testing Strategy

**Go unit tests:**
- HTML parsing with sample trending page HTML
- Stdout JSON output format validation
- Error handling (malformed HTML, API failures)

**Python/Dagster:**
- Asset invocation test (mock subprocess, verify env vars and output parsing)

**API:**
- Endpoint test with mock DB data
- LEFT JOIN behavior: with and without linked project

## Out of Scope (future)

- dbt model for trending data transformation
- Multiple language filters (`/trending/python`, `/trending/typescript`)
- Weekly/monthly trending periods
- Trending score integration into global recommendation algorithm
