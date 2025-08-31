package main

import (
	"context"
	"fmt"
	"log"
	"strings"
	"sync"
	"time"
	"unicode/utf8"

	"github.com/google/go-github/v57/github"
	"golang.org/x/oauth2"
)

// GitHubScraper handles GitHub API interactions with optimized performance
type GitHubScraper struct {
	client *github.Client
	ctx    context.Context
}

// NewGitHubScraper creates a new GitHub scraper instance with authentication
func NewGitHubScraper(token string) *GitHubScraper {
	ctx := context.Background()
	var client *github.Client

	if token != "" && token != "your_github_token_here" { // nolint:gosec // test token placeholder
		// Use authenticated client with optimized settings
		ts := oauth2.StaticTokenSource(
			&oauth2.Token{AccessToken: token},
		)
		tc := oauth2.NewClient(ctx, ts)
		client = github.NewClient(tc)
		log.Println("✅ Using authenticated GitHub client")
	} else {
		// Use unauthenticated client (limited rate)
		client = github.NewClient(nil)
		log.Println("⚠️ Using unauthenticated GitHub client (limited rate)")
	}

	return &GitHubScraper{
		client: client,
		ctx:    ctx,
	}
}

// ScrapeRepositories scrapes repositories based on the query with optimized performance
func (s *GitHubScraper) ScrapeRepositories(query string, maxRepos int) ([]Repository, error) {
	startTime := time.Now()
	log.Printf("🚀 Starting GitHub scraping with query: '%s'", query)
	log.Printf("📊 Target: %d repositories", maxRepos)

	// Pre-allocate slice with capacity for better memory efficiency
	repositories := make([]Repository, 0, maxRepos)

	// Use worker pool for parallel processing
	const maxWorkers = 5
	semaphore := make(chan struct{}, maxWorkers)
	var wg sync.WaitGroup
	var mu sync.Mutex

	// Pagination to get all repositories
	page := 1
	perPage := 100 // GitHub API maximum per page
	totalProcessed := 0

	for totalProcessed < maxRepos {
		opts := &github.SearchOptions{
			Sort:  "stars",
			Order: "desc",
			ListOptions: github.ListOptions{
				Page:    page,
				PerPage: perPage,
			},
		}

		// Search repositories with timeout context
		ctx, cancel := context.WithTimeout(s.ctx, 5*time.Minute)
		searchResult, resp, err := s.client.Search.Repositories(ctx, query, opts)
		cancel()

		if err != nil {
			return nil, fmt.Errorf("search repositories failed on page %d: %v", page, err)
		}

		// Log rate limit information
		if resp != nil {
			log.Printf("📈 Rate limit: %d/%d remaining", resp.Rate.Remaining, resp.Rate.Limit)
		}

		// Check if we have repositories to process
		if len(searchResult.Repositories) == 0 {
			log.Printf("📄 No more repositories found on page %d", page)
			break
		}

		log.Printf("📄 Page %d: Found %d repositories, processing...", page, len(searchResult.Repositories))

		// Process repositories from this page
		for _, repo := range searchResult.Repositories {
			if totalProcessed >= maxRepos {
				log.Printf("✅ Reached maximum repositories limit (%d)", maxRepos)
				break
			}

			totalProcessed++
			log.Printf("📦 [%d/%d] Processing: %s ⭐%d", totalProcessed, maxRepos, *repo.FullName, *repo.StargazersCount)

			wg.Add(1)
			go func(repo *github.Repository, index int) {
				defer wg.Done()

				// Acquire semaphore for rate limiting
				semaphore <- struct{}{}
				defer func() { <-semaphore }()

				log.Printf("   🚀 Starting enrichment for %s", *repo.FullName)

				// Get additional data for each repository
				repository, err := s.enrichRepository(repo)
				if err != nil {
					log.Printf("⚠️ Failed to enrich repository %s: %v", *repo.FullName, err)
					// Continue with basic data
					repository = s.basicRepository(repo)
					log.Printf("   📋 Using basic data for %s", *repo.FullName)
				}

				// Thread-safe append
				mu.Lock()
				repositories = append(repositories, repository)
				mu.Unlock()

				log.Printf("   ✅ Successfully scraped: %s (%s) - %d topics, %d languages",
					*repo.FullName, *repo.Language, len(repository.Topics), len(repository.LanguagesMap))
			}(repo, totalProcessed-1)
		}

		// Move to next page
		page++

		// Small delay between pages to be respectful
		time.Sleep(100 * time.Millisecond)
	}

	// Wait for all goroutines to complete
	wg.Wait()

	log.Printf("🎉 GitHub scraping completed successfully!")
	log.Printf("📊 Total repositories scraped: %d", len(repositories))
	log.Printf("⏱️ Processing time: %v", time.Since(startTime))

	// Log summary statistics
	if len(repositories) > 0 {
		s.logSummary(repositories)
	}

	return repositories, nil
}

