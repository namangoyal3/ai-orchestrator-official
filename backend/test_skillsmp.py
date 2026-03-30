import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page()
        await page.goto("https://skillsmp.com/en/timeline")
        await asyncio.sleep(3)
        html = await page.content()
        await b.close()
        
        soup = BeautifulSoup(html, "html.parser")
        print("\n--- Next.js Data ---")
        script = soup.find("script", id="__NEXT_DATA__")
        if script:
            print("Found __NEXT_DATA__ JSON block length:", len(script.string))
        else:
            print("No __NEXT_DATA__. Finding cards...")
            cards = soup.select("div.card, div[class*='item'], li")
            print(f"Found {len(cards)} generic elements.")

asyncio.run(run())
