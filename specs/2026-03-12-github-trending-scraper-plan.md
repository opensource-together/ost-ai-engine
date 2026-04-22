# GitHub Trending Scraper — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Go binary that scrapes GitHub Trending daily, enriches repos via the GitHub API, stores them in a dedicated DB table, and exposes a new REST API endpoint — all integrated into the existing Dagster pipeline.

**Architecture:** New Go binary (`src/services/go/trending/`) follows the scraper pattern: subprocess invoked by Dagster, JSON summary on stdout. Data lands in `github.raw_trending_project`, served by a new `/recommendations/github-trending` API endpoint with LEFT JOIN to `public.Project` on `repoUrl`.

**Tech Stack:** Go 1.24, goquery (HTML parsing), pgx/v5, google/uuid, Dagster, FastAPI, psycopg2

**Spec:** `specs/2026-03-12-github-trending-scraper-design.md`

---

## Chunk 1: Go Binary Core

### Task 1: Initialize Go module

**Files:**
- Create: `src/services/go/trending/go.mod`
- Create: `src/services/go/trending/main.go` (empty main)

- [ ] **Step 1: Create go.mod**

```bash
mkdir -p src/services/go/trending
cd src/services/go/trending
go mod init github.com/opensource-together/ost-ai-engine/github-trending
```

- [ ] **Step 2: Add dependencies**

```bash
cd src/services/go/trending
go get github.com/PuerkitoBio/goquery
go get github.com/google/uuid
go get github.com/jackc/pgx/v5
```

- [ ] **Step 3: Create minimal main.go**

```go
package main

import "fmt"

func main() {
	fmt.Println("trending scraper placeholder")
}
```

- [ ] **Step 4: Verify it compiles**

```bash
cd src/services/go/trending && go build -o /dev/null .
```

Expected: success, no errors.

- [ ] **Step 5: Commit**

```bash
git add src/services/go/trending/
git commit -m "feat(trending): initialize Go module with dependencies"
```

---

### Task 2: HTML parsing — extract trending repos

**Files:**
- Create: `src/services/go/trending/parse.go`
- Create: `src/services/go/trending/parse_test.go`
- Create: `src/services/go/trending/testdata/trending.html` (sample HTML)

- [ ] **Step 1: Save a sample trending page for tests**

Fetch and save `https://github.com/trending?since=daily&spoken_language_code=en` HTML to `src/services/go/trending/testdata/trending.html`. This is test fixture data — trim it down to ~5 repo entries to keep it small.

```bash
cd src/services/go/trending
mkdir -p testdata
curl -s "https://github.com/trending?since=daily&spoken_language_code=en" \
  | head -2000 > testdata/trending.html
```

Verify the file contains `<article class="Box-row">` or similar repo entries.

- [ ] **Step 2: Write the failing test**

`src/services/go/trending/parse_test.go`:

```go
package main

import (
	"os"
	"strings"
	"testing"
)

func TestParseTrendingPage(t *testing.T) {
	htmlBytes, err := os.ReadFile("testdata/trending.html")
	if err != nil {
		t.Fatalf("failed to read test fixture: %v", err)
	}

	repos, err := parseTrendingPage(strings.NewReader(string(htmlBytes)))
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if len(repos) == 0 {
		t.Fatal("expected at least 1 trending repo, got 0")
	}

	for i, r := range repos {
		if r.Owner == "" || r.Repo == "" {
			t.Errorf("repo[%d]: owner or repo is empty: %+v", i, r)
		}
		if r.RepoURL == "" {
			t.Errorf("repo[%d]: repoURL is empty", i)
		}
	}
}

func TestParseTrendingPage_StarsToday(t *testing.T) {
	htmlBytes, err := os.ReadFile("testdata/trending.html")
	if err != nil {
		t.Fatalf("failed to read test fixture: %v", err)
	}

	repos, err := parseTrendingPage(strings.NewReader(string(htmlBytes)))
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	// At least some repos should have stars_today > 0
	hasStars := false
	for _, r := range repos {
		if r.StarsToday > 0 {
			hasStars = true
			break
		}
	}
	if !hasStars {
		t.Error("expected at least one repo with stars_today > 0")
	}
}

func TestParseTrendingPage_EmptyHTML(t *testing.T) {
	repos, err := parseTrendingPage(strings.NewReader("<html></html>"))
	if err != nil {
		t.Fatalf("unexpected error on empty html: %v", err)
	}
	if len(repos) != 0 {
		t.Errorf("expected 0 repos from empty html, got %d", len(repos))
	}
}
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd src/services/go/trending && go test -run TestParseTrendingPage -v
```

