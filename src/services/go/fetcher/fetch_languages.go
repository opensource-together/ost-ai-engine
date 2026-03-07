package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sync"

	"github.com/jackc/pgx/v5"
)

func (f *GitHubFetcher) FetchLanguages(ctx context.Context, limit int) (int, error) {
	projects, err := f.getNewProjects(ctx, limit, "languages")
	if err != nil {
		return 0, err
	}

	type result struct {
		ProjectID string
		RepoURL   string
		Languages map[string]int
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

			url := fmt.Sprintf("https://api.github.com/repos/%s/%s/languages", p.Owner, p.Repo)
			body, err := f.retryRequest(ctx, url, 2)

			var langs map[string]int
			if err == nil {
				if unmarshalErr := json.Unmarshal(body, &langs); unmarshalErr != nil {
					log.Printf("[WARN] Failed to unmarshal languages for %s/%s: %v", p.Owner, p.Repo, unmarshalErr)
				}
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
			jsonLangs, err := json.Marshal(r.Languages)
			if err != nil {
				log.Printf("[WARN] Failed to marshal languages for project %s: %v", r.ProjectID, err)
				continue
			}
			pgBatch.Queue(`
				INSERT INTO github.raw_github_languages (id, project_id, repo_url, languages, created_at)
				VALUES (gen_random_uuid(), $1, $2, $3, NOW())
				ON CONFLICT (project_id) DO UPDATE
				SET repo_url = EXCLUDED.repo_url,
				    languages = EXCLUDED.languages,
				    created_at = NOW()
			`, r.ProjectID, r.RepoURL, string(jsonLangs))
		}

		if pgBatch.Len() == 0 {
			batch = nil
			return nil
		}

		br := f.db.SendBatch(ctx, pgBatch)
		for i := 0; i < pgBatch.Len(); i++ {
			if _, err := br.Exec(); err != nil {
				log.Printf("[ERROR] Languages batch item %d failed: %v", i, err)
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
