package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strconv"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/joho/godotenv"
)

type githubRepo struct {
	ID          int64   `json:"id"`
	Name        string  `json:"name"`
	FullName    string  `json:"full_name"`
	HTMLURL     string  `json:"html_url"`
	Description *string `json:"description"`
	Stargazers  int     `json:"stargazers_count"`
	Forks       int     `json:"forks_count"`
	Language    *string `json:"language"`
	Homepage    *string `json:"homepage"`
	DefaultBr   *string `json:"default_branch"`
	Private     *bool   `json:"private"`
	Owner       *struct {
		Login string `json:"login"`
	} `json:"owner"`
	CreatedAt string `json:"created_at"`
	UpdatedAt string `json:"updated_at"`
	PushedAt  string `json:"pushed_at"`
}

type githubSearchResponse struct {
	TotalCount int          `json:"total_count"`
	Items      []githubRepo `json:"items"`
}

func newHTTPClient() *http.Client {
	return &http.Client{Timeout: 30 * time.Second}
}

func fetchGitHubRepos(client *http.Client, token string, query string, perPage, page int) (githubSearchResponse, error) {
	var result githubSearchResponse
	base, _ := url.Parse("https://api.github.com/search/repositories")
	q := base.Query()
	q.Set("q", query)
	q.Set("sort", "stars")
	q.Set("order", "desc")
	q.Set("per_page", strconv.Itoa(perPage))
	q.Set("page", strconv.Itoa(page))
	base.RawQuery = q.Encode()

	req, _ := http.NewRequest("GET", base.String(), nil)
	req.Header.Set("Accept", "application/vnd.github+json")
	req.Header.Set("User-Agent", "ost-ai-engine-scraper")
	req.Header.Set("X-GitHub-Api-Version", "2022-11-28")
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}

	resp, err := client.Do(req)
	if err != nil {
		return result, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return result, fmt.Errorf("github api status %d", resp.StatusCode)
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return result, err
	}
	return result, nil
}

func main() {
	// Load .env by walking up from CWD to repo root so direct runs work
	_ = loadDotEnvUpwards()
	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		log.Fatal("DATABASE_URL is required")
	}
	ctx := context.Background()
	conn, err := pgx.Connect(ctx, dbURL)
	if err != nil {
		log.Fatalf("connect: %v", err)
	}
	defer conn.Close(ctx)

	token := os.Getenv("GITHUB_ACCESS_TOKEN")
	if token == "" {
		log.Println("warning: GITHUB_ACCESS_TOKEN not set; may hit rate limits")
	}
	query := os.Getenv("GITHUB_SCRAPING_QUERY")
	if query == "" {
		log.Fatal("GITHUB_SCRAPING_QUERY is required")
	}
	maxRepos := 1000
	if v := os.Getenv("GITHUB_MAX_REPOSITORIES"); v != "" {
		if n, err := strconv.Atoi(v); err == nil && n > 0 {
			maxRepos = n
		}
	}

	client := newHTTPClient()
	perPage := 100
	collected := 0
	for page := 1; collected < maxRepos; page++ {
		res, err := fetchGitHubRepos(client, token, query, perPage, page)
		if err != nil {
			log.Fatalf("github fetch: %v", err)
		}
		if len(res.Items) == 0 {
			break
		}
		for _, r := range res.Items {
			var owner *string
			if r.Owner != nil {
				owner = &r.Owner.Login
			}
			if err := upsertTrendingProject(ctx, conn, trendingProject{
				Platform:               "GITHUB",
				ExternalID:             fmt.Sprintf("%d", r.ID),
				Name:                   r.Name,
				FullName:               r.FullName,
				Description:            r.Description,
				HTMLURL:                r.HTMLURL,
				Homepage:               r.Homepage,
				DefaultBranch:          r.DefaultBr,
				Visibility:             nil,
				Language:               r.Language,
				TopicsJSON:             nil,
				License:                nil,
				Stars:                  r.Stargazers,
				Forks:                  r.Forks,
				OpenIssues:             nil,
				Subscribers:            nil,
				Archived:               false,
				Owner:                  owner,
				Namespace:              owner,
				CreatedAtSourceRFC3339: strPtr(r.CreatedAt),
				UpdatedAtSourceRFC3339: strPtr(r.UpdatedAt),
				LastActivityAtRFC3339:  strPtr(r.PushedAt),
			}); err != nil {
				log.Printf("upsert error id=%d: %v", r.ID, err)
			} else {
				log.Printf("upsert ok id=%d", r.ID)
			}
			collected++
			if collected%10 == 0 {
				log.Printf("github progress: collected=%d/%d (page=%d, batch=%d)", collected, maxRepos, page, len(res.Items))
			}
			if collected >= maxRepos {
				break
			}
		}
		log.Printf("github page %d done, page_count=%d, total=%d", page, len(res.Items), collected)
	}
	log.Printf("github collected %d repos (query=%q)\n", collected, query)
}

