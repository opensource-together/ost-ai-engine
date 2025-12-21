package main

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"

	"github.com/jackc/pgx/v5"
)

func (f *GitHubFetcher) FetchTopics(ctx context.Context, limit int) (int, error) {
	projects, err := f.getProjects(ctx, limit)
	if err != nil {
		return 0, err
	}

	type result struct {
		ProjectID string
		RepoURL   string
		Topics    []string
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

			url := fmt.Sprintf("https://api.github.com/repos/%s/%s/topics", p.Owner, p.Repo)
			body, err := f.makeRequest(url)

			var resp struct {
				Names []string `json:"names"`
			}
			if err == nil {
				_ = json.Unmarshal(body, &resp)
			}
			if resp.Names == nil {
				resp.Names = []string{}
			}
			results <- result{ProjectID: p.ID, RepoURL: p.RepoURL, Topics: resp.Names}
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
			jsonTopics, _ := json.Marshal(r.Topics)
			pgBatch.Queue(`DELETE FROM github.raw_github_topics WHERE project_id = $1`, r.ProjectID)
			pgBatch.Queue(`
				INSERT INTO github.raw_github_topics (id, project_id, repo_url, topics, created_at)
				VALUES (gen_random_uuid(), $1, $2, $3, NOW())
			`, r.ProjectID, r.RepoURL, string(jsonTopics))
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
			_ = flushBatch()
		}
	}
	_ = flushBatch()

	return count, nil
}