Expected: FAIL — `parseTrendingPage` undefined.

- [ ] **Step 4: Implement parseTrendingPage**

`src/services/go/trending/parse.go`:

```go
package main

import (
	"fmt"
	"io"
	"strconv"
	"strings"

	"github.com/PuerkitoBio/goquery"
)

// trendingRepo holds data extracted from the GitHub Trending HTML page.
type trendingRepo struct {
	Owner     string
	Repo      string
	RepoURL   string
	StarsToday int
}

// parseTrendingPage extracts trending repository info from the GitHub Trending HTML.
func parseTrendingPage(r io.Reader) ([]trendingRepo, error) {
	doc, err := goquery.NewDocumentFromReader(r)
	if err != nil {
		return nil, fmt.Errorf("parsing html: %w", err)
	}

	var repos []trendingRepo

	doc.Find("article.Box-row").Each(func(_ int, s *goquery.Selection) {
		// Repo link: h2 > a with href like "/owner/repo"
		link := s.Find("h2 a").First()
		href, exists := link.Attr("href")
		if !exists || href == "" {
			return
		}

		href = strings.TrimPrefix(href, "/")
		parts := strings.SplitN(href, "/", 2)
		if len(parts) != 2 || parts[0] == "" || parts[1] == "" {
			return
		}

		repo := trendingRepo{
			Owner:   parts[0],
			Repo:    parts[1],
			RepoURL: "https://github.com/" + href,
		}

		// Stars today: span with text like "1,234 stars today"
		s.Find("span.d-inline-block.float-sm-right").Each(func(_ int, star *goquery.Selection) {
			text := strings.TrimSpace(star.Text())
			if strings.Contains(text, "stars today") {
				numStr := strings.Split(text, " ")[0]
				numStr = strings.ReplaceAll(numStr, ",", "")
				if n, err := strconv.Atoi(numStr); err == nil {
					repo.StarsToday = n
				}
			}
		})

		repos = append(repos, repo)
	})

	return repos, nil
}
```

**IMPORTANT — Adapt selectors to actual HTML:** The CSS selectors above (`article.Box-row`, `h2 a`, `span.d-inline-block.float-sm-right`) are based on GitHub's known HTML structure but may have changed. **Before writing `parse.go`, inspect `testdata/trending.html`** and adapt:
1. Open the fixture file, search for the first repo link (e.g., `/microsoft/BitNet`)
2. Identify the container element (e.g., `article.Box-row` or `div.Box-row`)
3. Identify the link element (e.g., `h2 a[href]`)
4. Identify the "stars today" element (e.g., a `span` containing "stars today")
5. Update all selectors in `parseTrendingPage` to match

This step is critical — hardcoded selectors that don't match the HTML will produce 0 results.

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd src/services/go/trending && go test -run TestParseTrendingPage -v
```

Expected: all 3 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/services/go/trending/parse.go src/services/go/trending/parse_test.go src/services/go/trending/testdata/
git commit -m "feat(trending): implement HTML parsing for GitHub Trending page"
```

---

### Task 3: GitHub API client — fetch repo details

**Files:**
- Create: `src/services/go/trending/github.go`
- Create: `src/services/go/trending/github_test.go`

- [ ] **Step 1: Write the failing test**

`src/services/go/trending/github_test.go`:

```go
package main

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestFetchRepoDetails(t *testing.T) {
	expectedRepo := map[string]any{
		"id":               12345,
		"full_name":        "octocat/Hello-World",
		"html_url":         "https://github.com/octocat/Hello-World",
		"stargazers_count": 1500,
		"description":      "A test repo",
		"language":         "Go",
	}

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/repos/octocat/Hello-World" {
			t.Errorf("unexpected path: %s", r.URL.Path)
			w.WriteHeader(404)
			return
		}
		if got := r.Header.Get("User-Agent"); got != "ost-linker-trending" {
			t.Errorf("User-Agent = %q, want ost-linker-trending", got)
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(expectedRepo)
	}))
	defer server.Close()

	client := newGitHubClient("fake-token", server.URL)
	data, err := client.fetchRepoDetails(context.Background(), "octocat", "Hello-World")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	var result map[string]any
	if err := json.Unmarshal(data, &result); err != nil {
		t.Fatalf("failed to unmarshal result: %v", err)
	}
	if result["full_name"] != "octocat/Hello-World" {
		t.Errorf("full_name = %v, want octocat/Hello-World", result["full_name"])
	}
}

func TestFetchRepoDetails_Retry(t *testing.T) {
	attempts := 0
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		attempts++
		if attempts < 2 {
			w.WriteHeader(500)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]any{"id": 1})
	}))
	defer server.Close()

	client := newGitHubClient("fake-token", server.URL)
	_, err := client.fetchRepoDetails(context.Background(), "octocat", "Hello-World")
	if err != nil {
		t.Fatalf("expected retry to succeed, got: %v", err)
	}
	if attempts != 2 {
		t.Errorf("expected 2 attempts, got %d", attempts)
	}
}

func TestFetchRepoDetails_404(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(404)
	}))
	defer server.Close()

	client := newGitHubClient("fake-token", server.URL)
	_, err := client.fetchRepoDetails(context.Background(), "octocat", "doesnt-exist")
	if err == nil {
		t.Fatal("expected error for 404, got nil")
	}
}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd src/services/go/trending && go test -run TestFetchRepo -v
```

