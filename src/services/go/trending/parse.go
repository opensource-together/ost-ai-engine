package main

import (
	"io"
	"regexp"
	"strconv"
	"strings"

	"github.com/PuerkitoBio/goquery"
)

// trendingRepo holds the essential information parsed from one GitHub Trending row.
type trendingRepo struct {
	Owner      string
	Repo       string
	RepoURL    string
	StarsToday int
}

// reStarsToday matches strings like "134 stars today" or "1,234 stars today".
var reStarsToday = regexp.MustCompile(`([\d,]+)\s+stars today`)

// parseTrendingPage parses the GitHub Trending HTML page and returns one
// trendingRepo entry per repository row. It never returns a non-nil error for
// missing data — rows with a missing owner/repo are silently skipped.
func parseTrendingPage(r io.Reader) ([]trendingRepo, error) {
	doc, err := goquery.NewDocumentFromReader(r)
	if err != nil {
		return nil, err
	}

	var repos []trendingRepo

	doc.Find("article.Box-row").Each(func(_ int, s *goquery.Selection) {
		// The repo link is the first <a> inside the <h2> — its href is "/{owner}/{repo}".
		href, exists := s.Find("h2 a").First().Attr("href")
		if !exists {
			return
		}
		href = strings.TrimSpace(href)
		parts := strings.SplitN(strings.Trim(href, "/"), "/", 3)
		if len(parts) < 2 || parts[0] == "" || parts[1] == "" {
			return
		}
		owner, repo := parts[0], parts[1]
		repoURL := "https://github.com/" + owner + "/" + repo

		// Stars-today live in a span with class "d-inline-block float-sm-right".
		starsToday := 0
		s.Find("span.d-inline-block.float-sm-right").Each(func(_ int, span *goquery.Selection) {
			text := strings.TrimSpace(span.Text())
			if m := reStarsToday.FindStringSubmatch(text); m != nil {
				raw := strings.ReplaceAll(m[1], ",", "")
				if n, err := strconv.Atoi(raw); err == nil {
					starsToday = n
				}
			}
		})

		repos = append(repos, trendingRepo{
			Owner:      owner,
			Repo:       repo,
			RepoURL:    repoURL,
			StarsToday: starsToday,
		})
	})

	return repos, nil
}
