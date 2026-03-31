# End-to-End Testing Guide - Repository Scraper (Automatic Scheduler)

## Quick Start (No Credentials Required)

Test the scraper infrastructure running as an automatic hourly background job.

### Step 1: Prepare Environment
```bash
cd /Users/venkateshgupta1800gmail.com/ai-orchestrator-official/.worktrees/repo-scraper
export PYTHONPATH=$PWD/backend:$PYTHONPATH
```

### Step 2: Install Dependencies
```bash
cd backend
pip install -q snscrape praw PyGithub requests sqlalchemy
```

### Step 3: Run Unit Tests (No Credentials Needed)
```bash
pytest tests/test_scraper.py -v
```

**Expected Output:**
```
tests/test_scraper.py::test_trending_repo_model PASSED
tests/test_scraper.py::test_filter_repo_valid PASSED
tests/test_scraper.py::test_filter_repo_low_stars PASSED
tests/test_scraper.py::test_filter_repo_old_activity PASSED
tests/test_scraper.py::test_categorize_repo_agent PASSED
tests/test_scraper.py::test_categorize_repo_tool PASSED
======================== 6 passed in 0.23s ========================
```

### Step 4: Start Backend with Automatic Scheduler
```bash
cd backend
uvicorn app.main:app --reload
```

**Expected Output (Watch for this):**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
✓ Repository scraper scheduled to run every hour
```

This confirms the scheduler is active and will run every hour automatically.

### Step 5: Verify Scheduler is Running
The scraper runs automatically every hour. To verify it's set up correctly:

```bash
# In another terminal, check the database after a minute
sqlite3 backend/namango_dev.db << 'EOF'
SELECT COUNT(*) as total FROM trending_repos;
SELECT category, COUNT(*) FROM trending_repos GROUP BY category;
EOF
```

**Or wait for logs** - within the first hour, you'll see:
```
INFO:     Scraper job 'repo-scraper' executed successfully (or attempted)
```

## Full Testing with Credentials

### Step 1: Acquire Credentials

**GitHub Token:**
1. Go to https://github.com/settings/tokens/new
2. Name: "Namango Scraper"
3. Scope: Check `public_repo`
4. Generate and copy token

**Reddit Credentials:**
1. Go to https://www.reddit.com/prefs/apps/
2. Click "Create an application"
3. Name: "Namango Repo Scraper"
4. Type: "script"
5. Redirect URI: `http://localhost`
6. Copy Client ID and Client Secret

### Step 2: Configure Environment
```bash
cd backend
cat > .env << 'EOF'
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
REDDIT_CLIENT_ID=xxxxxxxx
REDDIT_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxx
EOF
```

### Step 3: Start Backend Again
```bash
cd backend
uvicorn app.main:app --reload
```

The scraper will now actually run and attempt to scrape real data from Twitter/Reddit.

### Step 4: Monitor First Run
Check logs for successful scraping:

```bash
# In another terminal
tail -f backend/nohup.out
```

Watch for messages like:
```
✓ Found 42 GitHub URLs from Twitter
✓ Found 28 GitHub URLs from Reddit  
✓ Enriching repositories with GitHub metadata...
✓ Successfully scraped and stored 15 new repositories
```

### Step 5: Verify Data in Database
```bash
sqlite3 backend/namango_dev.db << 'EOF'
-- Count all repos
SELECT COUNT(*) as total FROM trending_repos;

-- See repos by category
SELECT category, COUNT(*) FROM trending_repos GROUP BY category;

-- View recent repos
SELECT name, stars, category, discovered_at FROM trending_repos 
ORDER BY discovered_at DESC LIMIT 5;
EOF
```

## Testing Scheduler Behavior

### Verify Hourly Execution
The scraper runs at the start and then every 60 minutes automatically.

**Test 1: Watch the logs** (takes 1 hour to see second run)
```bash
# Keep monitoring logs - after 1 hour you should see another execution
watch -n 60 'grep "Scraper job" backend/nohup.out | tail -5'
```

**Test 2: Check database growth** (instant, if credentials provided)
```bash
# Run immediately (within 1 minute)
sqlite3 backend/namango_dev.db "SELECT COUNT(*) FROM trending_repos"

# Run again after a few minutes - count may increase slightly
sqlite3 backend/namango_dev.db "SELECT COUNT(*) FROM trending_repos"
```

**Test 3: Force manual test of scraper logic** (simulates what scheduler does)
```bash
python -c "
import asyncio
from app.scraper import RepoScraper

async def test():
    scraper = RepoScraper()
    # Simulate what the scheduler runs hourly
    count = await scraper.scrape_and_store(days=7)
    print(f'✅ Added {count} new repositories')

asyncio.run(test())
"
```

