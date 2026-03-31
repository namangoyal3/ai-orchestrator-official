"""
Internal scraper utilities - not exposed as public API.
Repositories are scraped automatically in the background via APScheduler.
"""
from app.scraper import RepoScraper

# The scraper runs automatically every hour
# No public API endpoints - results stored in TrendingRepo table