Expected: FAIL — `newGitHubClient` and `fetchRepoDetails` undefined.

- [ ] **Step 3: Implement GitHub API client**

`src/services/go/trending/github.go`:

```go
package main

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"time"
)

const (
	defaultAPIBase = "https://api.github.com"
	maxRetries     = 2
	userAgent      = "ost-linker-trending"
)

type gitHubClient struct {
	httpClient *http.Client
	token      string
	apiBase    string
}

func newGitHubClient(token, apiBase string) *gitHubClient {
	if apiBase == "" {
		apiBase = defaultAPIBase
	}
	return &gitHubClient{
		httpClient: &http.Client{Timeout: 30 * time.Second},
		token:      token,
		apiBase:    apiBase,
	}
}

// fetchRepoDetails calls GET /repos/{owner}/{repo} and returns the raw JSON body.
func (c *gitHubClient) fetchRepoDetails(ctx context.Context, owner, repo string) ([]byte, error) {
	url := fmt.Sprintf("%s/repos/%s/%s", c.apiBase, owner, repo)

	var lastErr error
	for attempt := 0; attempt <= maxRetries; attempt++ {
		if attempt > 0 {
			time.Sleep(time.Duration(attempt) * 2 * time.Second)
		}

		req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
		if err != nil {
			return nil, fmt.Errorf("creating request: %w", err)
		}
		req.Header.Set("User-Agent", userAgent)
		req.Header.Set("Accept", "application/vnd.github+json")
		req.Header.Set("X-GitHub-Api-Version", "2022-11-28")
		if c.token != "" {
			req.Header.Set("Authorization", "token "+c.token)
		}

		resp, err := c.httpClient.Do(req)
		if err != nil {
			lastErr = err
			continue
		}

		body, readErr := io.ReadAll(resp.Body)
		resp.Body.Close()

		if resp.StatusCode == 404 || resp.StatusCode == 422 {
			return nil, fmt.Errorf("repo %s/%s: %d", owner, repo, resp.StatusCode)
		}
		if resp.StatusCode >= 500 || resp.StatusCode == 403 {
			lastErr = fmt.Errorf("repo %s/%s: %d", owner, repo, resp.StatusCode)
			continue
		}
		if resp.StatusCode != 200 {
			return nil, fmt.Errorf("repo %s/%s: unexpected status %d", owner, repo, resp.StatusCode)
		}
		if readErr != nil {
			lastErr = readErr
			continue
		}

		return body, nil
	}
	return nil, fmt.Errorf("repo %s/%s: all retries exhausted: %w", owner, repo, lastErr)
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd src/services/go/trending && go test -run TestFetchRepo -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/services/go/trending/github.go src/services/go/trending/github_test.go
git commit -m "feat(trending): add GitHub API client with retry logic"
```

---

### Task 4: Main orchestration — scrape, enrich, upsert, output

**Files:**
- Modify: `src/services/go/trending/main.go` (replace placeholder)
- Create: `src/services/go/trending/main_test.go`

- [ ] **Step 1: Write the failing test for env parsing**

`src/services/go/trending/main_test.go`:

```go
package main

import (
	"encoding/json"
	"testing"
)

func TestSummaryJSON(t *testing.T) {
	s := trendingSummary{
		Collected:       25,
		Upserted:        23,
		Failed:          2,
		TrendingDate:    "2026-03-12",
		Status:          "partial",
		DurationSeconds: 12.5,
	}

	data, err := json.Marshal(s)
	if err != nil {
		t.Fatalf("failed to marshal summary: %v", err)
	}

	var decoded map[string]any
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("failed to unmarshal: %v", err)
	}

	if decoded["collected"] != float64(25) {
		t.Errorf("collected = %v, want 25", decoded["collected"])
	}
	if decoded["status"] != "partial" {
		t.Errorf("status = %v, want partial", decoded["status"])
	}
	if decoded["trending_date"] != "2026-03-12" {
		t.Errorf("trending_date = %v, want 2026-03-12", decoded["trending_date"])
	}
}

func TestRequireEnv(t *testing.T) {
	t.Setenv("DATABASE_URL", "")
	_, err := requireEnv("DATABASE_URL")
	if err == nil {
		t.Fatal("expected error for empty DATABASE_URL")
	}

	t.Setenv("DATABASE_URL", "postgres://test")
	val, err := requireEnv("DATABASE_URL")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if val != "postgres://test" {
		t.Errorf("got %q, want postgres://test", val)
	}
}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd src/services/go/trending && go test -run "TestSummaryJSON|TestRequireEnv" -v
```

Expected: FAIL — `trendingSummary` and `requireEnv` undefined.

- [ ] **Step 3: Implement main.go**

Replace `src/services/go/trending/main.go` with:

```go
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

const trendingURL = "https://github.com/trending?since=daily&spoken_language_code=en"

type trendingSummary struct {
	Collected       int     `json:"collected"`
	Upserted        int     `json:"upserted"`
	Failed          int     `json:"failed"`
	TrendingDate    string  `json:"trending_date"`
	Status          string  `json:"status"`
	DurationSeconds float64 `json:"duration_seconds"`
}

func requireEnv(key string) (string, error) {
	v := os.Getenv(key)
	if v == "" {
		return "", fmt.Errorf("%s is required but not set", key)
	}
	return v, nil
}

func main() {
	start := time.Now()
	today := time.Now().Format("2006-01-02")

	dbURL, err := requireEnv("DATABASE_URL")
	if err != nil {
		log.Fatal(err)
	}
	token := os.Getenv("GITHUB_ACCESS_TOKEN")
	if token == "" {
		log.Println("[WARN] GITHUB_ACCESS_TOKEN not set; API calls may be rate-limited")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()

	// 1. Fetch trending page HTML
	log.Println("[INFO] Fetching GitHub Trending page")
	resp, err := http.Get(trendingURL)
	if err != nil {
		log.Fatalf("failed to fetch trending page: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		log.Fatalf("trending page returned status %d", resp.StatusCode)
	}

	// 2. Parse HTML
	trendingRepos, err := parseTrendingPage(resp.Body)
	if err != nil {
		log.Fatalf("failed to parse trending page: %v", err)
	}
	log.Printf("[INFO] Parsed %d trending repos", len(trendingRepos))

	if len(trendingRepos) == 0 {
		log.Fatal("[ERROR] No trending repos found — HTML structure may have changed")
	}

	// 3. Connect to DB
	pool, err := pgxpool.New(ctx, dbURL)
	if err != nil {
		log.Fatalf("failed to create DB pool: %v", err)
	}
	defer pool.Close()

	// 4. Fetch repo details from GitHub API and upsert
	ghClient := newGitHubClient(token, "")
	summary := trendingSummary{
		Collected:    len(trendingRepos),
		TrendingDate: today,
	}

	batch := &pgx.Batch{}
	for _, tr := range trendingRepos {
		data, err := ghClient.fetchRepoDetails(ctx, tr.Owner, tr.Repo)
		if err != nil {
			log.Printf("[WARN] Failed to fetch %s/%s: %v", tr.Owner, tr.Repo, err)
			summary.Failed++
			continue
		}

		projectID := uuid.NewSHA1(uuid.NameSpaceURL, []byte(tr.RepoURL))

		batch.Queue(`
			INSERT INTO "github"."raw_trending_project"
				("id", "project_id", "repo_url", "data", "trending_date", "stars_today", "created_at")
			VALUES (gen_random_uuid(), $1, $2, $3, $4::date, $5, NOW())
			ON CONFLICT ("project_id", "trending_date") DO UPDATE
			SET "data" = EXCLUDED."data",
			    "stars_today" = EXCLUDED."stars_today",
			    "repo_url" = EXCLUDED."repo_url"
		`, projectID.String(), tr.RepoURL, data, today, tr.StarsToday)
	}

	if batch.Len() > 0 {
		dbCtx, dbCancel := context.WithTimeout(ctx, 30*time.Second)
		br := pool.SendBatch(dbCtx, batch)
		for i := 0; i < batch.Len(); i++ {
			if _, err := br.Exec(); err != nil {
				log.Printf("[ERROR] Upsert failed (batch item %d): %v", i, err)
				summary.Failed++
			} else {
				summary.Upserted++
			}
		}
		br.Close()
		dbCancel()
	}

	summary.DurationSeconds = time.Since(start).Seconds()
	summary.Status = "success"
	if summary.Failed > 0 {
		summary.Status = "partial"
	}

	if err := json.NewEncoder(os.Stdout).Encode(summary); err != nil {
		log.Fatalf("json encode: %v", err)
	}
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd src/services/go/trending && go test -v
```