## Testing Error Handling

### Without Credentials
The scraper still runs every hour but API calls fail gracefully:

```bash
# Remove credentials
unset GITHUB_TOKEN
unset REDDIT_CLIENT_ID
unset REDDIT_CLIENT_SECRET

# Start backend - scheduler still runs, but returns 0 repos silently
uvicorn app.main:app --reload

# Logs will show:
# ✓ Repository scraper scheduled to run every hour
# (Actual API failures are silent - no errors, just 0 repos stored)
```

### Invalid Credentials
```bash
export GITHUB_TOKEN=invalid_token_here
export REDDIT_CLIENT_ID=fake_id

# Backend starts fine, scheduler runs, API calls fail gracefully
# Zero repos stored, no errors in app logs
```

## Scheduling Behavior Tests

### Verify Scheduler Configuration
```bash
python -c "
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

sched = AsyncIOScheduler()
sched.add_job(lambda: None, 'interval', hours=1, id='test-job')

job = sched.get_job('test-job')
print(f'Job ID: {job.id}')
print(f'Next run: 1 hour from now')
print(f'Trigger: {job.trigger}')
"
```

## Integration Testing Checklist

- [ ] Unit tests pass (pytest)
- [ ] Backend starts without errors
- [ ] Scheduler initializes with message "✓ Repository scraper scheduled..."
- [ ] No API endpoints exposed for scraping (removed)
- [ ] CLI no longer has `scrape-repos` command
- [ ] Database table `trending_repos` exists
- [ ] Data stores in database correctly
- [ ] Error handling works gracefully (continues running even if API fails)
- [ ] Rate limiting handled automatically

## Production Readiness Checklist

- [ ] All unit tests pass
- [ ] Scheduler starts on app startup
- [ ] Database migrations applied
- [ ] Environment variables configured (GITHUB_TOKEN, REDDIT credentials)
- [ ] Logging shows hourly execution
- [ ] Error logs are informative
- [ ] Credentials secured (not in code)
- [ ] No manual user commands needed
- [ ] Documentation updated
- [ ] Performance acceptable

## Troubleshooting

### Scheduler Not Starting
```bash
# Check for import errors
python -c "from apscheduler.schedulers.asyncio import AsyncIOScheduler"

# Reinstall if needed
pip install --upgrade apscheduler
```

### API Calls Failing Silently
This is expected if credentials are invalid. Check:
```bash
echo $GITHUB_TOKEN          # Should not be empty
echo $REDDIT_CLIENT_ID      # Should not be empty
echo $REDDIT_CLIENT_SECRET  # Should not be empty
```

### Database Not Growing
```bash
# Check if table exists
sqlite3 backend/namango_dev.db ".tables" | grep trending_repos

# Check for data
sqlite3 backend/namango_dev.db "SELECT COUNT(*) FROM trending_repos"

# If 0 repos, either:
# 1. Credentials invalid/missing (add them)
# 2. Wait up to 1 hour for first scheduled run
# 3. Check if API services are down
```

---

**Next Step**: After successful testing, merge to main and deploy to Railway

## Full Testing with Credentials

To test actual scraping:

### Step 1: Acquire Credentials

**GitHub Token:**
1. Go to https://github.com/settings/tokens/new
2. Name: "Namango Scraper"
3. Scope: Check `public_repo`
4. Generate and copy token

**Reddit Credentials:**
1. Go to https://www.reddit.com/prefs/apps/
2. Click "Create an application"
3. Name: "Namango Repo Scraper"
4. Type: "script"
5. Redirect URI: `http://localhost`
6. Copy Client ID and Client Secret

### Step 2: Configure Environment
```bash
cd backend
cat > .env << 'EOF'
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
REDDIT_CLIENT_ID=xxxxxxxx
REDDIT_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxx
EOF
```

### Step 3: Test Scraper Module Directly
```bash
python -c "
import asyncio
from app.scraper import RepoScraper

async def test():
    scraper = RepoScraper()
    
    # Test Twitter scraping
    print('Scraping Twitter...')
    twitter_urls = scraper.scrape_twitter(days=1)
    print(f'Found {len(twitter_urls)} GitHub URLs on Twitter')
    
    # Test Reddit scraping
    print('Scraping Reddit...')
    reddit_urls = scraper.scrape_reddit(days=1)
    print(f'Found {len(reddit_urls)} GitHub URLs on Reddit')
    
    # Test enrichment
    if twitter_urls:
        url = twitter_urls[0]
        print(f'Enriching {url}...')
        data = scraper.enrich_repo(url)
        if data:
            print(f'✅ Success: {data[\"name\"]} ({data[\"stars\"]} stars)')

asyncio.run(test())
"
```

