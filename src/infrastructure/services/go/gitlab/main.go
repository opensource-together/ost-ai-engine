package main

import (
    "encoding/json"
    "log"
    "os"
    "gopkg.in/yaml.v3"
    "io/ioutil"
    "github.com/joho/godotenv"
    "github.com/xanzy/go-gitlab"
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
        DatabaseURL                string `yaml:"DATABASE_URL"`
        GitHubAccessToken          string `yaml:"GITHUB_ACCESS_TOKEN"`
        GitLabAccessToken          string `yaml:"GITLAB_ACCESS_TOKEN"`
        GitLabScrapingQuery        string `yaml:"GITLAB_SCRAPING_QUERY"`
        GitLabTopN                 int    `yaml:"GITLAB_TOP_N"`
        GitLabApiUrl               string `yaml:"GITLAB_API_URL"`
        GitLabProjectsVisibility   string `yaml:"GITLAB_PROJECTS_VISIBILITY"`
        GitLabProjectsArchived     string `yaml:"GITLAB_PROJECTS_ARCHIVED"`
        GitLabProjectsOrderBy      string `yaml:"GITLAB_PROJECTS_ORDER_BY"`
        GitLabProjectsSort         string `yaml:"GITLAB_PROJECTS_SORT"`
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
    var git *gitlab.Client
    if config.GitLabApiUrl != "" {
        git, err = gitlab.NewClient(token, gitlab.WithBaseURL(config.GitLabApiUrl))
    } else {
        git, err = gitlab.NewClient(token)
    }
    if err != nil {
        log.Fatalf("Failed to create GitLab client: %v", err)
    }

    // Prepare search options from config
    opt := &gitlab.ListProjectsOptions{
        Visibility: gitlab.Visibility(config.GitLabProjectsVisibility),
        OrderBy:    gitlab.String(config.GitLabProjectsOrderBy),
        Sort:       gitlab.String(config.GitLabProjectsSort),
        ListOptions: gitlab.ListOptions{
            Page:    1,
            PerPage: 100,
        },
    }
    // Handle archived (string to bool)
    if config.GitLabProjectsArchived == "true" {
        opt.Archived = gitlab.Bool(true)
    } else {
        opt.Archived = gitlab.Bool(false)
    }
    // If a search query is provided
    if config.GitLabScrapingQuery != "" && config.GitLabScrapingQuery != "default" {
        opt.Search = gitlab.String(config.GitLabScrapingQuery)
    }

    var allProjects []*gitlab.Project
    collected := 0
    for collected < maxProjects {
        projects, resp, err := git.Projects.ListProjects(opt)
        if err != nil {
            log.Fatalf("GitLab API error: %v", err)
        }
        if len(projects) == 0 {
            break
        }
        allProjects = append(allProjects, projects...)
        collected += len(projects)
        if resp.NextPage == 0 {
            break
        }
        opt.Page = resp.NextPage
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
