import os
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import snscrape.modules.twitter as sntwitter
import snscrape.modules.reddit as snreddit
from github import Github
from sqlalchemy.orm import Session

from app.models import TrendingRepo
from app.database import AsyncSessionLocal


class RepoScraper:
    def __init__(self):
        self.twitter_sources = ['github', 'opensource', 'python', 'javascript', 'machinelearning']
        self.reddit_sources = ['programming', 'github', 'opensource', 'MachineLearning', 'artificial']
        
        # Initialize clients
        self.github = Github(os.getenv('GITHUB_TOKEN'))
    
    def scrape_twitter(self, days: int = 7) -> List[str]:
        """Scrape GitHub URLs from Twitter."""
        urls = []
        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        for account in self.twitter_sources:
            try:
                query = f'from:{account} since:{since_date}'
                for tweet in sntwitter.TwitterSearchScraper(query).get_items():
                    # Extract GitHub URLs
                    github_urls = re.findall(r'https://github\.com/[^\s\n]+', tweet.rawContent)
                    urls.extend(github_urls)
            except Exception as e:
                print(f"Error scraping Twitter account {account}: {e}")
        
        return list(set(urls))  # Deduplicate
    
    def scrape_reddit(self, days: int = 7) -> List[str]:
        """Scrape GitHub URLs from Reddit using snscrape."""
        urls = []
        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        for sub in self.reddit_sources:
            try:
                query = f'subreddit:{sub} since:{since_date}'
                scraper = snreddit.RedditSubredditScraper(sub)
                
                for post in scraper.get_items():
                    if hasattr(post, 'url') and post.url:
                        # Check post URL
                        if 'github.com' in post.url:
                            urls.append(post.url)
                    
                    # Check post content
                    if hasattr(post, 'selftext') and post.selftext:
                        github_urls = re.findall(r'https://github\.com/[^\s\n]+', post.selftext)
                        urls.extend(github_urls)
                        
            except Exception as e:
                print(f"Error scraping Reddit subreddit {sub}: {e}")
        
        return list(set(urls))  # Deduplicate
    
    def enrich_repo(self, url: str) -> Optional[Dict]:
        """Fetch repo details from GitHub API."""
        try:
            match = re.search(r'github\.com/([^/]+)/([^/]+)', url)
            if not match:
                return None
            
            owner, repo_name = match.groups()
            repo = self.github.get_repo(f'{owner}/{repo_name}')
            
            # Get last commit
            commits = list(repo.get_commits())
            last_commit = commits[0].commit.author.date if commits else None
            
            return {
                'github_url': url.rstrip('/'),  # Remove trailing slash
                'name': repo.name,
                'description': repo.description or '',
                'stars': repo.stargazers_count,
                'forks': repo.forks_count,
                'language': repo.language,
                'topics': repo.get_topics(),
                'last_commit': last_commit
            }
        except Exception as e:
            print(f"Error enriching repo {url}: {e}")
            return None
    
    def filter_repo(self, data: Dict) -> bool:
        """Filter repos based on criteria."""
        # Stars > 100
        if data['stars'] <= 100:
            return False
        
        # Recent activity (within 30 days)
        if not data['last_commit']:
            return False
        
        thirty_days_ago = datetime.now() - timedelta(days=30)
        if data['last_commit'].replace(tzinfo=None) < thirty_days_ago:
            return False
        
        # Check for relevant topics/keywords
        text = ' '.join(data['topics']) + ' ' + data['description'].lower()
        relevant_terms = ['ai', 'agent', 'tool', 'mcp', 'model', 'context', 'protocol', 'orchestrator']
        
        return any(term in text for term in relevant_terms)
    
    def categorize_repo(self, data: Dict) -> str:
        """Categorize the repo."""
        text = ' '.join(data['topics']) + ' ' + data['description'].lower()
        
        if 'agent' in text:
            return 'agent'
        elif 'tool' in text or 'mcp' in text or 'protocol' in text:
            return 'tool'
        elif 'mcp' in text or 'model context' in text:
            return 'mcp'
        else:
            return 'general'
    
    async def scrape_and_store(self, days: int = 7) -> int:
        """Main scraping function."""
        # Scrape URLs
        twitter_urls = self.scrape_twitter(days)
        reddit_urls = self.scrape_reddit(days)
        all_urls = list(set(twitter_urls + reddit_urls))
        
        stored_count = 0
        
        async with AsyncSessionLocal() as session:
            for url in all_urls:
                # Check if already exists
                existing = await session.execute(
                    TrendingRepo.__table__.select().where(TrendingRepo.github_url == url)
                )
                if existing.fetchone():
                    continue
                
                # Enrich
                data = self.enrich_repo(url)
                if not data or not self.filter_repo(data):
                    continue
                
                # Categorize
                category = self.categorize_repo(data)
                
                # Store
                repo = TrendingRepo(
                    github_url=data['github_url'],
                    name=data['name'],
                    description=data['description'],
                    stars=data['stars'],
                    forks=data['forks'],
                    language=data['language'],
                    topics=data['topics'],
                    last_commit=data['last_commit'],
                    category=category,
                    source='twitter' if url in twitter_urls else 'reddit'
                )
                
                session.add(repo)
                stored_count += 1
            
            await session.commit()
        
        return stored_count