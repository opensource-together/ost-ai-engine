var envPath = "../../../../../.env.local"
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
	_ = godotenv.Load(envPath)
	log.Println("[INFO] Loaded environment variables.")
	log.Printf("[INFO] Query: %s", os.Getenv("GITHUB_SCRAPING_QUERY"))
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
	var allRepos []githubRepo
	for page := 1; collected < maxRepos; page++ {
		res, err := fetchGitHubRepos(client, token, query, perPage, page)
		if err != nil {
			log.Fatalf("github fetch: %v", err)
		}
		if len(res.Items) == 0 {
			break
		}
		allRepos = append(allRepos, res.Items...)
		collected += len(res.Items)
	}

	// Affiche la liste des projets scrapés en JSON sur stdout
	if err := json.NewEncoder(os.Stdout).Encode(allRepos); err != nil {
		log.Fatalf("json encode: %v", err)
	}
}

