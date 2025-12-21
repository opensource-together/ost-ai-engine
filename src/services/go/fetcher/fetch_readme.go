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

func (f *GitHubFetcher) FetchReadmes(ctx context.Context, limit int) (int, error) {
	projects, err := f.getProjects(ctx, limit)
	if err != nil {
		return 0, err
	}

	type result struct {
		ProjectID string
		RepoURL   string
		Content   string
	}

	results := make(chan result, len(projects))
	sem := make(chan struct{}, f.maxWorkers)
	var wg sync.WaitGroup

	for _, p := range projects {
		wg.Add(1)
		go func(p Project) {
			defer wg.Done()
			sem <- struct{}{}
			defer func() { <-sem }()

			url := fmt.Sprintf("https://api.github.com/repos/%s/%s/readme", p.Owner, p.Repo)

			req, _ := http.NewRequest("GET", url, nil)
			req.Header.Set("Accept", "application/vnd.github.raw")
			if f.githubToken != "" {
				req.Header.Set("Authorization", "token "+f.githubToken)
			}

			resp, err := f.client.Do(req)
			var content string
			if err == nil {
				defer resp.Body.Close()
				if resp.StatusCode == 200 {
					b, _ := io.ReadAll(resp.Body)
					content = string(b)
				}
			}

			if len(content) > 50000 {
				content = content[:50000]
			}

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
		for _, r := range batch {
			if r.Content == "" {
				continue
			}

			pgBatch.Queue(`DELETE FROM github.raw_github_readme WHERE project_id = $1`, r.ProjectID)
			pgBatch.Queue(`
				INSERT INTO github.raw_github_readme (id, project_id, repo_url, content, created_at)
				VALUES (gen_random_uuid(), $1, $2, $3, NOW())
			`, r.ProjectID, r.RepoURL, r.Content)
		}

		br := f.db.SendBatch(ctx, pgBatch)
		defer br.Close()
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
