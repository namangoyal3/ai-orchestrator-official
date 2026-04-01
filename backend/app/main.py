"""
AI Gateway Orchestrator — Main FastAPI Application
"""
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import init_db
from app.api import gateway, agents, tools, keys, analytics, marketplace, architect, stacks
from app.seed import seed_database
from app.scraper import RepoScraper

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await seed_database()

    # Start background scraper scheduler
    try:
        scraper = RepoScraper()
        # Schedule scraping every hour
        scheduler.add_job(
            scraper.scrape_and_store,
            'interval',
            hours=1,
            id='repo-scraper',
            name='Hourly Repository Scraper',
            misfire_grace_time=600  # 10 minute grace period
        )
        scheduler.start()
        logger.info("✓ Repository scraper scheduled to run every hour")
    except Exception as e:
        logger.error(f"Failed to start scraper scheduler: {e}")
    
    yield

    # Shutdown
    if scheduler.running:
        scheduler.shutdown()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
## AI Gateway Orchestrator

A universal AI infrastructure layer that automatically:

- 🧠 **Selects the optimal LLM** (Claude Opus, Sonnet, Haiku, GPT-4, Gemini) based on task complexity
- 🤖 **Orchestrates specialized agents** (Research, Code, Data Analysis, Document Q&A, and more)
- 🔧 **Executes pre-built tools** (web search, URL scraping, PDF parsing, APIs, databases)
- 📄 **Extracts context** from any URL or document automatically
- 📊 **Tracks usage, costs, and performance** with full analytics

### Quick Start

1. Create an organization: `POST /admin/organizations`
2. Generate an API key: `POST /admin/api-keys`
3. Submit any task: `POST /v1/query` with `X-API-Key: your-key`

The gateway handles everything else automatically.
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global error handler — log internally, never expose detail to clients
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import logging
    logging.getLogger("uvicorn.error").exception(
        "Unhandled exception for %s %s", request.method, request.url.path
    )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


# Health check
@app.get("/health", tags=["System"])
async def health():
    return {
        "status": "healthy",
        "version": settings.app_version,
        "app": settings.app_name,
    }


# Root info
@app.get("/", tags=["System"])
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "query": "POST /v1/query",
            "agents": "GET /v1/agents",
            "tools": "GET /v1/tools",
            "analytics": "GET /v1/analytics/summary",
            "models": "GET /v1/models",
        },
    }


# Register routers
app.include_router(gateway.router)
app.include_router(agents.router)
app.include_router(tools.router)
app.include_router(analytics.router)
app.include_router(keys.router)
app.include_router(marketplace.router)
app.include_router(architect.router, prefix="/v1/architect", tags=["architect"])
app.include_router(stacks.router)
