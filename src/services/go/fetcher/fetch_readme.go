package main

import (
	"context"
	"fmt"
	"io"
	"log"
	"net/http"
	"sync"

	"github.com/jackc/pgx/v5"
)

// fetchReadmeContent fetches the raw README for a given owner/repo using rate limiting and retry.
func (f *GitHubFetcher) fetchReadmeContent(ctx context.Context, owner, repo string) (string, error) {
	reqURL := fmt.Sprintf("https://api.github.com/repos/%s/%s/readme", owner, repo)

	for attempt := 1; attempt <= 2; attempt++ {
		f.rl.wait()

		req, err := http.NewRequestWithContext(ctx, "GET", reqURL, nil)
		if err != nil {
			return "", fmt.Errorf("creating request: %w", err)
		}
		req.Header.Set("Accept", "application/vnd.github.raw")
		req.Header.Set("User-Agent", "ost-linker-fetcher")
		if f.githubToken != "" {
			req.Header.Set("Authorization", "token "+f.githubToken)
		}

		resp, err := f.client.Do(req)
		if err != nil {
			if attempt < 2 {
				continue
			}
			return "", err
		}
		f.rl.update(resp)

		body, readErr := io.ReadAll(io.LimitReader(resp.Body, 10*1024*1024))
		resp.Body.Close()

		if resp.StatusCode == 200 {
			if readErr != nil {
				return "", readErr
			}
			return string(body), nil
		}
		if resp.StatusCode == 404 || resp.StatusCode == 422 {
			return "", nil
		}
		if attempt < 2 {
			continue
		}
		return "", fmt.Errorf("readme fetch status %d", resp.StatusCode)
	}
	return "", nil
}

func (f *GitHubFetcher) FetchReadmes(ctx context.Context, limit int) (int, error) {
	projects, err := f.getNewProjects(ctx, limit, "readme")
	if err != nil {
		return 0, err
	}

	type result struct {
		ProjectID string
		RepoURL   string
		Content   string
	}

	results := make(chan result, f.maxWorkers*2)
	sem := make(chan struct{}, f.maxWorkers)
	var wg sync.WaitGroup

	for _, p := range projects {
		wg.Add(1)
		go func(p Project) {
			defer wg.Done()
			sem <- struct{}{}
			defer func() { <-sem }()

			content, err := f.fetchReadmeContent(ctx, p.Owner, p.Repo)
			if err != nil {
				log.Printf("[WARN] Failed to fetch readme for %s/%s: %v", p.Owner, p.Repo, err)
			}

			content = truncateUTF8(content, 50000)

			results <- result{ProjectID: p.ID, RepoURL: p.RepoURL, Content: content}
		}(p)
	}

	go func() {
		wg.Wait()
		close(results)
	}()

	count := 0
	batchSize := 100
	var batch []result

	flushBatch := func() error {
		if len(batch) == 0 {
			return nil
		}

		pgBatch := &pgx.Batch{}
		queued := 0
		for _, r := range batch {
			if r.Content == "" {
				continue
			}

			pgBatch.Queue(`
				INSERT INTO github.raw_github_readme (id, project_id, repo_url, content, created_at)
				VALUES (gen_random_uuid(), $1, $2, $3, NOW())
				ON CONFLICT (project_id) DO UPDATE
				SET repo_url = EXCLUDED.repo_url,
				    content = EXCLUDED.content,
				    created_at = NOW()
			`, r.ProjectID, r.RepoURL, r.Content)
			queued++
		}

		if queued == 0 {
			batch = nil
			return nil
		}

		br := f.db.SendBatch(ctx, pgBatch)
		for i := 0; i < queued; i++ {
			if _, err := br.Exec(); err != nil {
				log.Printf("[ERROR] Readme batch item %d failed: %v", i, err)
			}
		}
		if err := br.Close(); err != nil {
			return err
		}

		count += len(batch)
		batch = nil
		return nil
	}

	for res := range results {
		batch = append(batch, res)
		if len(batch) >= batchSize {
			if err := flushBatch(); err != nil {
				log.Printf("Error flushing batch: %v", err)
			}
		}
	}
	if err := flushBatch(); err != nil {
		log.Printf("Error flushing final batch: %v", err)
	}

	return count, nil
}
