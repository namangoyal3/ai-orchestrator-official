import pytest
from datetime import datetime, timedelta
from app.models import TrendingRepo
from app.scraper import RepoScraper


def test_trending_repo_model():
    """Test TrendingRepo model creation."""
    repo = TrendingRepo(
        github_url="https://github.com/anthropics/anthropic-sdk-python",
        name="anthropic-sdk-python",
        description="Python SDK for Anthropic API",
        stars=500,
        forks=50,
        language="Python",
        topics=["ai", "sdk", "anthropic"],
        last_commit=datetime.now(),
        category="tool",
        source="twitter"
    )
    
    assert repo.github_url == "https://github.com/anthropics/anthropic-sdk-python"
    assert repo.category == "tool"
    assert repo.stars == 500


def test_filter_repo_valid():
    """Test valid repo filtering."""
    scraper = RepoScraper()
    
    data = {
        'stars': 500,
        'last_commit': datetime.now(),
        'topics': ['ai', 'agent'],
        'description': 'An AI orchestration framework'
    }
    
    assert scraper.filter_repo(data) == True


def test_filter_repo_low_stars():
    """Test filtering repos with low stars."""
    scraper = RepoScraper()
    
    data = {
        'stars': 50,  # Below threshold
        'last_commit': datetime.now(),
        'topics': ['ai', 'agent'],
        'description': 'An AI orchestration framework'
    }
    
    assert scraper.filter_repo(data) == False


def test_filter_repo_old_activity():
    """Test filtering repos with old activity."""
    scraper = RepoScraper()
    
    data = {
        'stars': 500,
        'last_commit': datetime.now() - timedelta(days=60),  # Beyond 30 days
        'topics': ['ai', 'agent'],
        'description': 'An AI orchestration framework'
    }
    
    assert scraper.filter_repo(data) == False


def test_categorize_repo_agent():
    """Test repo categorization as agent."""
    scraper = RepoScraper()
    
    data = {
        'stars': 500,
        'last_commit': datetime.now(),
        'topics': ['agent', 'ai'],
        'description': 'An AI agent framework'
    }
    
    assert scraper.categorize_repo(data) == 'agent'


def test_categorize_repo_tool():
    """Test repo categorization as tool."""
    scraper = RepoScraper()
    
    data = {
        'stars': 500,
        'last_commit': datetime.now(),
        'topics': ['tool', 'sdk'],
        'description': 'A developer tool'
    }
    
    assert scraper.categorize_repo(data) == 'tool'