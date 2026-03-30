"""
Tool Registry — all pre-built tool integrations available to agents.
Each tool is a callable async function with a standardized interface.
"""
import json
import re
from typing import Any, Optional
import httpx
from bs4 import BeautifulSoup


# ─────────────────────────────────────────────
# Tool result schema
# ─────────────────────────────────────────────

class ToolResult:
    def __init__(self, success: bool, output: Any, error: Optional[str] = None):
        self.success = success
        self.output = output
        self.error = error

    def to_dict(self) -> dict:
        return {"success": self.success, "output": self.output, "error": self.error}


# ─────────────────────────────────────────────
# Web Tools
# ─────────────────────────────────────────────

async def web_scrape(url: str, extract: str = "text") -> ToolResult:
    """Fetch and extract content from a URL."""
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; AIGateway/1.0; +https://aigateway.io)"
            }
            response = await client.get(url, headers=headers)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # Remove scripts and styles
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        if extract == "text":
            text = soup.get_text(separator="\n", strip=True)
            # Collapse excessive whitespace
            text = re.sub(r"\n{3,}", "\n\n", text)
            return ToolResult(True, text[:15000])  # cap at 15k chars
        elif extract == "html":
            return ToolResult(True, str(soup)[:15000])
        elif extract == "links":
            links = [
                {"text": a.get_text(strip=True), "href": a.get("href")}
                for a in soup.find_all("a", href=True)
            ]
            return ToolResult(True, links[:100])
        elif extract == "metadata":
            meta = {
                "title": soup.title.string if soup.title else "",
                "description": "",
                "og_image": "",
            }
            desc = soup.find("meta", attrs={"name": "description"})
            if desc:
                meta["description"] = desc.get("content", "")
            og_img = soup.find("meta", attrs={"property": "og:image"})
            if og_img:
                meta["og_image"] = og_img.get("content", "")
            return ToolResult(True, meta)
        else:
            return ToolResult(False, None, f"Unknown extract type: {extract}")

    except httpx.TimeoutException:
        return ToolResult(False, None, "Request timed out after 15 seconds")
    except Exception as e:
        return ToolResult(False, None, str(e))


