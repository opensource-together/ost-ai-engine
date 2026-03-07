# Go Black Flash — Agent Memory

## Key file paths

- Scraper: `src/services/go/scraper/` (main.go, common.go, common_test.go, main_test.go)
- Fetcher: `src/services/go/fetcher/` (main.go, common.go, fetch_readme.go, fetch_languages.go, fetch_topics.go, common_test.go)

## Confirmed fixes (as of feat/test-strategy branch)

- Fetcher top-level context timeout: `fetcher/main.go:50` — 30-minute timeout in place
- SQL injection mitigation: `fetcher/common.go:98-117` — allowlist `validTargetTables` guards table name interpolation
- Partial body on status 200: `fetcher/common.go:222-226` — returns error only, no partial body
- README body size limit: `fetch_readme.go:40` — `io.LimitReader(resp.Body, 10*1024*1024)`
- Scraper proactive rate limiting: `scraper/common.go` — `searchRateLimiter.wait()` + `update()` on every request
- `dbCancel` scoping: scraper now scopes cancel inside batch block correctly

## Open issues (do not re-report as new)

1. **Unlock-sleep-relock race** — both `fetcher/common.go:29-38` and `scraper/common.go:28-38` still use the pattern. Medium severity, latent, fires under full concurrency with remaining==1.
2. **`br.Close()` error discarded** — `scraper/main.go:117`. Fetcher files check it correctly.
3. **`FetchReadmes` count inflation** — `fetch_readme.go:141` adds `len(batch)` but empty-content items are skipped in the DB queue. Languages/topics are unaffected (always write).
4. **`retryRequest` sleeps ignore context** — `fetcher/common.go:213,240,244` use bare `time.Sleep`. Fix: `select { case <-time.After(dur): case <-ctx.Done(): return nil, ctx.Err() }`.
5. **Scan errors silently dropped** — `fetcher/common.go:132,167`. Should log at WARN level.

## Patterns confirmed in this codebase

- `pgx.Batch` + `SendBatch` + iterate `br.Exec()` N times + check `br.Close()` — fetcher does this correctly; scraper discards `br.Close()` error
- `io.LimitReader` on raw README content; not needed on JSON API endpoints (GitHub enforces size)
- Rate limiters: `wait()` before request, `update(resp)` after regardless of status code
- Worker pool pattern: buffered `sem` channel + `wg.Wait()` in goroutine to close results channel
- Context propagation: all fetch functions take `ctx context.Context` as first arg
- No mock tests — tests cover pure functions only (env parsing, URL parsing, UTF-8 truncation, header parsing)