// enrichRepository gets additional data for a repository with error handling
func (s *GitHubScraper) enrichRepository(repo *github.Repository) (Repository, error) {
	repository := s.basicRepository(repo)

	// Use context with timeout for API calls
	ctx, cancel := context.WithTimeout(s.ctx, 30*time.Second)
	defer cancel()

	// Get topics with error handling
	log.Printf("   🔍 Fetching topics for %s...", *repo.FullName)
	topics, _, err := s.client.Repositories.ListAllTopics(ctx, *repo.Owner.Login, *repo.Name)
	if err == nil {
		// Sanitize topics
		sanitizedTopics := make([]string, 0, len(topics))
		for _, topic := range topics {
			sanitizedTopics = append(sanitizedTopics, sanitizeUTF8(topic))
		}
		repository.Topics = sanitizedTopics
		if len(sanitizedTopics) > 0 {
			log.Printf("   📂 Topics: %s", strings.Join(sanitizedTopics[:minInt(len(sanitizedTopics), 3)], ", "))
			if len(sanitizedTopics) > 3 {
				log.Printf("   ... and %d more topics", len(sanitizedTopics)-3)
			}
		} else {
			log.Printf("   📂 No topics found")
		}
	} else {
		log.Printf("   ⚠️ Failed to get topics: %v", err)
	}

	// Get languages with error handling
	log.Printf("   🔍 Fetching languages for %s...", *repo.FullName)
	languages, _, err := s.client.Repositories.ListLanguages(ctx, *repo.Owner.Login, *repo.Name)
	if err == nil {
		repository.LanguagesMap = languages
		// Get top 3 languages efficiently
		topLanguages := make([]string, 0, 3)
		for lang := range languages {
			if len(topLanguages) < 3 {
				topLanguages = append(topLanguages, lang)
			}
		}
		if len(topLanguages) > 0 {
			log.Printf("   🔧 Languages: %s", strings.Join(topLanguages, ", "))
		} else {
			log.Printf("   🔧 No languages detected")
		}
	} else {
		log.Printf("   ⚠️ Failed to get languages: %v", err)
	}

	// Get README with error handling
	log.Printf("   🔍 Fetching README for %s...", *repo.FullName)
	readme, _, err := s.client.Repositories.GetReadme(ctx, *repo.Owner.Login, *repo.Name, &github.RepositoryContentGetOptions{})
	if err == nil {
		content, err := readme.GetContent()
		if err == nil {
			// Sanitize and limit README size for memory efficiency
			sanitizedContent := sanitizeUTF8(content)
			if len(sanitizedContent) > 10000 {
				sanitizedContent = sanitizedContent[:10000] + "... (truncated)"
				log.Printf("   📖 README: %d chars (truncated to 10k)", len(sanitizedContent))
			} else {
				log.Printf("   📖 README: %d chars", len(sanitizedContent))
			}
			repository.Readme = sanitizedContent
		} else {
			log.Printf("   ⚠️ Failed to decode README content: %v", err)
		}
	} else {
		log.Printf("   📖 No README found or failed to fetch: %v", err)
	}

	return repository, nil
}

// basicRepository creates a basic repository from GitHub API response
func (s *GitHubScraper) basicRepository(repo *github.Repository) Repository {
	// Safe owner access
	owner := ""
	if repo.Owner != nil {
		owner = sanitizeText(repo.Owner.Login)
	}

	// Safe license access
	license := ""
	if repo.License != nil {
		license = sanitizeText(repo.License.SPDXID)
	}

	// Safe homepage access
	homepage := sanitizeText(repo.Homepage)

	// Safe boolean access with defaults
	fork := false
	if repo.Fork != nil {
		fork = *repo.Fork
	}

	archived := false
	if repo.Archived != nil {
		archived = *repo.Archived
	}

	disabled := false
	if repo.Disabled != nil {
		disabled = *repo.Disabled
	}

	// Safe integer access with defaults
	stargazersCount := 0
	if repo.StargazersCount != nil {
		stargazersCount = *repo.StargazersCount
	}

	watchersCount := 0
	if repo.WatchersCount != nil {
		watchersCount = *repo.WatchersCount
	}

	forksCount := 0
	if repo.ForksCount != nil {
		forksCount = *repo.ForksCount
	}

	openIssuesCount := 0
	if repo.OpenIssuesCount != nil {
		openIssuesCount = *repo.OpenIssuesCount
	}

	return Repository{
		FullName:        sanitizeText(repo.FullName),
		Name:            sanitizeText(repo.Name),
		Owner:           owner,
		Description:     sanitizeText(repo.Description),
		Fork:            fork,
		Language:        sanitizeText(repo.Language),
		StargazersCount: stargazersCount,
		WatchersCount:   watchersCount,
		ForksCount:      forksCount,
		OpenIssuesCount: openIssuesCount,
		Topics:          []string{},
		Archived:        archived,
		Disabled:        disabled,
		CreatedAt:       repo.CreatedAt.Time,
		UpdatedAt:       repo.UpdatedAt.Time,
		PushedAt:        repo.PushedAt.Time,
		Homepage:        homepage,
		License:         license,
		LanguagesMap:    make(map[string]int),
		Readme:          "",
	}
}

// logSummary logs summary statistics with performance metrics
func (s *GitHubScraper) logSummary(repositories []Repository) {
	// Language distribution with efficient counting
	languageCounts := make(map[string]int)
	for i := range repositories {
		repo := &repositories[i]
		if repo.Language != "" {
			languageCounts[repo.Language]++
		}
	}

	log.Printf("🔤 Languages distribution:")
	for lang, count := range languageCounts {
		log.Printf("   %s: %d", lang, count)
	}

	// Total stars calculation
	totalStars := 0
	for i := range repositories {
		repo := &repositories[i]
		totalStars += repo.StargazersCount
	}
	avgStars := totalStars / len(repositories)
	log.Printf("⭐ Total stars: %d | Average: %d per repo", totalStars, avgStars)

	// Most starred repository
	if len(repositories) > 0 {
		log.Printf("🔝 Most starred: %s (%d ⭐)", repositories[0].FullName, repositories[0].StargazersCount)
	}
}

// minInt returns the minimum of two integers (optimized)
func minInt(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// sanitizeUTF8 removes invalid UTF-8 sequences and replaces them with replacement characters
func sanitizeUTF8(s string) string {
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

// sanitizeText safely sanitizes text fields for database insertion
func sanitizeText(s *string) string {
	if s == nil {
		return ""
	}
	return sanitizeUTF8(*s)
}