async def web_search(query: str, num_results: int = 5) -> ToolResult:
    """
    Perform a web search using DuckDuckGo's instant answer API.
    For production, integrate SerpAPI, Brave Search, or Tavily.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Use DuckDuckGo Instant Answer API (free, no key needed)
            response = await client.get(
                "https://api.duckduckgo.com/",
                params={
                    "q": query,
                    "format": "json",
                    "no_html": 1,
                    "skip_disambig": 1,
                },
                headers={"User-Agent": "AIGateway/1.0"},
            )
            data = response.json()

        results = []

        # Abstract (main answer)
        if data.get("AbstractText"):
            results.append({
                "title": data.get("Heading", query),
                "snippet": data["AbstractText"],
                "url": data.get("AbstractURL", ""),
                "source": "DuckDuckGo Abstract",
            })

        # Related topics
        for topic in data.get("RelatedTopics", [])[:num_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({
                    "title": topic.get("Text", "")[:100],
                    "snippet": topic.get("Text", ""),
                    "url": topic.get("FirstURL", ""),
                    "source": "DuckDuckGo",
                })

        if not results:
            results = [{"title": "Search completed", "snippet": f"Query: {query}", "url": "", "source": "DuckDuckGo"}]

        return ToolResult(True, results[:num_results])
    except Exception as e:
        return ToolResult(False, None, str(e))


# ─────────────────────────────────────────────
# Document Tools
# ─────────────────────────────────────────────

async def parse_pdf(file_path: str) -> ToolResult:
    """Extract text from a PDF file."""
    try:
        import PyPDF2
        text_parts = []
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text_parts.append(page.extract_text() or "")
        return ToolResult(True, "\n\n".join(text_parts)[:20000])
    except Exception as e:
        return ToolResult(False, None, str(e))


async def parse_docx(file_path: str) -> ToolResult:
    """Extract text from a .docx file."""
    try:
        import docx
        doc = docx.Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return ToolResult(True, "\n\n".join(paragraphs)[:20000])
    except Exception as e:
        return ToolResult(False, None, str(e))


async def parse_text(content: str, max_length: int = 20000) -> ToolResult:
    """Process raw text content."""
    return ToolResult(True, content[:max_length])


# ─────────────────────────────────────────────
# Data & Code Tools
# ─────────────────────────────────────────────

async def json_query(data: Any, jq_path: str) -> ToolResult:
    """Query JSON data using a simple path expression."""
    try:
        if isinstance(data, str):
            data = json.loads(data)

        # Simple dot-notation path traversal
        parts = jq_path.strip(".").split(".")
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                current = current[int(part)]
            else:
                return ToolResult(False, None, f"Path '{jq_path}' not found")

        return ToolResult(True, current)
    except Exception as e:
        return ToolResult(False, None, str(e))


async def calculator(expression: str) -> ToolResult:
    """Safely evaluate a mathematical expression."""
    try:
        # Whitelist safe characters
        safe = re.match(r'^[\d\s\+\-\*\/\(\)\.\^%]+$', expression.replace("**", "^"))
        if not safe:
            return ToolResult(False, None, "Unsafe expression")
        result = eval(expression.replace("^", "**"), {"__builtins__": {}})
        return ToolResult(True, result)
    except Exception as e:
        return ToolResult(False, None, str(e))


async def summarize_text(text: str, max_sentences: int = 5) -> ToolResult:
    """Extract key sentences from text (extractive summarization)."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= max_sentences:
        return ToolResult(True, text)
    # Simple heuristic: take first 2, middle 1, last 2
    summary = sentences[:2] + sentences[len(sentences)//2:len(sentences)//2+1] + sentences[-2:]
    return ToolResult(True, " ".join(summary))


# ─────────────────────────────────────────────
# API Integration Tools
# ─────────────────────────────────────────────

async def http_request(
    method: str,
    url: str,
    headers: Optional[dict] = None,
    body: Optional[dict] = None,
    params: Optional[dict] = None,
) -> ToolResult:
    """Make an HTTP request to any API endpoint."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.request(
                method=method.upper(),
                url=url,
                headers=headers or {},
                json=body,
                params=params or {},
            )
            try:
                data = response.json()
            except Exception:
                data = response.text

            return ToolResult(True, {
                "status_code": response.status_code,
                "data": data,
                "headers": dict(response.headers),
            })
    except Exception as e:
        return ToolResult(False, None, str(e))


async def sql_query(connection_string: str, query: str) -> ToolResult:
    """Execute a SQL SELECT query (read-only)."""
    # Only allow SELECT statements for safety
    if not query.strip().upper().startswith("SELECT"):
        return ToolResult(False, None, "Only SELECT queries are allowed for safety")
    try:
        import aiosqlite
        if "sqlite" in connection_string:
            db_path = connection_string.replace("sqlite:///", "")
            async with aiosqlite.connect(db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(query) as cursor:
                    rows = await cursor.fetchall()
                    return ToolResult(True, [dict(row) for row in rows])
        return ToolResult(False, None, "Only SQLite supported in this demo")
    except Exception as e:
        return ToolResult(False, None, str(e))


async def github_repo_info(owner: str, repo: str, token: Optional[str] = None) -> ToolResult:
    """Fetch GitHub repository information."""
    try:
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers=headers,
            )
            data = response.json()

        return ToolResult(True, {
            "name": data.get("name"),
            "description": data.get("description"),
            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "language": data.get("language"),
            "topics": data.get("topics", []),
            "last_updated": data.get("updated_at"),
        })
    except Exception as e:
        return ToolResult(False, None, str(e))


async def github_search_and_rank(query: str, limit: int = 10, sort: str = "stars") -> ToolResult:
    """Search for repositories and rank them based on relevance and stars."""
    try:
        headers = {"Accept": "application/vnd.github.v3+json"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://api.github.com/search/repositories",
                params={"q": query, "sort": sort, "order": "desc", "per_page": limit},
                headers=headers,
            )
            data = response.json()
            items = data.get("items", [])
            
            # Simple ranking logic (stars + forks ratio)
            ranked = []
            for item in items:
                score = item.get("stargazers_count", 0) + (item.get("forks_count", 0) * 2)
                ranked.append({
                    "name": item.get("full_name"),
                    "description": item.get("description"),
                    "stars": item.get("stargazers_count"),
                    "forks": item.get("forks_count"),
                    "url": item.get("html_url"),
                    "score": score,
                    "language": item.get("language"),
                })
            
            # Sort by score (descending)
            ranked.sort(key=lambda x: x["score"], reverse=True)
            
            return ToolResult(True, ranked)
    except Exception as e:
        return ToolResult(False, None, str(e))


async def news_search(query: str, category: str = "general") -> ToolResult:
    """Search for news articles (using NewsAPI-compatible endpoint)."""
    # In production, replace with NewsAPI, Bing News, or similar
    return ToolResult(True, {
        "articles": [
            {
                "title": f"News about: {query}",
                "source": "News API (configure NewsAPI key for live results)",
                "url": "",
                "published_at": "2025-01-01",
                "description": f"Configure a NewsAPI key in settings to get live news for: {query}",
            }
        ],
        "note": "Add NEWSAPI_KEY to .env for live results",
    })


async def weather(location: str, units: str = "metric") -> ToolResult:
    """Get current weather for a location (OpenWeatherMap)."""
    # In production, use OPENWEATHERMAP_API_KEY
    return ToolResult(True, {
        "location": location,
        "temperature": "22°C",
        "condition": "Partly cloudy",
        "humidity": "65%",
        "note": "Add OPENWEATHERMAP_KEY to .env for live weather data",
    })


async def send_slack(webhook_url: str, message: str, channel: Optional[str] = None) -> ToolResult:
    """Send a message to Slack via webhook."""
    try:
        payload: dict = {"text": message}
        if channel:
            payload["channel"] = channel

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=payload)
            return ToolResult(response.status_code == 200, {"status": response.text})
    except Exception as e:
        return ToolResult(False, None, str(e))


async def translate(text: str, target_language: str, source_language: str = "auto") -> ToolResult:
    """Translate text (stub — integrate DeepL or Google Translate in production)."""
    return ToolResult(True, {
        "original": text,
        "translated": f"[Translation to {target_language}] {text}",
        "note": "Integrate DeepL or Google Translate API for live translations",
    })


async def extract_entities(text: str) -> ToolResult:
    """Extract named entities (persons, organizations, dates, locations) from text."""
    # Simple regex-based extraction (production: use spaCy or Claude)
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    urls = re.findall(r'https?://[^\s]+', text)
    dates = re.findall(
        r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}-\d{2}-\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4})\b',
        text,
    )
    numbers = re.findall(r'\$[\d,]+(?:\.\d+)?|\d+(?:,\d{3})*(?:\.\d+)?%?', text)

    return ToolResult(True, {
        "emails": emails,
        "urls": urls,
        "dates": dates,
        "numbers": numbers,
    })


# ─────────────────────────────────────────────
# Tool Registry
# ─────────────────────────────────────────────

TOOL_REGISTRY: dict[str, dict] = {
    "web_scrape": {
        "fn": web_scrape,
        "name": "Web Scraper",
        "slug": "web_scrape",
        "description": "Fetch and extract content from any URL — text, links, metadata, or raw HTML.",
        "category": "Web",
        "icon": "🌐",
        "is_builtin": True,
        "requires_auth": False,
        "parameters": {"url": "string (required)", "extract": "text|html|links|metadata"},
    },
    "web_search": {
        "fn": web_search,
        "name": "Web Search",
        "slug": "web_search",
        "description": "Search the web for information using DuckDuckGo. Returns top results with snippets.",
        "category": "Web",
        "icon": "🔍",
        "is_builtin": True,
        "requires_auth": False,
        "parameters": {"query": "string (required)", "num_results": "integer (default 5)"},
    },
    "http_request": {
        "fn": http_request,
        "name": "HTTP Request",
        "slug": "http_request",
        "description": "Make GET/POST/PUT/DELETE requests to any REST API endpoint.",
        "category": "API",
        "icon": "📡",
        "is_builtin": True,
        "requires_auth": False,
        "parameters": {"method": "string", "url": "string", "headers": "dict", "body": "dict", "params": "dict"},
    },
    "parse_pdf": {
        "fn": parse_pdf,
        "name": "PDF Parser",
        "slug": "parse_pdf",
        "description": "Extract text content from PDF documents.",
        "category": "Documents",
        "icon": "📄",
        "is_builtin": True,
        "requires_auth": False,
        "parameters": {"file_path": "string (required)"},
    },
    "parse_docx": {
        "fn": parse_docx,
        "name": "Word Doc Parser",
        "slug": "parse_docx",
        "description": "Extract text from Microsoft Word (.docx) documents.",
        "category": "Documents",
        "icon": "📝",
        "is_builtin": True,
        "requires_auth": False,
        "parameters": {"file_path": "string (required)"},
    },
    "json_query": {
        "fn": json_query,
        "name": "JSON Query",
        "slug": "json_query",
        "description": "Query and extract values from JSON data using dot-notation paths.",
        "category": "Data",
        "icon": "🗄️",
        "is_builtin": True,
        "requires_auth": False,
        "parameters": {"data": "any", "jq_path": "string"},
    },
    "calculator": {
        "fn": calculator,
        "name": "Calculator",
        "slug": "calculator",
        "description": "Safely evaluate mathematical expressions (+, -, *, /, **, %).",
        "category": "Data",
        "icon": "🧮",
        "is_builtin": True,
        "requires_auth": False,
        "parameters": {"expression": "string"},
    },
    "github_repo_info": {
        "fn": github_repo_info,
        "name": "GitHub Info",
        "slug": "github_repo_info",
        "description": "Fetch repository details, stats, and metadata from GitHub.",
        "category": "Integrations",
        "icon": "🐙",
        "is_builtin": True,
        "requires_auth": False,
        "parameters": {"owner": "string", "repo": "string", "token": "string (optional)"},
    },
    "sql_query": {
        "fn": sql_query,
        "name": "SQL Query",
        "slug": "sql_query",
        "description": "Execute read-only SQL SELECT queries against SQLite databases.",
        "category": "Data",
        "icon": "🗃️",
        "is_builtin": True,
        "requires_auth": False,
        "parameters": {"connection_string": "string", "query": "string"},
    },
    "extract_entities": {
        "fn": extract_entities,
        "name": "Entity Extractor",
        "slug": "extract_entities",
        "description": "Extract emails, URLs, dates, and numbers from unstructured text.",
        "category": "NLP",
        "icon": "🏷️",
        "is_builtin": True,
        "requires_auth": False,
        "parameters": {"text": "string"},
    },
    "summarize_text": {
        "fn": summarize_text,
        "name": "Text Summarizer",
        "slug": "summarize_text",
        "description": "Extract the most important sentences from a piece of text.",
        "category": "NLP",
        "icon": "📋",
        "is_builtin": True,
        "requires_auth": False,
        "parameters": {"text": "string", "max_sentences": "integer (default 5)"},
    },
    "translate": {
        "fn": translate,
        "name": "Translator",
        "slug": "translate",
        "description": "Translate text between languages. Integrate DeepL/Google Translate for production.",
        "category": "NLP",
        "icon": "🌍",
        "is_builtin": True,
        "requires_auth": False,
        "parameters": {"text": "string", "target_language": "string", "source_language": "auto"},
    },
    "weather": {
        "fn": weather,
        "name": "Weather",
        "slug": "weather",
        "description": "Get current weather conditions for any location.",
        "category": "Integrations",
        "icon": "🌤️",
        "is_builtin": True,
        "requires_auth": False,
        "parameters": {"location": "string", "units": "metric|imperial"},
    },
    "news_search": {
        "fn": news_search,
        "name": "News Search",
        "slug": "news_search",
        "description": "Search for recent news articles. Add NewsAPI key for live results.",
        "category": "Web",
        "icon": "📰",
        "is_builtin": True,
        "requires_auth": False,
        "parameters": {"query": "string", "category": "string"},
    },
    "send_slack": {
        "fn": send_slack,
        "name": "Slack Message",
        "slug": "send_slack",
        "description": "Send messages to Slack channels via webhook URL.",
        "category": "Integrations",
        "icon": "💬",
        "is_builtin": True,
        "requires_auth": True,
        "parameters": {"webhook_url": "string", "message": "string", "channel": "string (optional)"},
    },
    "github_search_and_rank": {
        "fn": github_search_and_rank,
        "name": "GitHub Repo Ranker",
        "slug": "github_search_and_rank",
        "description": "Search for open-source repositories by skill or topic, then rank them based on stars, forks, and relevance.",
        "category": "Integrations",
        "icon": "📈",
        "is_builtin": True,
        "requires_auth": False,
        "parameters": {"query": "string (required)", "limit": "integer (default 10)"},
    },
}


async def execute_tool(tool_slug: str, params: dict) -> ToolResult:
    """Execute a registered tool by slug with the given parameters."""
    if tool_slug not in TOOL_REGISTRY:
        return ToolResult(False, None, f"Tool '{tool_slug}' not found in registry")

    tool = TOOL_REGISTRY[tool_slug]
    try:
        result = await tool["fn"](**params)
        return result
    except TypeError as e:
        return ToolResult(False, None, f"Invalid parameters for tool '{tool_slug}': {e}")
    except Exception as e:
        return ToolResult(False, None, f"Tool execution failed: {e}")
