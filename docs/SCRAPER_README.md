# Repository Scraper

The repository scraper automatically discovers trending open source projects from Twitter and Reddit, enriches them with GitHub metadata, and stores them in the Namango platform.

## Features

- **Multi-source scraping**: Twitter and Reddit
- **Intelligent filtering**: Identifies AI agents, tools, MCPs, and general open source projects
- **Real-time metadata**: Fetches stars, forks, language, and commit history from GitHub
- **Categorization**: Automatically categorizes repos (agent, tool, mcp, general)
- **Deduplication**: Avoids storing duplicate repositories
- **Scheduled runs**: Periodic background scraping

## Setup

### 1. Configure API Credentials

Create or update `.env.scraper` in `backend/`:

```bash
# GitHub Token (https://github.com/settings/tokens)
GITHUB_TOKEN=your_token_here

# Reddit App (https://www.reddit.com/prefs/apps)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Use from CLI

```bash
# Login first
namango login

# Scrape repos from the last 7 days
namango scrape-repos

# Scrape repos from the last 30 days
namango scrape-repos --days 30
```

### 4. Use via API

```bash
curl -X POST http://localhost:8000/v1/scrape-repos?days=7 \
  -H "X-API-Key: your-api-key"
```

## Architecture

### Scraper Module (`backend/app/scraper/`)

- **scraper.py**: Core scraping logic
  - `RepoScraper.scrape_twitter()`: Extracts GitHub URLs from tweets
  - `RepoScraper.scrape_reddit()`: Extracts GitHub URLs from posts/comments
  - `RepoScraper.enrich_repo()`: Fetches metadata from GitHub API
  - `RepoScraper.filter_repo()`: Validates quality criteria
  - `RepoScraper.categorize_repo()`: Assigns repo category
  - `RepoScraper.scrape_and_store()`: Main orchestration function

### API Endpoint (`backend/app/api/scraper.py`)

- `POST /v1/scrape-repos`: Triggers scraping
  - Parameter: `days` (int, default 7)
  - Returns: `{"message": "Successfully scraped and stored X repositories"}`

### Database Model (`backend/app/models.py`)

```python
class TrendingRepo(Base):
    github_url: str (unique)
    name: str
    description: str
    stars: int
    forks: int
    language: str
    topics: list
    last_commit: datetime
    category: str  # agent, tool, mcp, general
    discovered_at: datetime
    source: str  # twitter, reddit
```

## Filtering Criteria

Repos must meet ALL criteria:

1. **Stars**: > 100
2. **Activity**: Commit within last 30 days
3. **Relevance**: Topics or description contains: `ai`, `agent`, `tool`, `mcp`, `model`, `context`, `protocol`, `orchestrator`

## Rate Limiting

- **GitHub API**: 60 requests/hour (public) or 5,000/hour (authenticated)
- **Twitter**: Monitored via snscrape
- **Reddit**: Respects rate limits automatically

## Scheduling (Optional)

In production, add to `backend/app/main.py`:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.scraper import RepoScraper

scheduler = AsyncIOScheduler()
scheduler.add_job(RepoScraper().scrape_and_store, 'interval', hours=24)
scheduler.start()
```

## Testing

```bash
cd backend
pytest tests/test_scraper.py -v
```

## Troubleshooting

**"Integration 'github' not found"**
- Ensure `GITHUB_TOKEN` is set and valid

**"PRAW exception: Received 401 Unauthorized"**
- Check `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`

**"Rate limit exceeded"**
- Scraper uses exponential backoff automatically
- GitHub: use authenticated requests for higher limits
- Reddit: apply for higher rate limits in your app settings

## Future Enhancements

- [ ] Discord/Slack community scraping
- [ ] HackerNews trending repos
- [ ] Product Hunt AI tools
- [ ] GitHub trending page scraping
- [ ] Batch operations for faster scraping
- [ ] Webhook notifications for new discoveries
- [ ] Web UI for browsing scraped repos