### Step 4: Start Backend API
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### Step 5: Test API Endpoint in New Terminal
```bash
# First, create a test API key (check backend logs or use existing one)
# Or use admin endpoint to create one if available

# Test the scraper endpoint
curl -X POST "http://localhost:8000/v1/scrape-repos?days=7" \
  -H "X-API-Key: gw-test-key" \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "message": "Successfully scraped and stored 15 repositories"
}
```

### Step 6: Verify Data in Database
```bash
# In a new terminal
cd backend
sqlite3 namango_dev.db << 'EOF'
SELECT COUNT(*) as total_repos FROM trending_repos;
SELECT name, stars, category FROM trending_repos LIMIT 5;
SELECT category, COUNT(*) FROM trending_repos GROUP BY category;
EOF
```

**Expected Output:**
```
total_repos
42

name|stars|category
anthropic-sdk-python|500|tool
autogen|1200|agent
crewai|800|agent
...

category|COUNT(*)
agent|12
tool|18
mcp|8
general|4
```

## Testing CLI Integration

### Setup
```bash
cd cli/create-namango-app
npm install

# Make namango command available
npm link
```

### Test Login
```bash
namango login
# Enter test API key when prompted (can be any non-empty value for testing)
```

### Test Scrape Command
```bash
namango scrape-repos --days 7
```

**Expected Output:**
```
🔍 Scraping trending open source repositories...

Searching the last 7 days from Twitter and Reddit...

✅ Successfully scraped and stored 42 repositories

💡 Tip: Use the Namango platform to browse and explore these repositories.
```

## Troubleshooting

### Tests Fail with Import Errors
```bash
# Make sure you're in the right directory and Python path is set
export PYTHONPATH=$PWD/backend:$PYTHONPATH
cd backend
pytest tests/test_scraper.py -v
```

### API Returns 401 Unauthorized
```bash
# Make sure API key is passed correctly
curl -X POST "http://localhost:8000/v1/scrape-repos" \
  -H "X-API-Key: your-actual-key"

# Check that the key exists in the database
sqlite3 backend/namango_dev.db \
  "SELECT * FROM api_keys WHERE is_active = true LIMIT 1;"
```

### Scraper Returns 0 Results
**This is normal without credentials!** The scraper will:
- Attempt to query Twitter/Reddit
- Get rate-limited or fail silently
- Return empty URL list
- Store 0 repos

**This is expected behavior** and proves the error handling works.

### GitHub API: "401 Unauthorized"
- Verify `GITHUB_TOKEN` is set correctly
- Token must have `public_repo` scope
- Check token hasn't expired

### Reddit: "Received 401 Unauthorized"
- Verify both `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`
- Try creating a new app at https://reddit.com/prefs/apps
- Make sure app type is "script"

## Performance Testing

### Test with Different Time Windows
```bash
# Test 1 day (faster, fewer repos)
namango scrape-repos --days 1

# Test 7 days (standard)
namango scrape-repos --days 7

# Test 30 days (comprehensive)
namango scrape-repos --days 30
```

### Monitor API Response Time
```bash
time curl -X POST "http://localhost:8000/v1/scrape-repos?days=7" \
  -H "X-API-Key: test-key"
```

Typical response time: **2-10 seconds** (depends on API availability)

## Security Testing

### API Key Validation
```bash
# Should fail with invalid key
curl -X POST "http://localhost:8000/v1/scrape-repos" \
  -H "X-API-Key: invalid-key"

# Expected: 401 Unauthorized
```

### SQL Injection (Should be Safe)
```bash
# Test with malicious input
curl -X POST "http://localhost:8000/v1/scrape-repos?days=999999' OR '1'='1" \
  -H "X-API-Key: test-key"

# Expected: Normal response (SQLAlchemy prevents injection)
```

## Integration Testing Checklist

- [ ] Unit tests pass (`pytest`)
- [ ] Model creation works without errors
- [ ] API server starts without errors
- [ ] API endpoint responds to requests
- [ ] Data stores in database
- [ ] CLI command executes successfully
- [ ] Environment variables are respected
- [ ] Error handling works gracefully
- [ ] Rate limiting is handled
- [ ] Database deduplication prevents duplicates

## Production Readiness Checklist

- [ ] All unit tests pass
- [ ] Integration tests successful
- [ ] Error logs are informative
- [ ] Rate limiting configured
- [ ] Credentials secured in environment
- [ ] Database migrations applied
- [ ] API key authentication in place
- [ ] Documentation complete
- [ ] CLI command documented
- [ ] Performance acceptable

---

**Next Step**: After successful testing, merge to main and deploy to Railway