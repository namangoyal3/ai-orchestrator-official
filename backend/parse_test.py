import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import json

async def test_parse():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        print("Fetching GitHub Trending...")
        await page.goto("https://github.com/trending?spoken_language_code=en")
        await asyncio.sleep(2)
        html = await page.content()
        await browser.close()
        
        soup = BeautifulSoup(html, "html.parser")
        articles = soup.find_all("article", class_="Box-row")
        print(f"Found {len(articles)} repos")
        for a in articles[:3]:
            h2 = a.find("h2")
            name = h2.text.strip().replace("\n", "").replace(" ", "") if h2 else "Unknown"
            p_desc = a.find("p")
            desc = p_desc.text.strip() if p_desc else "No description"
            print(f"Repo: {name} | Desc: {desc[:50]}...")

asyncio.run(test_parse())
