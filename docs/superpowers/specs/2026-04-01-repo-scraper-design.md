# Open Source Repo Scraper Design

## Overview
A scraper service that continuously discovers trending open source GitHub repositories, specialized AI agents, tools, and MCPs from Twitter and Reddit, filtering for quality and relevance, and integrates seamlessly with the AI Orchestrator platform for direct CLI usage.

## Architecture
- **Backend Integration**: Python module in `backend/scraper/`
- **Data Sources**: Twitter (snscrape), Reddit (PRAW)
- **Storage**: PostgreSQL table `trending_repos`
- **API**: FastAPI endpoint `/api/scrape-repos`
- **CLI Integration**: Node.js CLI command `namango scrape-repos`

## Components
1. **Scraper Engine**: Core logic for data collection and filtering
2. **GitHub Enricher**: Fetches detailed repo metadata via GitHub API
3. **Database Layer**: SQLAlchemy models for persistence
4. **Scheduler**: Background job for periodic scraping
5. **CLI Bridge**: HTTP client to trigger scraping from CLI

## Data Flow
1. CLI command → API endpoint
2. Scraper collects URLs from social media
3. GitHub API enriches with metadata
4. Filter and deduplicate
5. Store in database
6. Return results to CLI

## Filtering Criteria
- Stars: > 100
- Recent activity: commits within 30 days
- Categories: AI, agents, tools, MCPs (based on topics/description)
- Quality: exclude forks, archived repos

## Error Handling
- Rate limiting for APIs
- Retry failed requests
- Graceful degradation on service outages
- Logging for monitoring

## Testing
- Unit tests for scraper logic
- Integration tests for API endpoints
- Mock external APIs for CI/CD