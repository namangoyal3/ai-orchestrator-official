"""
Stacks API — curated product-building tool catalog for the Namango CLI.

Opinionated, high-signal catalog. Every tool here is something a builder
would actually choose. Noise removed: no obscure infra, no dead projects.

Powers `namango init` stack recommendations.
"""
from fastapi import APIRouter, Depends
from app.auth import validate_api_key

router = APIRouter(prefix="/v1", tags=["Stacks"])

STACK_CATALOG: dict[str, list[dict]] = {

    # ── Frontend / Web ────────────────────────────────────────────────────────
    "web": [
        {"slug": "nextjs",   "name": "Next.js",     "tier": "free", "monthly_cost_usd": 0, "category": "web", "description": "React framework with SSR, API routes, and App Router. Default choice for most SaaS."},
        {"slug": "react",    "name": "React",        "tier": "free", "monthly_cost_usd": 0, "category": "web", "description": "UI component library. Use with Vite for SPAs, Next.js for full-stack."},
        {"slug": "tailwind", "name": "Tailwind CSS", "tier": "free", "monthly_cost_usd": 0, "category": "web", "description": "Utility-first CSS. Fastest way to build clean UIs without writing custom CSS."},
        {"slug": "shadcn",   "name": "shadcn/ui",    "tier": "free", "monthly_cost_usd": 0, "category": "web", "description": "Copy-paste accessible React components. Pairs with Tailwind + Next.js."},
    ],

    # ── Backend ───────────────────────────────────────────────────────────────
    "backend": [
        {"slug": "fastapi",  "name": "FastAPI",    "tier": "free", "monthly_cost_usd": 0, "category": "backend", "description": "Best Python API framework. Fast, async, auto-docs. Ideal for AI/ML backends."},
        {"slug": "express",  "name": "Express.js", "tier": "free", "monthly_cost_usd": 0, "category": "backend", "description": "Minimal Node.js framework. Good for simple APIs and proxies."},
        {"slug": "nestjs",   "name": "NestJS",     "tier": "free", "monthly_cost_usd": 0, "category": "backend", "description": "Structured TypeScript backend with dependency injection. Great for large teams."},
        {"slug": "hono",     "name": "Hono",       "tier": "free", "monthly_cost_usd": 0, "category": "backend", "description": "Ultra-fast edge-native API framework. Runs on Cloudflare Workers, Vercel Edge."},
    ],

    # ── Database ──────────────────────────────────────────────────────────────
    "database": [
        {"slug": "supabase",   "name": "Supabase",    "tier": "freemium", "monthly_cost_usd": 0,  "category": "database", "description": "Postgres + Auth + Storage + Realtime in one. Best default for new projects."},
        {"slug": "postgresql", "name": "PostgreSQL",  "tier": "free",     "monthly_cost_usd": 0,  "category": "database", "description": "Gold-standard open-source relational DB. Self-host or use Neon/Supabase."},
        {"slug": "neon",       "name": "Neon",        "tier": "freemium", "monthly_cost_usd": 0,  "category": "database", "description": "Serverless Postgres with branching. Great for Railway/Vercel deploys."},
        {"slug": "mongodb",    "name": "MongoDB",     "tier": "freemium", "monthly_cost_usd": 0,  "category": "database", "description": "Flexible document DB. Good for unstructured or rapidly evolving schemas."},
        {"slug": "sqlite",     "name": "SQLite",      "tier": "free",     "monthly_cost_usd": 0,  "category": "database", "description": "Zero-config embedded DB. Perfect for local dev and lightweight apps."},
        {"slug": "prisma",     "name": "Prisma ORM",  "tier": "free",     "monthly_cost_usd": 0,  "category": "database", "description": "Type-safe ORM with migrations and Prisma Studio. Use with any SQL DB."},
        {"slug": "drizzle",    "name": "Drizzle ORM", "tier": "free",     "monthly_cost_usd": 0,  "category": "database", "description": "Lightweight TypeScript ORM. Faster than Prisma, great for edge runtimes."},
    ],

    # ── Auth ──────────────────────────────────────────────────────────────────
    "auth": [
        {"slug": "clerk",         "name": "Clerk",         "tier": "freemium", "monthly_cost_usd": 0,  "category": "auth", "description": "Best-in-class drop-in auth UI for Next.js. Social login, MFA, orgs — zero config."},
        {"slug": "supabase-auth", "name": "Supabase Auth", "tier": "freemium", "monthly_cost_usd": 0,  "category": "auth", "description": "Open-source auth with social login, magic links, and row-level security."},
        {"slug": "nextauth",      "name": "NextAuth.js",   "tier": "free",     "monthly_cost_usd": 0,  "category": "auth", "description": "Auth for Next.js with 50+ OAuth providers. Free and self-hosted."},
        {"slug": "auth0",         "name": "Auth0",         "tier": "freemium", "monthly_cost_usd": 23, "category": "auth", "description": "Enterprise identity platform — OAuth, OIDC, SAML, MFA. Best for B2B SaaS."},
    ],

    # ── Payments ──────────────────────────────────────────────────────────────
    "payments": [
        {"slug": "stripe",       "name": "Stripe",        "tier": "paid", "monthly_cost_usd": 0, "category": "payments", "description": "Default choice for payments. Subscriptions, invoices, Connect, global."},
        {"slug": "lemonsqueezy", "name": "Lemon Squeezy", "tier": "paid", "monthly_cost_usd": 0, "category": "payments", "description": "Merchant of record for indie SaaS. Handles VAT/tax globally. Simpler than Stripe."},
        {"slug": "razorpay",     "name": "Razorpay",      "tier": "paid", "monthly_cost_usd": 0, "category": "payments", "description": "Best for Indian market — UPI, cards, net banking, subscriptions."},
    ],

    # ── AI / LLM ──────────────────────────────────────────────────────────────
    "ai": [
        {"slug": "anthropic",  "name": "Anthropic Claude", "tier": "paid",     "monthly_cost_usd": 15, "category": "ai", "description": "Best for reasoning, long context, and code. Claude 3.5/4 via API."},
        {"slug": "openai",     "name": "OpenAI API",       "tier": "paid",     "monthly_cost_usd": 20, "category": "ai", "description": "GPT-4o, embeddings, vision, Whisper, DALL-E. Widest ecosystem."},
        {"slug": "groq",       "name": "Groq",             "tier": "freemium", "monthly_cost_usd": 0,  "category": "ai", "description": "Fastest LLM inference — Llama 3, Mixtral. Free tier available."},
        {"slug": "ollama",     "name": "Ollama",           "tier": "free",     "monthly_cost_usd": 0,  "category": "ai", "description": "Run LLMs locally — Llama 3, Mistral, Phi. Zero cost, full privacy."},
        {"slug": "openrouter", "name": "OpenRouter",       "tier": "freemium", "monthly_cost_usd": 0,  "category": "ai", "description": "Single API for 100+ models. Route between Claude, GPT, Gemini, Llama."},
        {"slug": "vercel-ai",  "name": "Vercel AI SDK",   "tier": "free",     "monthly_cost_usd": 0,  "category": "ai", "description": "Best SDK for streaming AI responses in Next.js. Provider-agnostic."},
        {"slug": "langchain",  "name": "LangChain",       "tier": "free",     "monthly_cost_usd": 0,  "category": "ai", "description": "LLM chains, agents, RAG pipelines. Largest ecosystem of integrations."},
        {"slug": "pinecone",   "name": "Pinecone",        "tier": "freemium", "monthly_cost_usd": 0,  "category": "ai", "description": "Managed vector DB for RAG and semantic search. Production-ready."},
        {"slug": "qdrant",     "name": "Qdrant",          "tier": "free",     "monthly_cost_usd": 0,  "category": "ai", "description": "Open-source vector DB. Self-hostable alternative to Pinecone."},
    ],

    # ── No-Code Workflow Automation ───────────────────────────────────────────
    "automation": [
        {"slug": "n8n", "use_case_tags": ["workflow", "automation", "no-code", "zapier", "trigger", "visual", "drag-drop", "integration"],          "name": "n8n",          "tier": "free", "monthly_cost_usd": 0, "category": "automation", "github_url": "https://github.com/n8n-io/n8n",              "stars": 182000, "description": "Visual drag-and-drop workflow automation. 400+ integrations, AI nodes, self-hostable. Best Zapier alternative."},
        {"slug": "dify", "use_case_tags": ["llm", "agent", "no-code", "rag", "chatbot", "workflow", "prompt", "ai-app"],         "name": "Dify",         "tier": "free", "monthly_cost_usd": 0, "category": "automation", "github_url": "https://github.com/langgenius/dify",          "stars": 135000, "description": "No-code LLM app and agent builder. RAG, visual workflow, prompt IDE. Production-ready."},
        {"slug": "activepieces", "use_case_tags": ["automation", "workflow", "mcp", "integration", "no-code", "zapier"], "name": "Activepieces", "tier": "free", "monthly_cost_usd": 0, "category": "automation", "github_url": "https://github.com/activepieces/activepieces", "stars": 21500,  "description": "400+ MCP servers + AI workflow automation. Self-hostable TypeScript."},
        {"slug": "automatisch", "use_case_tags": ["automation", "workflow", "zapier", "trigger", "no-code"],  "name": "Automatisch",  "tier": "free", "monthly_cost_usd": 0, "category": "automation", "github_url": "https://github.com/automatisch/automatisch",  "stars": 13700,  "description": "Clean open-source Zapier alternative. Trigger-action automation, no AI bloat."},
    ],

    # ── No-Code App Builders ──────────────────────────────────────────────────
    "no-code-builder": [
        {"slug": "budibase", "use_case_tags": ["no-code", "internal-tool", "dashboard", "crud", "retool", "admin", "visual-builder"],    "name": "Budibase",    "tier": "free", "monthly_cost_usd": 0, "category": "no-code-builder", "github_url": "https://github.com/Budibase/budibase",        "stars": 27800, "description": "No-code internal app builder with AI agents and automations. Open-source Retool."},
        {"slug": "coze-studio", "use_case_tags": ["agent", "no-code", "visual-builder", "chatbot", "ai-studio", "drag-drop"], "name": "Coze Studio", "tier": "free", "monthly_cost_usd": 0, "category": "no-code-builder", "github_url": "https://github.com/coze-dev/coze-studio",     "stars": 20400, "description": "ByteDance's visual AI agent IDE. Build, debug and deploy agents — no code needed."},
        {"slug": "fastgpt", "use_case_tags": ["knowledge-base", "rag", "no-code", "chatbot", "workflow", "mcp"],     "name": "FastGPT",     "tier": "free", "monthly_cost_usd": 0, "category": "no-code-builder", "github_url": "https://github.com/labring/FastGPT",          "stars": 27600, "description": "No-code knowledge base + agent workflow builder. MCP support built-in."},
        {"slug": "pyspur", "use_case_tags": ["agent", "workflow", "visual", "agentic", "no-code", "prototype"],      "name": "PySpur",      "tier": "free", "monthly_cost_usd": 0, "category": "no-code-builder", "github_url": "https://github.com/PySpur-Dev/pyspur",        "stars": 5700,  "description": "Visual playground for agentic workflows. Iterate 10x faster with live feedback."},
        {"slug": "baserow", "use_case_tags": ["no-code", "database", "airtable", "spreadsheet", "automation", "crud"],     "name": "Baserow",     "tier": "free", "monthly_cost_usd": 0, "category": "no-code-builder", "github_url": "https://github.com/baserow/baserow",          "stars": 4500,  "description": "No-code Airtable alternative with database, automations, and AI agents."},
        {"slug": "maxun", "use_case_tags": ["scraping", "web-scraper", "no-code", "data-extraction", "crawling"],       "name": "Maxun",       "tier": "free", "monthly_cost_usd": 0, "category": "no-code-builder", "github_url": "https://github.com/getmaxun/maxun",           "stars": 15300, "description": "No-code web scraping and AI data extraction. Point-and-click scraper builder."},
    ],

    # ── AI Agent Frameworks ───────────────────────────────────────────────────
    "agent-framework": [
        {"slug": "crewai", "use_case_tags": ["agent", "multi-agent", "autonomous", "orchestration", "llm", "agentic"],      "name": "CrewAI",      "tier": "free",     "monthly_cost_usd": 0, "category": "agent-framework", "github_url": "https://github.com/crewAIInc/crewAI",           "stars": 47900, "description": "Most popular agent framework. Role-playing autonomous agents with collaborative intelligence."},
        {"slug": "sim", "use_case_tags": ["agent", "visual", "orchestration", "workflow", "ai-agent", "canvas"],         "name": "Sim Studio",  "tier": "free",     "monthly_cost_usd": 0, "category": "agent-framework", "github_url": "https://github.com/simstudioai/sim",            "stars": 27400, "description": "Visual canvas to build, deploy, and orchestrate AI agent workforces."},
        {"slug": "agentgpt", "use_case_tags": ["agent", "autonomous", "browser", "no-code", "ai-agent"],    "name": "AgentGPT",    "tier": "free",     "monthly_cost_usd": 0, "category": "agent-framework", "github_url": "https://github.com/reworkd/AgentGPT",           "stars": 35900, "description": "Assemble and deploy autonomous AI agents in the browser. No setup needed."},
        {"slug": "haystack", "use_case_tags": ["rag", "llm", "orchestration", "pipeline", "search", "agent"],    "name": "Haystack",    "tier": "free",     "monthly_cost_usd": 0, "category": "agent-framework", "github_url": "https://github.com/deepset-ai/haystack",        "stars": 24700, "description": "Production-ready LLM orchestration framework for RAG, agents, and pipelines."},
        {"slug": "skyvern", "use_case_tags": ["browser-automation", "agent", "web", "vision", "scraping", "workflow"],     "name": "Skyvern",     "tier": "free",     "monthly_cost_usd": 0, "category": "agent-framework", "github_url": "https://github.com/Skyvern-AI/skyvern",         "stars": 21000, "description": "AI browser automation. Automate any web workflow with vision + LLMs."},
        {"slug": "superagi", "use_case_tags": ["agent", "autonomous", "agentic", "framework", "ai-agent"],    "name": "SuperAGI",    "tier": "free",     "monthly_cost_usd": 0, "category": "agent-framework", "github_url": "https://github.com/TransformerOptimus/SuperAGI", "stars": 17400, "description": "Dev-first autonomous AI agent framework. Build, manage, and run production agents."},
        {"slug": "trigger-dev", "use_case_tags": ["background-jobs", "workflow", "automation", "agent", "scheduling"], "name": "Trigger.dev", "tier": "freemium", "monthly_cost_usd": 0, "category": "agent-framework", "github_url": "https://github.com/triggerdotdev/trigger.dev",  "stars": 14300, "description": "Build and deploy fully-managed AI agents and background jobs. Cloud or self-hosted."},
        {"slug": "agent-squad", "use_case_tags": ["agent", "multi-agent", "conversation", "aws", "orchestration"], "name": "Agent Squad", "tier": "free",     "monthly_cost_usd": 0, "category": "agent-framework", "github_url": "https://github.com/awslabs/agent-squad",        "stars": 7600,  "description": "AWS open-source framework for multi-agent systems and complex conversations."},
    ],

    # ── MCP Ecosystem ─────────────────────────────────────────────────────────
    "mcp": [
        {"slug": "fastapi-mcp", "use_case_tags": ["mcp", "api", "tool-calling", "fastapi", "integration"],    "name": "FastAPI MCP",    "tier": "free", "monthly_cost_usd": 0, "category": "mcp", "github_url": "https://github.com/tadata-org/fastapi_mcp",          "stars": 11700, "description": "Expose any FastAPI endpoint as an MCP tool instantly. With auth."},
        {"slug": "mcp-agent", "use_case_tags": ["mcp", "agent", "workflow", "tool-calling"],      "name": "MCP Agent",      "tier": "free", "monthly_cost_usd": 0, "category": "mcp", "github_url": "https://github.com/lastmile-ai/mcp-agent",           "stars": 8200,  "description": "Build effective agents using MCP and simple workflow patterns."},
        {"slug": "mcp-go", "use_case_tags": ["mcp", "go", "server", "tool-calling"],         "name": "MCP Go",         "tier": "free", "monthly_cost_usd": 0, "category": "mcp", "github_url": "https://github.com/mark3labs/mcp-go",                 "stars": 8500,  "description": "Go SDK for MCP — build high-performance MCP servers in Go."},
        {"slug": "mcp-registry", "use_case_tags": ["mcp", "registry", "servers", "marketplace"],   "name": "MCP Registry",   "tier": "free", "monthly_cost_usd": 0, "category": "mcp", "github_url": "https://github.com/modelcontextprotocol/registry",    "stars": 6600,  "description": "Official community-driven registry of MCP servers."},
        {"slug": "mcp-playwright", "use_case_tags": ["mcp", "browser", "automation", "testing", "playwright"], "name": "MCP Playwright", "tier": "free", "monthly_cost_usd": 0, "category": "mcp", "github_url": "https://github.com/executeautomation/mcp-playwright", "stars": 5400,  "description": "Playwright MCP server — give agents full browser automation capabilities."},
    ],

    # ── Deploy / Hosting ──────────────────────────────────────────────────────
    "deploy": [
        {"slug": "vercel",  "name": "Vercel",  "tier": "freemium", "monthly_cost_usd": 0,  "category": "deploy", "description": "Best for Next.js. Auto-deploys, edge functions, preview URLs. Generous free tier."},
        {"slug": "railway", "name": "Railway", "tier": "freemium", "monthly_cost_usd": 5,  "category": "deploy", "description": "Deploy anything with Git push. Databases, workers, cron — all in one. $5/mo hobby."},
        {"slug": "render",  "name": "Render",  "tier": "freemium", "monthly_cost_usd": 7,  "category": "deploy", "description": "Full-stack cloud — web services, workers, cron, managed DB. Heroku replacement."},
        {"slug": "fly",     "name": "Fly.io",  "tier": "freemium", "monthly_cost_usd": 0,  "category": "deploy", "description": "Run Docker containers globally at the edge. Best for latency-sensitive apps."},
        {"slug": "docker",  "name": "Docker",  "tier": "free",     "monthly_cost_usd": 0,  "category": "deploy", "description": "Container packaging for consistent environments. Foundation for all cloud deploy."},
    ],

    # ── Email ─────────────────────────────────────────────────────────────────
    "email": [
        {"slug": "resend",   "name": "Resend",   "tier": "freemium", "monthly_cost_usd": 0,  "category": "email", "description": "Best developer email API. React Email templates, 3K emails/mo free."},
        {"slug": "sendgrid", "name": "SendGrid", "tier": "freemium", "monthly_cost_usd": 0,  "category": "email", "description": "Reliable transactional email. 100/day free. Good for high volume."},
        {"slug": "mailgun",  "name": "Mailgun",  "tier": "freemium", "monthly_cost_usd": 0,  "category": "email", "description": "Email API with advanced analytics, logging, and inbound email parsing."},
    ],

    # ── Storage ───────────────────────────────────────────────────────────────
    "storage": [
        {"slug": "r2",               "name": "Cloudflare R2",    "tier": "freemium", "monthly_cost_usd": 0, "category": "storage", "description": "Zero-egress S3-compatible object storage. Cheapest for high-bandwidth apps."},
        {"slug": "supabase-storage", "name": "Supabase Storage", "tier": "freemium", "monthly_cost_usd": 0, "category": "storage", "description": "S3-compatible storage with Postgres row-level security. Great with Supabase DB."},
        {"slug": "cloudinary",       "name": "Cloudinary",       "tier": "freemium", "monthly_cost_usd": 0, "category": "storage", "description": "Image and video CDN with transforms, optimization, and AI tagging."},
        {"slug": "s3",               "name": "AWS S3",           "tier": "paid",     "monthly_cost_usd": 2, "category": "storage", "description": "Gold standard object storage. Use for AWS-native stacks or compliance needs."},
    ],

    # ── Monitoring / Analytics ────────────────────────────────────────────────
    "monitoring": [
        {"slug": "sentry",  "name": "Sentry",  "tier": "freemium", "monthly_cost_usd": 0,  "category": "monitoring", "description": "Error tracking and performance monitoring. First tool to add to any production app."},
        {"slug": "posthog", "name": "PostHog", "tier": "freemium", "monthly_cost_usd": 0,  "category": "monitoring", "description": "Open-source product analytics, feature flags, session replay, A/B testing."},
        {"slug": "grafana", "name": "Grafana", "tier": "freemium", "monthly_cost_usd": 0,  "category": "monitoring", "description": "Open-source metrics and log visualization. Connect to any data source."},
        {"slug": "datadog", "name": "Datadog", "tier": "paid",     "monthly_cost_usd": 31, "category": "monitoring", "description": "Full-stack observability — APM, metrics, logs, synthetics. Enterprise choice."},
    ],

    # ── Realtime ──────────────────────────────────────────────────────────────
    "realtime": [
        {"slug": "socket-io", "name": "Socket.IO", "tier": "free",     "monthly_cost_usd": 0, "category": "realtime", "description": "WebSocket library with rooms and namespaces. Most used realtime lib for Node.js."},
        {"slug": "pusher",    "name": "Pusher",    "tier": "freemium", "monthly_cost_usd": 0, "category": "realtime", "description": "Hosted WebSocket channels. 200k messages/day free. Zero infra management."},
        {"slug": "ably",      "name": "Ably",      "tier": "freemium", "monthly_cost_usd": 0, "category": "realtime", "description": "Realtime pub/sub at scale. Better SLA and global edge than Pusher."},
    ],
}


@router.get("/stacks", summary="Get curated product-building stack catalog")
async def get_stacks():
    """
    Namango's curated catalog of real product-building tools organized by
    category. Every tool here is something a builder would actually choose.

    Powers the `namango init` CLI command's stack recommendation engine.
    """
    all_tools = []
    for tools in STACK_CATALOG.values():
        all_tools.extend(tools)

    return {
        "categories": STACK_CATALOG,
        "total": len(all_tools),
        "category_count": len(STACK_CATALOG),
    }
