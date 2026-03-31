from fastapi import APIRouter, HTTPException
from ..scraper import RepoScraper

router = APIRouter()

@router.post("/scrape-repos")
async def scrape_repos(days: int = 7):
    """Trigger repository scraping from Twitter and Reddit."""
    try:
        scraper = RepoScraper()
        count = await scraper.scrape_and_store(days)
        return {"message": f"Successfully scraped and stored {count} repositories"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")