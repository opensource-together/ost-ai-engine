package main

import (
	"encoding/json"
	"io/ioutil"
	"log"
	"os"

	"github.com/joho/godotenv"
	gitlab "gitlab.com/gitlab-org/api/client-go"
	"gopkg.in/yaml.v3"
)

func main() {
	_ = godotenv.Load(".env")

	configPath := os.Getenv("OST_CONFIG_PATH")

	// Load configuration from YAML file
	configBytes, err := ioutil.ReadFile(configPath)
	if err != nil {
		log.Fatalf("[ERROR] Config file could not be read: %v", err)
	}
	var config struct {
		DatabaseURL              string `yaml:"DATABASE_URL"`
		GitHubAccessToken        string `yaml:"GITHUB_ACCESS_TOKEN"`
		GitLabAccessToken        string `yaml:"GITLAB_ACCESS_TOKEN"`
		GitLabScrapingQuery      string `yaml:"GITLAB_SCRAPING_QUERY"`
		GitLabTopN               int    `yaml:"GITLAB_TOP_N"`
		GitLabApiUrl             string `yaml:"GITLAB_API_URL"`
		GitLabProjectsVisibility string `yaml:"GITLAB_PROJECTS_VISIBILITY"`
		GitLabProjectsArchived   string `yaml:"GITLAB_PROJECTS_ARCHIVED"`
		GitLabProjectsOrderBy    string `yaml:"GITLAB_PROJECTS_ORDER_BY"`
		GitLabProjectsSort       string `yaml:"GITLAB_PROJECTS_SORT"`
	}
	if err := yaml.Unmarshal(configBytes, &config); err != nil {
		log.Fatalf("[ERROR] Config file could not be parsed: %v", err)
	}

	log.Println("[INFO] Loaded config from config/config.yaml.")
	log.Printf("[INFO] Query: %s", config.GitLabScrapingQuery)
	token := config.GitLabAccessToken
	if token == "" {
		log.Println("warning: GITLAB_ACCESS_TOKEN not set; may hit rate limits")
	}
	maxProjects := config.GitLabTopN
	if maxProjects <= 0 {
		maxProjects = 1000
	}

	// Initialize GitLab client

	client := gitlab.NewClient(nil, token)
	if config.GitLabApiUrl != "" {
		if err := client.SetBaseURL(config.GitLabApiUrl); err != nil {
			log.Fatalf("Failed to set GitLab API URL: %v", err)
		}
	}

	// Build search options from config

	archived := false
	if config.GitLabProjectsArchived == "true" {
		archived = true
	}

	opt := &gitlab.ListProjectsOptions{
		OrderBy:  config.GitLabProjectsOrderBy,
		Sort:     config.GitLabProjectsSort,
		Search:   config.GitLabScrapingQuery,
		Archived: archived,
		// Add Visibility if supported by the client library
		// Visibility: config.GitLabProjectsVisibility,
	}

	var allProjects []*gitlab.Project
	collected := 0
	page := 1
	for collected < maxProjects {
		opt.Page = page
		projects, resp, err := client.Projects.ListProjects(opt)
		if err != nil {
			log.Fatalf("GitLab API error: %v", err)
		}
		if len(projects) == 0 {
			break
		}
		allProjects = append(allProjects, projects...)
		collected += len(projects)
		if resp == nil || resp.NextPage == 0 {
			break
		}
		page = resp.NextPage
	}

	// Truncate if too many projects
	if len(allProjects) > maxProjects {
		allProjects = allProjects[:maxProjects]
	}

	// Output results as JSON
	if err := json.NewEncoder(os.Stdout).Encode(allProjects); err != nil {
		log.Fatalf("json encode: %v", err)
	}
}