type trendingProject struct {
	Platform               string
	ExternalID             string
	Name                   string
	FullName               string
	Description            *string
	HTMLURL                string
	Homepage               *string
	DefaultBranch          *string
	Visibility             *string
	Language               *string
	TopicsJSON             *string
	License                *string
	Stars                  int
	Forks                  int
	OpenIssues             *int
	Subscribers            *int
	Archived               bool
	Owner                  *string
	Namespace              *string
	CreatedAtSourceRFC3339 *string
	UpdatedAtSourceRFC3339 *string
	LastActivityAtRFC3339  *string
}

func upsertTrendingProject(ctx context.Context, conn *pgx.Conn, p trendingProject) error {
	const q = `
INSERT INTO staging.stg_trending_projects (
  platform, external_id, name, full_name, description,
  html_url, homepage, default_branch, visibility,
  language, topics, license,
  stars, forks, open_issues, subscribers, archived,
  owner, namespace,
  created_at_source, updated_at_source, last_activity_at_source,
  _loaded_at
) VALUES (
  $1, $2, $3, $4, $5,
  $6, $7, $8, $9,
  $10, $11::jsonb, $12,
  $13, $14, $15, $16, $17,
  $18, $19,
  COALESCE(to_timestamp($20, 'YYYY-MM-DD"T"HH24:MI:SS"Z"'), NULL),
  COALESCE(to_timestamp($21, 'YYYY-MM-DD"T"HH24:MI:SS"Z"'), NULL),
  COALESCE(to_timestamp($22, 'YYYY-MM-DD"T"HH24:MI:SS"Z"'), NULL),
  NOW()
)
ON CONFLICT (platform, external_id) DO UPDATE SET
  name = EXCLUDED.name,
  full_name = EXCLUDED.full_name,
  description = EXCLUDED.description,
  html_url = EXCLUDED.html_url,
  homepage = EXCLUDED.homepage,
  default_branch = EXCLUDED.default_branch,
  visibility = EXCLUDED.visibility,
  language = EXCLUDED.language,
  topics = EXCLUDED.topics,
  license = EXCLUDED.license,
  stars = EXCLUDED.stars,
  forks = EXCLUDED.forks,
  open_issues = EXCLUDED.open_issues,
  subscribers = EXCLUDED.subscribers,
  archived = EXCLUDED.archived,
  owner = EXCLUDED.owner,
  namespace = EXCLUDED.namespace,
  created_at_source = EXCLUDED.created_at_source,
  updated_at_source = EXCLUDED.updated_at_source,
  last_activity_at_source = EXCLUDED.last_activity_at_source,
  _loaded_at = NOW();
`
	_, err := conn.Exec(ctx, q,
		p.Platform, p.ExternalID, p.Name, p.FullName, p.Description,
		p.HTMLURL, p.Homepage, p.DefaultBranch, p.Visibility,
		p.Language, p.TopicsJSON, p.License,
		p.Stars, p.Forks, p.OpenIssues, p.Subscribers, p.Archived,
		p.Owner, p.Namespace,
		p.CreatedAtSourceRFC3339, p.UpdatedAtSourceRFC3339, p.LastActivityAtRFC3339,
	)
	return err
}

func boolPtrValue(b *bool) bool {
	if b == nil {
		return false
	}
	return *b
}
func strPtr(s string) *string { return &s }

// loadDotEnvUpwards searches current and parent directories for a .env
func loadDotEnvUpwards() error {
	// First try current directory
	if err := godotenv.Load(".env"); err == nil {
		return nil
	}

	// Then walk up directories looking for .env
	dir, err := os.Getwd()
	if err != nil {
		return err
	}

	for i := 0; i < 6; i++ { // up to 6 levels up
		candidate := dir + string(os.PathSeparator) + ".env"
		if _, statErr := os.Stat(candidate); statErr == nil {
			return godotenv.Load(candidate)
		}
		parent := dir + string(os.PathSeparator) + ".."
		abs, err := filepath.Abs(parent)
		if err != nil {
			break
		}
		dir = abs
	}

	// Last resort: try repo root from PROJECT_ROOT env var
	if projectRoot := os.Getenv("PROJECT_ROOT"); projectRoot != "" {
		repoRoot := filepath.Join(projectRoot, ".env")
		if _, statErr := os.Stat(repoRoot); statErr == nil {
			return godotenv.Load(repoRoot)
		}
	}

	return nil
}
