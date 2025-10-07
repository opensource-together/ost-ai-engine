package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"time"

	"github.com/joho/godotenv"
)

type gitlabProject struct {
	ID          int64   `json:"id"`
	Name        string  `json:"name"`
	PathWithNS  string  `json:"path_with_namespace"`
	WebURL      string  `json:"web_url"`
	Description *string `json:"description"`
	StarCount   int     `json:"star_count"`
	ForksCount  int     `json:"forks_count"`
	DefaultBr   *string `json:"default_branch"`
	Visibility  *string `json:"visibility"`
	CreatedAt   string  `json:"created_at"`
	LastActAt   string  `json:"last_activity_at"`
}

func newHTTPClient() *http.Client {
	return &http.Client{Timeout: 30 * time.Second}
}

func fetchGitLabProjects(client *http.Client, token string, perPage, page int) ([]gitlabProject, error) {
	var projects []gitlabProject
	base, _ := url.Parse("https://gitlab.com/api/v4/projects")
	q := base.Query()
	q.Set("visibility", "public")
	q.Set("sort", "desc")
	q.Set("per_page", strconv.Itoa(perPage))
	q.Set("page", strconv.Itoa(page))
	base.RawQuery = q.Encode()

	req, _ := http.NewRequest("GET", base.String(), nil)
	req.Header.Set("User-Agent", "ost-ai-engine-scraper")
	if token != "" {
		req.Header.Set("PRIVATE-TOKEN", token)
	}
	resp, err := client.Do(req)
	if err != nil {
		return projects, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return projects, fmt.Errorf("gitlab api status %d", resp.StatusCode)
	}
	if err := json.NewDecoder(resp.Body).Decode(&projects); err != nil {
		return projects, err
	}
	return projects, nil
}

func main() {
	_ = godotenv.Load()
	token := os.Getenv("GITLAB_ACCESS_TOKEN")
	if token == "" {
		log.Println("warning: GITLAB_ACCESS_TOKEN not set; may hit rate limits")
	}
	maxProjects := 1000
	if v := os.Getenv("GITLAB_MAX_PROJECTS"); v != "" {
		if n, err := strconv.Atoi(v); err == nil && n > 0 {
			maxProjects = n
		}
	}

	client := newHTTPClient()
	perPage := 20
	collected := 0
	allProjects := []gitlabProject{}
	for page := 1; collected < maxProjects; page++ {
		items, err := fetchGitLabProjects(client, token, perPage, page)
		if err != nil {
			log.Fatalf("gitlab fetch: %v", err)
		}
		if len(items) == 0 {
			break
		}
		allProjects = append(allProjects, items...)
		collected += len(items)
	}

	// Print all projects as JSON to stdout
	if err := json.NewEncoder(os.Stdout).Encode(allProjects); err != nil {
		log.Fatalf("json encode: %v", err)
	}
		}
		for _, p := range items {
			ns := p.PathWithNS
			if err := upsertTrendingProject(ctx, conn, trendingProject{
				Platform:               "GITLAB",
				ExternalID:             fmt.Sprintf("%d", p.ID),
				Name:                   p.Name,
				FullName:               p.PathWithNS,
				Description:            p.Description,
				HTMLURL:                p.WebURL,
				Homepage:               nil,
				DefaultBranch:          p.DefaultBr,
				Visibility:             p.Visibility,
				Language:               nil,
				TopicsJSON:             nil,
				License:                nil,
				Stars:                  p.StarCount,
				Forks:                  p.ForksCount,
				OpenIssues:             nil,
				Subscribers:            nil,
				Archived:               false,
				Owner:                  nil,
				Namespace:              &ns,
				CreatedAtSourceRFC3339: &p.CreatedAt,
				UpdatedAtSourceRFC3339: nil,
				LastActivityAtRFC3339:  &p.LastActAt,
			}); err != nil {
				log.Printf("upsert error id=%d: %v", p.ID, err)
			} else {
				log.Printf("upsert ok id=%d", p.ID)
			}
			collected++
			if collected%10 == 0 {
				log.Printf("gitlab progress: collected=%d/%d (page=%d, batch=%d)", collected, maxProjects, page, len(items))
			}
			if collected >= maxProjects {
				break
			}
		}
		log.Printf("gitlab page %d done, page_count=%d, total=%d", page, len(items), collected)
	}
	log.Printf("gitlab collected %d projects\n", collected)
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
