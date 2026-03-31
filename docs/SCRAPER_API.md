# Repository Scraper - Internal Implementation

**Note:** The repository scraper runs automatically in the background. No public API endpoints are exposed to end users.

## How It Works

The scraper runs **automatically every hour** in the background:

1. ✓ Starts when FastAPI application starts
2. ✓ Runs silently without user interaction
3. ✓ Discovers trending repos from Twitter + Reddit
4. ✓ Stores in `trending_repos` database table
5. ✓ Completes within seconds

## Access Discovered Repos

While there's no public "scrape" endpoint, the discovered repos are accessible:

```bash
# Query the database directly
sqlite3 backend/namango_dev.db "SELECT * FROM trending_repos LIMIT 10"

# Or build a public endpoint to browse results (optional)
# Example: GET /v1/trending-repos with pagination
```

## Schedule

- **Frequency**: Every 1 hour
- **Start**: Automatic on FastAPI startup
- **Duration**: 3-10 seconds per run (depends on API availability)
- **Error Handling**: Graceful - continues running even if API calls fail

## Internal Functions (for reference)

These are used internally (not exposed as API):

```python
scraper.scrape_twitter(days=7)      # → List[str] of URLs
scraper.scrape_reddit(days=7)       # → List[str] of URLs
scraper.enrich_repo(url)            # → Dict with metadata
scraper.filter_repo(data)           # → bool (valid or not)
scraper.categorize_repo(data)       # → str (agent/tool/mcp/general)
scraper.scrape_and_store(days=7)    # → int (repos stored)
```

## Configuration

To adjust the schedule, edit `backend/app/main.py`:

```python
# Change from hourly to every 30 minutes
scheduler.add_job(
    scraper.scrape_and_store,
    'interval',
    minutes=30  # ← Change this
)

# Or use cron-style scheduling
scheduler.add_job(
    scraper.scrape_and_store,
    'cron',
    hour=3,      # Run at 3 AM daily
    minute=0
)
```

## Database Query Examples

Get all trending repos:
```sql
SELECT id, name, stars, category, discovered_at FROM trending_repos
ORDER BY discovered_at DESC;
```

Get repos by category:
```sql
SELECT COUNT(*) as count, category FROM trending_repos GROUP BY category;
```

Get recent agents:
```sql
SELECT name, stars, language FROM trending_repos 
WHERE category = 'agent' 
ORDER BY discovered_at DESC 
LIMIT 10;
```

Get high-star repos:
```sql
SELECT name, stars, forks FROM trending_repos 
WHERE stars > 500 
ORDER BY stars DESC;
```

## Logging

View scraper activity in application logs:

```
INFO:     Application startup complete
✓ Repository scraper scheduled to run every hour

[After 1 hour...]
INFO:     Scraper job 'repo-scraper' executed successfully
INFO:     Stored 15 new repositories (7 duplicates skipped)
```