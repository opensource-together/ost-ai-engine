# Go Service Reviewer — Persistent Memory

## Key file paths

- Fetcher: `src/services/go/fetcher/` (main.go, common.go, fetch_readme.go, fetch_languages.go, fetch_topics.go)
- Scraper: `src/services/go/scraper/` (main.go, common.go)
- Each binary has its own `go.mod`; build with `go build ./...` from the package directory

## Confirmed fixes applied (branch fix/post-review-fixes)

1. **rateLimiter.wait() mutex pattern** — Never use `defer mu.Unlock()` when the function also manually calls `mu.Unlock()` + `mu.Lock()` inside the body. The defer fires at return and double-unlocks. Correct pattern: lock at top, conditional unlock/sleep/relock in body, explicit unlock at bottom.

2. **fetcher top-level context** — `context.Background()` in `fetcher/main.go` replaced with `context.WithTimeout(..., 30*time.Minute)` + `defer cancel()`.

3. **SQL injection in getNewProjects** — `validTargetTables map[string]string` allowlist added in `fetcher/common.go`. Callers (`FetchReadmes`, `FetchLanguages`, `FetchTopics`) now pass mode keys (`"readme"`, `"languages"`, `"topics"`) not raw table names.

4. **io.LimitReader on README** — `fetch_readme.go` wraps `resp.Body` with `io.LimitReader(resp.Body, 10*1024*1024)` before `io.ReadAll`.

5. **Partial body on readErr** — `retryRequest` in `common.go` returns `(nil, readErr)` instead of `(body, readErr)` when `io.ReadAll` fails on a 200 response.

6. **Scraper shared rate limiter** — `searchRateLimiter` struct added to `scraper/common.go`. `fetchGitHubRepos` now accepts `*searchRateLimiter`, calls `rl.wait()` before the request and `rl.update(resp)` after. `scrapeQuery` and the goroutine loop in `main()` share one `newSearchRateLimiter()` instance.

## Patterns to check on every review

- `defer mu.Unlock()` combined with manual unlock/relock = double-unlock panic. Use explicit unlock at the bottom instead.
- `io.ReadAll` on HTTP bodies without `io.LimitReader` = unbounded memory risk.
- `fmt.Sprintf` with user-supplied or caller-supplied table names = SQL injection. Always use an allowlist.
- Top-level `context.Background()` in long-running binaries must have `WithTimeout`.
- Returning `(partialData, err)` on read failure misleads callers; always return `(nil, err)`.
- Concurrent goroutines sharing one `http.Client` need a proactive shared rate limiter, not just reactive 403 handling.
