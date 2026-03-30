import asyncio
import os
import sys
import httpx

# Append parent dir so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models import Base, LLMModel, Skill, MCP, Agent, Tool

engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def init_db():
    print("Ensuring database tables exist...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def sync_openrouter():
    """Fetches all models from OpenRouter and populates the LLMModel table."""
    print("Syncing OpenRouter models...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("https://openrouter.ai/api/v1/models", timeout=15.0)
            response.raise_for_status()
            data = response.json().get("data", [])
            
            async with SessionLocal() as db:
                for model in data:
                    model_id = model.get("id")
                    name = model.get("name")
                    provider = model_id.split('/')[0] if '/' in model_id else "unknown"
                    context_len = model.get("context_length", 0)
                    
                    pricing = model.get("pricing", {})
                    # Prevent type errors if pricing is string/None
                    prompt_price = float(pricing.get("prompt", 0)) * 1_000_000 if pricing.get("prompt") else 0.0
                    completion_price = float(pricing.get("completion", 0)) * 1_000_000 if pricing.get("completion") else 0.0
                    
                    # Merge into DB
                    existing = await db.get(LLMModel, model_id)
                    if existing:
                        existing.display_name = name
                        existing.context_length = context_len
                        existing.cost_per_1m_input = prompt_price
                        existing.cost_per_1m_output = completion_price
                    else:
                        new_model = LLMModel(
                            id=model_id,
                            display_name=name,
                            provider=provider,
                            context_length=context_len,
                            cost_per_1m_input=prompt_price,
                            cost_per_1m_output=completion_price,
                            source="openrouter"
                        )
                        db.add(new_model)
                await db.commit()
            print(f"✅ Synced {len(data)} models from OpenRouter.")
        except Exception as e:
            print(f"❌ Failed to sync OpenRouter: {str(e)}")

import json
from pydantic import BaseModel, Field

class ScrapedSkill(BaseModel):
    name: str
    description: str
    category: str

class ScrapedTool(BaseModel):
    name: str
    description: str
    website_url: str

class ScrapedRepo(BaseModel):
    name: str
    description: str
    repo_url: str

from bs4 import BeautifulSoup
import asyncio
from playwright.async_api import async_playwright

async def get_page_content(url: str) -> str:
    """Uses Playwright to fetch the page content, bypassing basic Cloudflare/Vercel blocks."""
    print(f"Fetching {url} via Headless Playwright...")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded")
            await asyncio.sleep(5)  # Wait for JS to render
            content = await page.content()
            await browser.close()
            return content
    except Exception as e:
        print(f"Playwright fetch failed for {url}: {e}")
        return ""

async def parse_and_insert_skills(content: str, category_name: str):
    if not content:
        return 0
    soup = BeautifulSoup(content, "html.parser")
    # Universal fallback dynamic parsing: get all H2/H3s and their associated descriptions
    headings = soup.find_all(['h2', 'h3', 'h4'])
    count = 0
    async with SessionLocal() as db:
        from sqlalchemy.future import select
        for heading in headings:
            name = heading.get_text(strip=True)[:100]
            if not name or len(name) < 3:
                continue
            
            # Find closest text description
            desc_tag = heading.find_next_sibling(['p', 'span', 'div'])
            desc = desc_tag.get_text(strip=True)[:500] if desc_tag else "Available heavily used AI tool."
            
            # Avoid inserting giant junk menu items
            if len(desc.split(' ')) < 3:
                continue

            result = await db.execute(select(Skill).where(Skill.name == name))
            existing = result.scalars().first()
            if not existing:
                count += 1
                db.add(Skill(
                    name=name,
                    description=desc,
                    category=category_name
                ))
        await db.commit()
    return count

async def sync_skillsmp():
    print("Scraping SkillsMP...")
    content = await get_page_content("https://skillsmp.com/en/timeline")
    count = await parse_and_insert_skills(content, "Agent Skill")
    print(f"✅ Synced {count} Skills from SkillsMP")

async def sync_futurepedia():
    print("Scraping Futurepedia...")
    content = await get_page_content("https://www.futurepedia.io/")
    count = await parse_and_insert_skills(content, "AI Tool")
    print(f"✅ Synced {count} Tools from Futurepedia")

async def sync_open_source_repos():
    print("Scraping top Open Source Repositories...")
    content = await get_page_content("https://github.com/trending?spoken_language_code=en")
    count = await parse_and_insert_skills(content, "Open Source Repo")
    print(f"✅ Synced {count} Repositories from GitHub Trending")

async def sync_mcpmarket():
    print("Syncing MCP Market...")
    import json
    # Extracted by Browser Subagent bypassing Vercel edge protections
    mcps_data = [
      {"name": "Superpowers", "description": "Empowers AI coding agents with a comprehensive and structured software development workflow, from design refinement to TDD-driven implementation.", "repo_url": "https://github.com/obra/superpowers"},
      {"name": "Context7", "description": "Fetches up-to-date documentation and code examples for LLMs and AI code editors directly from the source.", "repo_url": "https://github.com/upstash/context7"},
      {"name": "TrendRadar", "description": "Aggregates trending topics from over 35 platforms, offering intelligent filtering, automated multi-channel notifications, and AI-powered conversational analysis.", "repo_url": "https://github.com/sansan0/trendradar"},
      {"name": "MindsDB", "description": "Customizes AI from your data. Connect any data source to any AI model with automation.", "repo_url": "https://github.com/mindsdb/mindsdb"},
      {"name": "OpenSpec", "description": "A collection of MCP servers for various APIs and tools.", "repo_url": "https://github.com/fission-ai/openspec"},
      {"name": "Chrome DevTools", "description": "Allows AI agents to interact with Chrome DevTools for debugging and inspection.", "repo_url": "https://github.com/benjaminr/chrome-devtools-mcp"},
      {"name": "Playwright", "description": "Automates browser interactions for AI agents using the Playwright framework.", "repo_url": "https://github.com/microsoft/playwright-mcp"},
      {"name": "GitHub", "description": "Enables advanced automation and interaction capabilities with GitHub APIs.", "repo_url": "https://github.com/github/github-mcp-server"},
      {"name": "Ruflo", "description": "Orchestrates intelligent multi-agent swarms for Claude, coordinating autonomous workflows.", "repo_url": "https://github.com/ruvnet/ruflo"},
      {"name": "Task Master", "description": "Streamline AI-driven development workflows by automating task management with Claude.", "repo_url": "https://github.com/eyaltoledano/claude-task-master"},
      {"name": "GPT Researcher", "description": "Conducts in-depth web and local research on any topic, generating comprehensive reports.", "repo_url": "https://github.com/assafelovic/gpt-researcher"},
      {"name": "Next AI Draw.io", "description": "Integrates AI capabilities with draw.io diagrams to create, modify, and enhance visualizations.", "repo_url": "https://github.com/dayuanjiang/next-ai-draw-io"},
      {"name": "Graphiti", "description": "Builds and queries temporally-aware knowledge graphs tailored for AI agents.", "repo_url": "https://github.com/getzep/graphiti"},
      {"name": "FastMCP", "description": "Facilitates the creation of Model Context Protocol (MCP) servers with a Pythonic interface.", "repo_url": "https://github.com/jlowin/fastmcp"},
      {"name": "Serena", "description": "Turns an LLM into a coding agent that works directly on your codebase.", "repo_url": "https://github.com/oraios/serena"},
      {"name": "Beads", "description": "A high-performance memory and context management system for AI agents.", "repo_url": "https://github.com/steveyegge/beads"},
      {"name": "Blender MCP", "description": "Connects Blender to Claude AI, enabling prompt-assisted 3D modeling and scene creation.", "repo_url": "https://github.com/ahujasid/blender-mcp"},
      {"name": "n8n", "description": "Workflow automation tool with MCP support.", "repo_url": "https://github.com/dopehunter/n8n_mcp_server_complete"},
      {"name": "Cognee", "description": "Provides a reliable memory layer for AI applications and agents.", "repo_url": "https://github.com/topoteretes/cognee"},
      {"name": "Trigger.dev", "description": "Open source background jobs platform with MCP support.", "repo_url": "https://github.com/triggerdotdev/trigger.dev"},
      {"name": "Figma Context", "description": "Provides AI coding agents with simplified Figma layout information.", "repo_url": "https://github.com/glips/figma-context-mcp"},
      {"name": "Cua", "description": "Connects AI agents to your local and cloud infrastructure.", "repo_url": "https://github.com/trycua/cua"},
      {"name": "Xiaohongshu", "description": "MCP server for interacting with Xiaohongshu (Little Red Book) content.", "repo_url": "https://github.com/cjpnice/xiaohongshu_mcp"},
      {"name": "Kubeshark", "description": "Captures cluster-wide network traffic for Kubernetes with full context.", "repo_url": "https://github.com/kubeshark/kubeshark"},
      {"name": "FastAPI", "description": "Exposes FastAPI endpoints as Model Context Protocol (MCP) tools.", "repo_url": "https://github.com/tadata-org/fastapi_mcp"},
      {"name": "Convex", "description": "Connects your AI agent to your Convex backend.", "repo_url": "https://github.com/get-convex/convex-backend"},
      {"name": "ElevenLabs", "description": "Enables interaction with Text to Speech and audio processing APIs.", "repo_url": "https://github.com/elevenlabs/elevenlabs-mcp"},
      {"name": "Postgres", "description": "Model Context Protocol server for Postgres databases.", "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/postgres"},
      {"name": "SQLite", "description": "Model Context Protocol server for SQLite databases.", "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/sqlite"},
      {"name": "Google Drive", "description": "Connects AI agents to Google Drive for file management.", "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/google-drive"},
      {"name": "Puppeteer", "description": "Browser automation for AI agents using Puppeteer.", "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/puppeteer"},
      {"name": "Slack (Official)", "description": "Official MCP server for Slack integration.", "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/slack"},
      {"name": "Everything", "description": "A reference implementation of an MCP server with all features.", "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/everything"},
      {"name": "Filesystem", "description": "Allows AI agents to interact with the local filesystem.", "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem"},
      {"name": "Google Maps", "description": "Integrates Google Maps capabilities into AI agents.", "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/google-maps"},
      {"name": "Memory", "description": "A persistent memory layer for AI agents using MCP.", "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/memory"},
      {"name": "Sentry", "description": "Integrates Sentry error tracking with AI agents.", "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/sentry"},
      {"name": "Brave Search", "description": "Enables web search for AI agents using the Brave Search API.", "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search"},
      {"name": "Evernote", "description": "Connects AI agents to Evernote for note management.", "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/evernote"},
      {"name": "Fetch", "description": "A simple fetch tool for AI agents to retrieve web content.", "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/fetch"},
      {"name": "Git (Official)", "description": "Official MCP server for Git integration.", "repo_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/git"}
    ]
    
    async with SessionLocal() as db:
        for item in mcps_data:
            slug = item["name"].lower().replace(" ", "-")
            existing = await db.get(MCP, slug)
            if existing:
                existing.name = item["name"]
                existing.description = item["description"]
                existing.repo_url = item["repo_url"]
            else:
                db.add(MCP(
                    id=slug,
                    name=item["name"],
                    slug=slug,
                    description=item["description"],
                    repo_url=item["repo_url"]
                ))
        await db.commit()
    print(f"✅ Synced {len(mcps_data)} MCPs to the database.")
    return

async def main():
    await init_db()
    await sync_openrouter()
    await sync_skillsmp()
    await sync_futurepedia()
    await sync_open_source_repos()
    await sync_mcpmarket()

if __name__ == "__main__":
    asyncio.run(main())
