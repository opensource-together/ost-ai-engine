package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"time"

	"strings"
	"unicode/utf8"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// cleanUTF8 removes invalid UTF-8 sequences for database insertion
func cleanUTF8(s string) string {
	if utf8.ValidString(s) {
		return s
	}

	// Replace invalid UTF-8 sequences with replacement character
	var result strings.Builder
	for i := 0; i < len(s); {
		r, size := utf8.DecodeRuneInString(s[i:])
		if r == utf8.RuneError {
			result.WriteRune('\uFFFD') // Replacement character
			i++
		} else {
			result.WriteRune(r)
			i += size
		}
	}
	return result.String()
}

func upsertRepositories(dbURL string, repos []Repository) error {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()

	pool, err := pgxpool.New(ctx, dbURL)
	if err != nil {
		return fmt.Errorf("connect db: %w", err)
	}
	defer pool.Close()

	tx, err := pool.Begin(ctx)
	if err != nil {
		return fmt.Errorf("begin tx: %w", err)
	}
	defer func() {
		if err != nil {
			_ = tx.Rollback(ctx)
		} else {
			_ = tx.Commit(ctx)
		}
	}()

	stmt := `
	INSERT INTO "github_PROJECT" (
		full_name, name, owner, description, fork, language,
		stargazers_count, watchers_count, forks_count, open_issues_count,
		topics, archived, disabled, created_at, updated_at, pushed_at,
		homepage, license, languages_map, readme, raw, last_ingested_at
	) VALUES (
		$1, $2, $3, $4, $5, $6,
		$7, $8, $9, $10,
		$11, $12, $13, $14, $15, $16,
		$17, $18, CAST($19 AS JSONB), $20, CAST($21 AS JSONB), NOW()
	) ON CONFLICT (full_name) DO UPDATE SET
		name = EXCLUDED.name,
		owner = EXCLUDED.owner,
		description = EXCLUDED.description,
		fork = EXCLUDED.fork,
		language = EXCLUDED.language,
		stargazers_count = EXCLUDED.stargazers_count,
		watchers_count = EXCLUDED.watchers_count,
		forks_count = EXCLUDED.forks_count,
		open_issues_count = EXCLUDED.open_issues_count,
		topics = EXCLUDED.topics,
		archived = EXCLUDED.archived,
		disabled = EXCLUDED.disabled,
		created_at = EXCLUDED.created_at,
		updated_at = EXCLUDED.updated_at,
		pushed_at = EXCLUDED.pushed_at,
		homepage = EXCLUDED.homepage,
		license = EXCLUDED.license,
		languages_map = EXCLUDED.languages_map,
		readme = EXCLUDED.readme,
		raw = EXCLUDED.raw,
		last_ingested_at = NOW()
	`

	batch := &pgx.Batch{}
	for i := range repos {
		r := &repos[i]
		languagesJSON, _ := json.Marshal(r.LanguagesMap)

		// Create a sanitized copy for raw JSON
		sanitizedRepo := Repository{
			FullName:        cleanUTF8(r.FullName),
			Name:            cleanUTF8(r.Name),
			Owner:           cleanUTF8(r.Owner),
			Description:     cleanUTF8(r.Description),
			Fork:            r.Fork,
			Language:        cleanUTF8(r.Language),
			StargazersCount: r.StargazersCount,
			WatchersCount:   r.WatchersCount,
			ForksCount:      r.ForksCount,
			OpenIssuesCount: r.OpenIssuesCount,
			Topics:          r.Topics, // Already sanitized
			Archived:        r.Archived,
			Disabled:        r.Disabled,
			CreatedAt:       r.CreatedAt,
			UpdatedAt:       r.UpdatedAt,
			PushedAt:        r.PushedAt,
			Homepage:        cleanUTF8(r.Homepage),
			License:         cleanUTF8(r.License),
			LanguagesMap:    r.LanguagesMap,
			Readme:          cleanUTF8(r.Readme),
		}
		rawJSON, _ := json.Marshal(sanitizedRepo)

		// Insert sanitized data
		batch.Queue(stmt,
			sanitizedRepo.FullName,
			sanitizedRepo.Name,
			sanitizedRepo.Owner,
			sanitizedRepo.Description,
			sanitizedRepo.Fork,
			sanitizedRepo.Language,
			sanitizedRepo.StargazersCount,
			sanitizedRepo.WatchersCount,
			sanitizedRepo.ForksCount,
			sanitizedRepo.OpenIssuesCount,
			sanitizedRepo.Topics,
			sanitizedRepo.Archived,
			sanitizedRepo.Disabled,
			sanitizedRepo.CreatedAt,
			sanitizedRepo.UpdatedAt,
			sanitizedRepo.PushedAt,
			sanitizedRepo.Homepage,
			sanitizedRepo.License,
			languagesJSON,
			sanitizedRepo.Readme,
			rawJSON,
		)
	}

	br := tx.SendBatch(ctx, batch)
	defer br.Close()
	for i := 0; i < len(repos); i++ {
		if _, err := br.Exec(); err != nil {
			log.Printf("upsert failed on row %d: %v", i, err)
			return err
		}
	}

	return nil
}
