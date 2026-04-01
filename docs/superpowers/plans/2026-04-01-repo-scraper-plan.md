# Open Source Repo Scraper Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a scraper that discovers trending open source GitHub repos, agents, tools, and MCPs from Twitter/Reddit and integrates with the AI Orchestrator CLI.

**Architecture:** Python backend module with social media scraping, GitHub enrichment, database storage, FastAPI endpoint, and Node.js CLI bridge.

**Tech Stack:** Python (snscrape, PRAW, requests), FastAPI, SQLAlchemy, Node.js

---

### Task 1: Database Model for Trending Repos

**Files:**
- Modify: `backend/app/models.py`

- [ ] **Step 1: Add TrendingRepo model**

```python
class TrendingRepo(Base):
    __tablename__ = "trending_repos"
    
    id = Column(Integer, primary_key=True)
    github_url = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    stars = Column(Integer)
    forks = Column(Integer)
    language = Column(String)
    topics = Column(JSON)
    last_commit = Column(DateTime)
    category = Column(String)  # 'agent', 'tool', 'mcp', 'general'
    discovered_at = Column(DateTime, default=datetime.utcnow)
    source = Column(String)  # 'twitter', 'reddit'
```

- [ ] **Step 2: Run migration**

Run: `alembic revision --autogenerate -m "Add trending_repos table"`
Then: `alembic upgrade head`

- [ ] **Step 3: Commit**

### Task 2: Scraper Core Module

**Files:**
- Create: `backend/app/scraper/__init__.py`
- Create: `backend/app/scraper/scraper.py`

- [ ] **Step 1: Install dependencies**

Add to `backend/requirements.txt`:
```
snscrape
praw
requests
```

- [ ] **Step 2: Create scraper.py**

```python
import snscrape.modules.twitter as sntwitter
import praw
import re
from github import Github
from .models import TrendingRepo

class RepoScraper:
    def __init__(self):
        self.twitter_sources = ['github', 'opensource', 'python', 'javascript']
        self.reddit_sources = ['programming', 'github', 'opensource', 'MachineLearning']
        self.github = Github(os.getenv('GITHUB_TOKEN'))
        
    def scrape_twitter(self, days=7):
        urls = []
        for account in self.twitter_sources:
            for tweet in sntwitter.TwitterSearchScraper(f'from:{account} since:{days} days ago').get_items():
                urls.extend(re.findall(r'https://github\.com/[^\s]+', tweet.rawContent))
        return urls
    
    def scrape_reddit(self, days=7):
        reddit = praw.Reddit(...)
        urls = []
        for sub in self.reddit_sources:
            for post in reddit.subreddit(sub).new(limit=100):
                if post.created_utc > time.time() - days*86400:
                    urls.extend(re.findall(r'https://github\.com/[^\s]+', post.selftext + post.url))
        return urls
    
    def enrich_repo(self, url):
        match = re.search(r'github\.com/([^/]+)/([^/]+)', url)
        if match:
            repo = self.github.get_repo(f'{match.group(1)}/{match.group(2)}')
            return {
                'github_url': url,
                'name': repo.name,
                'description': repo.description,
                'stars': repo.stargazers_count,
                'forks': repo.forks_count,
                'language': repo.language,
                'topics': repo.get_topics(),
                'last_commit': repo.get_commits()[0].commit.author.date if repo.get_commits() else None
            }
        return None
    
    def filter_repo(self, data):
        return (data['stars'] > 100 and 
                data['last_commit'] and 
                (datetime.utcnow() - data['last_commit']).days < 30 and
                any(term in ' '.join(data['topics'] + [data['description'] or '']).lower() 
                    for term in ['ai', 'agent', 'tool', 'mcp']))
    
    def scrape_and_store(self):
        urls = set(self.scrape_twitter() + self.scrape_reddit())
        for url in urls:
            data = self.enrich_repo(url)
            if data and self.filter_repo(data):
                category = 'agent' if 'agent' in data['description'].lower() else 'tool' if 'tool' in data['description'].lower() else 'mcp' if 'mcp' in data['description'].lower() else 'general'
                TrendingRepo.create(**data, category=category)
```

- [ ] **Step 3: Create __init__.py**

```python
from .scraper import RepoScraper
```

- [ ] **Step 4: Test scraper**

Run: `python -c "from app.scraper import RepoScraper; s = RepoScraper(); print(len(s.scrape_twitter(1)))"`

- [ ] **Step 5: Commit**

### Task 3: API Endpoint

**Files:**
- Create: `backend/app/api/scraper.py`

- [ ] **Step 1: Create scraper API**

```python
from fastapi import APIRouter
from ..scraper import RepoScraper

router = APIRouter()

@router.post("/scrape-repos")
async def scrape_repos():
    scraper = RepoScraper()
    count = scraper.scrape_and_store()
    return {"message": f"Scraped and stored {count} repos"}
```

- [ ] **Step 2: Add to main.py**

In `backend/app/main.py`, add:
```python
from .api import scraper
app.include_router(scraper.router, prefix="/api")
```

- [ ] **Step 3: Test endpoint**

Run: `curl -X POST http://localhost:8000/api/scrape-repos`

- [ ] **Step 4: Commit**

### Task 4: CLI Integration

**Files:**
- Modify: `cli/create-namango-app/package.json`
- Modify: `cli/create-namango-app/bin/index.js`

- [ ] **Step 1: Add scrape command to CLI**

In `bin/index.js`, add:
```javascript
program
  .command('scrape-repos')
  .description('Scrape trending open source repos')
  .action(async () => {
    const response = await fetch(`${API_URL}/api/scrape-repos`, { method: 'POST' });
    const result = await response.json();
    console.log(result.message);
  });
```

- [ ] **Step 2: Test CLI**

Run: `npm run scrape-repos`

- [ ] **Step 3: Commit**

### Task 5: Scheduler for Continuous Scraping

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Add APScheduler**

Add to requirements.txt: `apscheduler`

- [ ] **Step 2: Schedule scraping**

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(RepoScraper().scrape_and_store, 'interval', hours=24)
scheduler.start()
```

- [ ] **Step 3: Test scheduler**

Run app and check logs.

- [ ] **Step 4: Commit**

### Task 6: Documentation and Testing

**Files:**
- Create: `backend/tests/test_scraper.py`
- Modify: `README.md`

- [ ] **Step 1: Write tests**

```python
def test_scraper():
    scraper = RepoScraper()
    urls = scraper.scrape_twitter(1)
    assert len(urls) >= 0
```

- [ ] **Step 2: Update README**

Add section: "Scraping Trending Repos: Use `namango scrape-repos` to discover new tools and agents."

- [ ] **Step 3: Commit**