Expected: all tests PASS.

- [ ] **Step 5: Verify it compiles**

```bash
cd src/services/go/trending && go build -o /dev/null .
```

Expected: success.

- [ ] **Step 6: Commit**

```bash
git add src/services/go/trending/main.go src/services/go/trending/main_test.go
git commit -m "feat(trending): implement main orchestration — scrape, enrich, upsert"
```

---

## Chunk 2: Database, Dagster & Infrastructure

### Task 5: Add Prisma model

**Files:**
- Modify: `prisma/schema.prisma` (add `RawTrendingProject` model after `RawGithubProject` at ~line 389)

- [ ] **Step 1: Add model to Prisma schema**

Add after the `RawGithubProject` model (after line 389 in `prisma/schema.prisma`):

```prisma
model RawTrendingProject {
  id            String   @id @default(uuid()) @db.Uuid
  project_id    String
  repo_url      String
  data          Json
  trending_date DateTime @db.Date
  stars_today   Int?
  created_at    DateTime @default(now())

  @@unique([project_id, trending_date])
  @@map("raw_trending_project")
  @@schema("github")
}
```

- [ ] **Step 2: Validate Prisma schema**

```bash
npx prisma validate
```

Expected: "The schema is valid."

- [ ] **Step 3: Commit**

```bash
git add prisma/schema.prisma
git commit -m "feat(trending): add RawTrendingProject to Prisma schema"
```

---

### Task 6: Dagster asset + config

**Files:**
- Create: `src/linker/assets/scraper/raw_github__extract_trending.py`
- Modify: `src/linker/resources/cfg_resource.py` (add `go_trending_path`, `build_trending_env`)
- Modify: `src/linker/definitions.py` (import asset, add config)

- [ ] **Step 1: Add config fields**

In `src/linker/resources/cfg_resource.py`:

Add `go_trending_path` to `PipelineConfig` (after `go_fetcher_path: str`, ~line 72):

```python
    go_trending_path: str = ""
```

**Note:** The default `""` matters because `definitions.py` will use `EnvVar("GO_TRENDING_PATH")` which would crash if unset. To make it truly optional, we'll handle it differently in Step 3.

Add `build_trending_env` function (after `build_fetcher_env`, ~line 107):

```python
def build_trending_env(cfg: PipelineConfig) -> dict[str, str]:
    """Return environment dict for the Go trending scraper subprocess."""
    env: dict[str, str] = {"DATABASE_URL": cfg.db_url}
    if cfg.github_token:
        env["GITHUB_ACCESS_TOKEN"] = cfg.github_token
    return env
```

- [ ] **Step 2: Create asset file**

`src/linker/assets/scraper/raw_github__extract_trending.py`:

