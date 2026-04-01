# Repository Scraper

The repository scraper automatically discovers trending open source projects from Twitter and Reddit **every hour** in the background. The scraper runs continuously without any user interaction required.

## How It Works

**Automatically (Every Hour):**
1. Scraper starts up with the FastAPI application
2. Every hour, it silently scans Twitter and Reddit for new GitHub repositories
3. Filters repos by quality (100+ stars, recent activity, strategic relevance)
4. Auto-categorizes repos (agent, tool, mcp, general)
5. Stores new repos in the database
6. Runs in the background — no user interaction needed

## Setup

### 1. Configure API Credentials

Create or update environment variables in your deployment:

```bash
# GitHub Token (https://github.com/settings/tokens)
GITHUB_TOKEN=your_token_here
```

### 2. Deploy

The scraper starts automatically when the FastAPI application starts:

```bash
# Start the backend (scraper runs in background)
cd backend
uvicorn app.main:app --reload
```

**Console output:**
```
INFO:     Application startup complete
✓ Repository scraper scheduled to run every hour
```

## What Gets Scraped

The scraper discovers and stores repositories with:

- **Stars**: > 100
- **Activity**: Commits within last 30 days  
- **Relevance**: Topics/description mentions: `ai`, `agent`, `tool`, `mcp`, `model`, `context`, `protocol`, `orchestrator`
- **Categories**: agent, tool, mcp, or general

## Where Results Are Stored

Find discovered repos in the database:

```sql
-- View all trending repos
SELECT * FROM trending_repos;

-- Count by category
SELECT category, COUNT(*) FROM trending_repos GROUP BY category;

-- Find recent discoveries
SELECT name, stars, discovered_at FROM trending_repos 
ORDER BY discovered_at DESC LIMIT 10;
```

## Architecture

### Scheduler (`backend/app/main.py`)

```python
scheduler = AsyncIOScheduler()
scheduler.add_job(
    RepoScraper().scrape_and_store,
    'interval',
    hours=1,  # Every hour
    id='repo-scraper'
)
scheduler.start()
```

### Scraper Module (`backend/app/scraper/scraper.py`)

- `scrape_twitter(days)`: Finds GitHub URLs from tweets
- `scrape_reddit(days)`: Finds GitHub URLs from posts/comments
- `enrich_repo(url)`: Fetches metadata from GitHub API
- `filter_repo(data)`: Validates quality criteria
- `categorize_repo(data)`: Auto-assigns repo type
- `scrape_and_store()`: Main orchestration (runs hourly)

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
    discovered_at: datetime (auto-filled when stored)
    source: str  # twitter or reddit (tracks origin)
```

## Scheduling Behavior

- **Interval**: Every hour (3600 seconds)
- **Start**: Automatically on FastAPI startup
- **Shutdown**: Gracefully stops when app shuts down
- **Misfire Grace Period**: 10 minutes (handles API delays)

## Rate Limiting

- **GitHub API**: Automatic rate limiting with backoff
- **Twitter**: Monitored automatically
- **Reddit**: Adaptive rate limiting

The scraper handles rate limits gracefully without failures.

## Optional: Custom Schedules

To change the interval, modify `backend/app/main.py`:

```python
# Every 30 minutes
scheduler.add_job(..., 'interval', minutes=30)

# Every 12 hours
scheduler.add_job(..., 'interval', hours=12)

# Every day at 3 AM  
scheduler.add_job(..., 'cron', hour=3, minute=0)
```

## Monitoring & Logs

Check the application logs to see scraper activity:

```
INFO:     Repository scraper scheduled to run every hour
INFO:     Found 42 GitHub URLs from data sources
INFO:     Successfully scraped and stored 23 repositories (19 already existed)
```

## Troubleshooting

**"GITHUB_TOKEN" not set**
- Set `GITHUB_TOKEN` environment variable
- Scraper will fail silently (API calls skip) but continues running

**"PRAW exception: Received 401"**
- Verify `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`
- Reddit scraping will skip but Twitter scraping continues

**Zero repos discovered**
- Check that trending repos actually exist on Twitter/Reddit linking GitHub
- Network connectivity to social media APIs
- Verify no aggressive API rate limiting

## What's Different from Manual Trigger

**Before** (manually triggered):
```bash
namango scrape-repos --days 7  # User runs command
```

**Now** (automatic background):
```
✓ Runs every hour automatically
✓ No user command needed
✓ No "checking for repos" interruption
✓ Results always available in database
✓ Fully invisible to end users
```

## Future Enhancements

- [ ] Configurable schedule (environment variable)
- [ ] Webhook notifications for major discoveries
- [ ] Discord/Slack alerts
- [ ] Database cleanup (remove old entries after 90 days)
- [ ] Trending score calculation
- [ ] Repository health metrics

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