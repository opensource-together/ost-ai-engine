package main

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"

	"github.com/jackc/pgx/v5"
)

func (f *GitHubFetcher) FetchLanguages(ctx context.Context, limit int) (int, error) {
	projects, err := f.getProjects(ctx, limit)
	if err != nil {
		return 0, err
	}

	type result struct {
		ProjectID string
		RepoURL   string
		Languages map[string]int
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

			url := fmt.Sprintf("https://api.github.com/repos/%s/%s/languages", p.Owner, p.Repo)
			body, err := f.makeRequest(url)

			var langs map[string]int
			if err == nil {
				_ = json.Unmarshal(body, &langs)
			}
			if langs == nil {
				langs = make(map[string]int)
			}
			results <- result{ProjectID: p.ID, RepoURL: p.RepoURL, Languages: langs}
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
			jsonLangs, _ := json.Marshal(r.Languages)
			pgBatch.Queue(`DELETE FROM github.raw_github_languages WHERE project_id = $1`, r.ProjectID)
			pgBatch.Queue(`
				INSERT INTO github.raw_github_languages (id, project_id, repo_url, languages, created_at)
				VALUES (gen_random_uuid(), $1, $2, $3, NOW())
			`, r.ProjectID, r.RepoURL, string(jsonLangs))
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