```python
import json
import os
import subprocess

from dagster import (
    AssetExecutionContext,
    AssetKey,
    MetadataValue,
    Output,
    asset,
)

from ...resources.cfg_resource import build_trending_env

DEFAULT_OWNERS = ["team:OST/spideyai-X"]


@asset(
    kinds={"go", "postgres"},
    owners=DEFAULT_OWNERS,
    group_name="ingestion",
    required_resource_keys={"config"},
    key=AssetKey(["github", "raw_trending_project"]),
)
def raw_github__extract_trending(context: AssetExecutionContext) -> Output[None]:
    """Execute Go trending scraper to fetch GitHub Trending repos and write to DB."""
    context.log.info("raw_github__extract_trending: Starting GitHub Trending scraper")
    cfg = context.resources.config

    env = os.environ.copy()
    env.update(build_trending_env(cfg))

    if "DATABASE_URL" not in env:
        msg = "DATABASE_URL must be set in environment or config for trending scraper"
        raise ValueError(msg)

    trending_path = cfg.go_trending_path
    if not trending_path:
        raise RuntimeError("GO_TRENDING_PATH not configured")

    if not os.path.exists(trending_path):
        raise RuntimeError(f"Go trending binary not found at {trending_path}")

    context.log.info(f"Using trending scraper at {trending_path}")

    try:
        result = subprocess.run(
            [trending_path],
            capture_output=True,
            text=True,
            env=env,
            cwd=os.getcwd(),
            timeout=300,
        )

        stdout = result.stdout
        stderr = result.stderr

        if result.returncode != 0:
            context.log.error(f"Trending scraper exited with code {result.returncode}")
            context.log.error(f"Stderr: {stderr}")
            context.log.error(f"Stdout: {stdout}")
            raise RuntimeError(
                f"Trending scraper failed (exit {result.returncode})"
            )

        context.log.info(f"Trending scraper stdout: {stdout}")
        if stderr:
            context.log.warning(f"Trending scraper stderr: {stderr}")

        try:
            summary = json.loads(stdout)
        except Exception:
            context.log.warning("Could not parse trending scraper summary JSON")
            return Output(
                value=None,
                metadata={"status": "completed_via_go_unparsed"},
            )

        return Output(
            value=None,
            metadata={
                "collected": MetadataValue.int(summary.get("collected", 0)),
                "upserted": MetadataValue.int(summary.get("upserted", 0)),
                "failed": MetadataValue.int(summary.get("failed", 0)),
                "trending_date": MetadataValue.text(
                    summary.get("trending_date", "unknown")
                ),
                "duration_seconds": MetadataValue.float(
                    summary.get("duration_seconds", 0)
                ),
                "status": MetadataValue.text(summary.get("status", "unknown")),
            },
        )

    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Trending scraper timed out after 300s") from exc
    except Exception as e:
        context.log.error(f"Trending scraper execution error: {e}")
        raise
```

- [ ] **Step 3: Wire asset in definitions.py**

In `src/linker/definitions.py`:

Add import (after `raw_github__extract_projects` import, ~line 44):
```python
    raw_github__extract_trending,
```

Add to `load_assets_from_modules` list (~line 53):
```python
        raw_github__extract_trending,
```

Conditionally pass `go_trending_path` only if the env var is set (~line 97). Since `PipelineConfig` has a default of `""`, omitting it is safe:

```python
            **({
                "go_trending_path": EnvVar("GO_TRENDING_PATH"),
            } if os.getenv("GO_TRENDING_PATH") else {}),
```

**Why:** Using `EnvVar("GO_TRENDING_PATH")` unconditionally would crash existing deployments that don't have this env var. The conditional spread keeps it optional.

- [ ] **Step 4: Verify Dagster loads without errors**

```bash
dagster definitions validate -m src.linker.definitions 2>&1 | head -5
```

