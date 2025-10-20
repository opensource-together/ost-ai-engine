package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"time"

	"github.com/joho/godotenv"
	"gopkg.in/yaml.v3"
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
		Login     string  `json:"login"`
		AvatarURL *string `json:"avatar_url"`
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

func fetchGitHubRepos(client *http.Client, token string, apiURL string, query string, perPage, page int) (githubSearchResponse, error) {
	var result githubSearchResponse
	if apiURL == "" {
		return result, fmt.Errorf("GITHUB_API_URL is required but not set")
	}
	base, err := url.Parse(apiURL)
	if err != nil {
		return result, fmt.Errorf("invalid github api url: %v", err)
	}
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
	_ = godotenv.Load(".env")

	configPath := os.Getenv("OST_CONFIG_PATH")

	// Load configuration from YAML file
	configBytes, err := ioutil.ReadFile(configPath)
	if err != nil {
		log.Fatalf("[ERROR] Config file could not be read: %v", err)
	}
	var config struct {
		DatabaseURL         string `yaml:"DATABASE_URL"`
		GitHubAccessToken   string `yaml:"GITHUB_ACCESS_TOKEN"`
		GitLabAccessToken   string `yaml:"GITLAB_ACCESS_TOKEN"`
		GitHubScrapingQuery string `yaml:"GITHUB_SCRAPING_QUERY"`
		GitHubTopN          int    `yaml:"GITHUB_TOP_N"`
		GitHubApiUrl        string `yaml:"GITHUB_API_URL"`
	}
	if err := yaml.Unmarshal(configBytes, &config); err != nil {
		log.Fatalf("[ERROR] Config file could not be parsed: %v", err)
	}

	log.Println("[INFO] Loaded config from config/config.yaml.")
	log.Printf("[INFO] Query: %s", config.GitHubScrapingQuery)

	token := config.GitHubAccessToken
	if token == "" {
		log.Println("warning: GITHUB_ACCESS_TOKEN not set; may hit rate limits")
	}
	query := config.GitHubScrapingQuery
	if query == "" {
		log.Fatal("GITHUB_SCRAPING_QUERY is required")
	}
	apiURL := config.GitHubApiUrl
	if apiURL == "" {
		log.Fatal("GITHUB_API_URL is required in config")
	}
	maxRepos := config.GitHubTopN
	if maxRepos <= 0 {
		maxRepos = 1000
	}

	client := newHTTPClient()
	perPage := 100
	collected := 0
	var allRepos []githubRepo
	for page := 1; collected < maxRepos; page++ {
		res, err := fetchGitHubRepos(client, token, apiURL, query, perPage, page)
		if err != nil {
			log.Fatalf("github fetch: %v", err)
		}
		if len(res.Items) == 0 {
			break
		}
		allRepos = append(allRepos, res.Items...)
		collected += len(res.Items)
	}

	// Display results as JSON
	if err := json.NewEncoder(os.Stdout).Encode(allRepos); err != nil {
		log.Fatalf("json encode: %v", err)
	}
}