Expected: no import errors. (May warn about missing env vars — that's OK.)

- [ ] **Step 5: Commit**

```bash
git add src/linker/assets/scraper/raw_github__extract_trending.py src/linker/resources/cfg_resource.py src/linker/definitions.py
git commit -m "feat(trending): add Dagster asset and config for trending scraper"
```

---

### Task 7: REST API endpoint

**Files:**
- Modify: `src/services/api/routes/recommendations.py` (add endpoint)
- Modify: `src/services/api/schemas.py` (add response schema)
- Create: `tests/api/test_github_trending.py`

- [ ] **Step 1: Write the failing test**

`tests/api/test_github_trending.py`:

```python
from datetime import date
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.services.api.dependencies import get_pool
from src.services.api.main import app


def _make_pool(rows: list[dict]) -> MagicMock:
    """Create a mock pool whose cursor returns given rows."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = rows
    mock_pool = MagicMock()
    mock_pool.get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_pool.get_cursor.return_value.__exit__ = MagicMock(return_value=False)
    return mock_pool


class TestGithubTrending:
    def test_returns_trending_list(self, client: TestClient) -> None:
        """GET /recommendations/github-trending returns trending repos."""
        pool = _make_pool(
            [
                {
                    "repo_url": "https://github.com/octocat/Hello-World",
                    "data": {
                        "name": "Hello-World",
                        "full_name": "octocat/Hello-World",
                        "description": "A test repo",
                        "stargazers_count": 1500,
                        "language": "Go",
                    },
                    "stars_today": 200,
                    "trending_date": date(2026, 3, 12),
                    "linked_project_id": None,
                    "categoryId": None,
                    "domainId": None,
                },
            ]
        )
        app.dependency_overrides[get_pool] = lambda: pool
        try:
            response = client.get("/recommendations/github-trending")
        finally:
            app.dependency_overrides.pop(get_pool, None)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["repo_url"] == "https://github.com/octocat/Hello-World"
        assert data[0]["stars_today"] == 200
        assert data[0]["full_name"] == "octocat/Hello-World"
        assert data[0]["name"] == "Hello-World"

    def test_with_linked_project(self, client: TestClient) -> None:
        """LEFT JOIN enriches response when project exists in public.Project."""
        pool = _make_pool(
            [
                {
                    "repo_url": "https://github.com/octocat/Hello-World",
                    "data": {
                        "name": "Hello-World",
                        "full_name": "octocat/Hello-World",
                        "description": "A test repo",
                        "stargazers_count": 1500,
                        "language": "Go",
                    },
                    "stars_today": 200,
                    "trending_date": date(2026, 3, 12),
                    "linked_project_id": "abc-123",
                    "categoryId": "cat-1",
                    "domainId": "dom-1",
                },
            ]
        )
        app.dependency_overrides[get_pool] = lambda: pool
        try:
            response = client.get("/recommendations/github-trending")
        finally:
            app.dependency_overrides.pop(get_pool, None)

        assert response.status_code == 200
        data = response.json()
        assert data[0]["linked_project_id"] == "abc-123"
        assert data[0]["category_id"] == "cat-1"

    def test_respects_limit(self, client: TestClient) -> None:
        """GET /recommendations/github-trending?limit=5 limits results."""
        pool = _make_pool([])
        app.dependency_overrides[get_pool] = lambda: pool
        try:
            response = client.get("/recommendations/github-trending?limit=5")
        finally:
            app.dependency_overrides.pop(get_pool, None)

        assert response.status_code == 200

    def test_limit_validation(self, client: TestClient) -> None:
        """Limit must be between 1 and 50."""
        pool = _make_pool([])
        app.dependency_overrides[get_pool] = lambda: pool
        try:
            response = client.get("/recommendations/github-trending?limit=0")
        finally:
            app.dependency_overrides.pop(get_pool, None)

        assert response.status_code == 422
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/api/test_github_trending.py -v
```

Expected: FAIL — 404 on `/recommendations/github-trending`.

- [ ] **Step 3: Add response schema**

In `src/services/api/schemas.py`, add after `TrendingProjectOut` (~line 48):

```python
class GithubTrendingProjectOut(BaseModel):
    repo_url: str
    stars_today: int | None = None
    trending_date: date
    name: str
    full_name: str
    description: str | None = None
    stars: int | None = None
    language: str | None = None
    linked_project_id: str | None = None
    category_id: str | None = None
    domain_id: str | None = None
```

Add `date` to the imports at line 1:

```python
from datetime import date, datetime
```

- [ ] **Step 4: Add endpoint**

In `src/services/api/routes/recommendations.py`, add the import for the new schema (update line 8):

```python
from src.services.api.schemas import GithubTrendingProjectOut, TrendingProjectOut
```

Add the endpoint after `get_trending` (~line 30):

```python
@router.get("/github-trending", response_model=list[GithubTrendingProjectOut])
@limiter.limit("60/minute")
def get_github_trending(
    request: Request,
    limit: int = Query(default=25, ge=1, le=50),
    pool: ConnectionPool = Depends(get_pool),
) -> list[dict[str, Any]]:
    """Get repos currently trending on GitHub."""
    with pool.get_cursor() as cur:
        cur.execute(
            """SELECT
                 t.repo_url, t.data, t.stars_today, t.trending_date,
                 p.id AS linked_project_id, p.name, p.description,
                 p."categoryId", p."domainId"
               FROM github.raw_trending_project t
               LEFT JOIN public."Project" p
                 ON t.repo_url = p."repoUrl"
               WHERE t.trending_date = CURRENT_DATE
               ORDER BY t.stars_today DESC NULLS LAST
               LIMIT %s""",
            (limit,),
        )
        rows = cur.fetchall()

    results = []
    for row in rows:
        data = row.get("data") or {}
        results.append(
            {
                "repo_url": row["repo_url"],
                "stars_today": row.get("stars_today"),
                "trending_date": row["trending_date"],
                "name": data.get("name", ""),
                "full_name": data.get("full_name", ""),
                "description": data.get("description"),
                "stars": data.get("stargazers_count"),
                "language": data.get("language"),
                "linked_project_id": row.get("linked_project_id"),
                "category_id": row.get("categoryId"),
                "domain_id": row.get("domainId"),
            }
        )
    return results
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/api/test_github_trending.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 6: Run all API tests to check for regressions**

```bash
pytest -m api -v
```

Expected: all PASS.

- [ ] **Step 7: Lint and type check**

```bash
ruff check src/services/api/ && ruff format src/services/api/ && mypy src/services/api/
```

Expected: no errors.

- [ ] **Step 8: Commit**

```bash
git add src/services/api/routes/recommendations.py src/services/api/schemas.py tests/api/test_github_trending.py
git commit -m "feat(api): add /recommendations/github-trending endpoint"
```

---

## Chunk 3: Docker, CI & Infrastructure

### Task 8: Docker build

**Files:**
- Modify: `Dockerfile` (add trending build + copy)
- Modify: `docker-compose.yml` (add env var)

- [ ] **Step 1: Update Dockerfile — Go builder stage**

In `Dockerfile`, after line 13 (`COPY src/services/go/scraper ./src/services/go/scraper`), add:

```dockerfile
COPY src/services/go/trending ./src/services/go/trending
```

After line 21 (fetcher build), add:

```dockerfile
# Build Trending Scraper
WORKDIR /app/src/services/go/trending
RUN CGO_ENABLED=0 go mod download && go build -ldflags="-s -w" -o /app/bin/ost-trending .
```

- [ ] **Step 2: Update Dockerfile — runtime stage**

After line 70 (`COPY --from=go-builder /app/bin/ost-scraper /usr/local/bin/ost-scraper`), add:

```dockerfile
COPY --from=go-builder /app/bin/ost-trending /usr/local/bin/ost-trending
```

- [ ] **Step 3: Update docker-compose.yml**

In `x-common-env` (~line 10), after `GO_FETCHER_PATH`, add:

```yaml
  GO_TRENDING_PATH: /usr/local/bin/ost-trending
```

- [ ] **Step 4: Verify Docker build**

```bash
docker compose build webserver 2>&1 | tail -5
```

Expected: build succeeds.

- [ ] **Step 5: Commit**

```bash
git add Dockerfile docker-compose.yml
git commit -m "chore(docker): add trending scraper to build and compose"
```

---

### Task 9: Scripts, env, CI

**Files:**
- Modify: `scripts/go_binary_gen.sh` (add trending)
- Modify: `.env.example` (add `GO_TRENDING_PATH`)
- Modify: `.github/workflows/quality-checks.yml` (add Go test step)

- [ ] **Step 1: Update go_binary_gen.sh**

Append to the end of `scripts/go_binary_gen.sh`:

```bash

# Trending Scraper
GITHUB_TRENDING_DIR="$PROJECT_ROOT/src/services/go/trending"
GITHUB_TRENDING_BIN="$PROJECT_ROOT/data/ost-trending"
echo "Compiling GitHub Trending Scraper..."
cd "$GITHUB_TRENDING_DIR"
go build -o "$GITHUB_TRENDING_BIN" .
echo "Binary generated: $GITHUB_TRENDING_BIN"
```

- [ ] **Step 2: Update .env.example**

After `GO_FETCHER_PATH` (~line 43), add:

```
GO_TRENDING_PATH="/path/to/ost-linker/src/services/go/trending/ost-trending"
```

- [ ] **Step 3: Update CI workflow**

In `.github/workflows/quality-checks.yml`, after the fetcher test step (~line 93), add:

```yaml
      - name: Vet, build and test trending
        run: |
          cd src/services/go/trending
          go vet ./...
          go build -o /dev/null .
          go test ./...
```

- [ ] **Step 4: Commit**

```bash
git add scripts/go_binary_gen.sh .env.example .github/workflows/quality-checks.yml
git commit -m "chore: add trending scraper to build scripts, env, and CI"
```

---

### Task 10: Final verification

- [ ] **Step 1: Run all Go tests**

```bash
cd src/services/go/trending && go test -v
```

Expected: all PASS.

- [ ] **Step 2: Run all Python tests**

```bash
pytest -v
```

Expected: all PASS.

- [ ] **Step 3: Lint and type check**

```bash
ruff check src/ && ruff format --check src/ && mypy src/
```

Expected: no errors.

- [ ] **Step 4: Verify Docker build**

```bash
docker compose build 2>&1 | tail -10
```

Expected: build succeeds.
