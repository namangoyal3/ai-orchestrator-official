"""
Stacks API — curated product-building tool catalog for the Namango CLI.

Returns real frameworks, databases, SaaS APIs, and infra tools organized
by category. This powers the CLI's stack recommendation engine so developers
get an opinionated, curated recommendation instead of generic LLM output.

Unlike /v1/marketplace (which lists MCP agent servers), /v1/stacks lists
the tools a developer would actually install when building a product.
"""
from fastapi import APIRouter, Depends
from app.auth import validate_api_key

router = APIRouter(prefix="/v1", tags=["Stacks"])

# ── Curated Stack Catalog ─────────────────────────────────────────────────────
# This is Namango's opinionated catalog of production-grade tools.
# The CLI embeds the same data as a fallback, so keep both in sync.

STACK_CATALOG: dict[str, list[dict]] = {
    "web": [
        {"slug": "fastapi",  "name": "FastAPI",    "description": "High-performance async Python web framework",   "tier": "free",     "monthly_cost_usd": 0,  "category": "web"},
        {"slug": "django",   "name": "Django",     "description": "Batteries-included Python web framework",        "tier": "free",     "monthly_cost_usd": 0,  "category": "web"},
        {"slug": "express",  "name": "Express.js", "description": "Minimal, flexible Node.js web framework",        "tier": "free",     "monthly_cost_usd": 0,  "category": "web"},
        {"slug": "nextjs",   "name": "Next.js",    "description": "React framework with SSR and API routes",        "tier": "free",     "monthly_cost_usd": 0,  "category": "web"},
        {"slug": "flask",    "name": "Flask",      "description": "Lightweight Python web microframework",          "tier": "free",     "monthly_cost_usd": 0,  "category": "web"},
    ],
    "database": [
        {"slug": "postgresql",  "name": "PostgreSQL",  "description": "Reliable open-source relational database",           "tier": "free",     "monthly_cost_usd": 0,  "category": "database"},
        {"slug": "mongodb",     "name": "MongoDB",     "description": "Flexible NoSQL document database",                    "tier": "freemium", "monthly_cost_usd": 0,  "category": "database"},
        {"slug": "sqlite",      "name": "SQLite",      "description": "Zero-config embedded SQL, perfect for prototyping",   "tier": "free",     "monthly_cost_usd": 0,  "category": "database"},
        {"slug": "supabase",    "name": "Supabase",    "description": "Open-source Firebase with Postgres + Auth + Storage", "tier": "freemium", "monthly_cost_usd": 0,  "category": "database"},
        {"slug": "planetscale", "name": "PlanetScale", "description": "Serverless MySQL with branching for safe migrations", "tier": "freemium", "monthly_cost_usd": 0,  "category": "database"},
    ],
    "cache": [
        {"slug": "redis",   "name": "Redis",        "description": "In-memory cache, sessions, pub/sub messaging",  "tier": "free",     "monthly_cost_usd": 0, "category": "cache"},
        {"slug": "upstash", "name": "Upstash Redis", "description": "Serverless Redis, pay-per-request pricing",   "tier": "freemium", "monthly_cost_usd": 0, "category": "cache"},
    ],
    "queue": [
        {"slug": "celery",    "name": "Celery",    "description": "Distributed task queue for Python with Redis/RabbitMQ", "tier": "free",     "monthly_cost_usd": 0, "category": "queue"},
        {"slug": "bullmq",    "name": "BullMQ",    "description": "Redis-backed job queue for Node.js",                    "tier": "free",     "monthly_cost_usd": 0, "category": "queue"},
        {"slug": "inngest",   "name": "Inngest",   "description": "Event-driven serverless background jobs",                "tier": "freemium", "monthly_cost_usd": 0, "category": "queue"},
        {"slug": "rabbitmq",  "name": "RabbitMQ",  "description": "Message broker for distributed systems",                "tier": "free",     "monthly_cost_usd": 0, "category": "queue"},
    ],
    "auth": [
        {"slug": "jwt",           "name": "JWT",           "description": "Stateless token-based auth — zero infra",          "tier": "free",     "monthly_cost_usd": 0,  "category": "auth"},
        {"slug": "auth0",         "name": "Auth0",         "description": "Identity platform with OAuth, OIDC, SAML, MFA",    "tier": "freemium", "monthly_cost_usd": 23, "category": "auth"},
        {"slug": "supabase-auth", "name": "Supabase Auth", "description": "Open-source auth with social login and RLS",       "tier": "freemium", "monthly_cost_usd": 0,  "category": "auth"},
        {"slug": "clerk",         "name": "Clerk",         "description": "Drop-in auth UI components for React/Next.js",     "tier": "freemium", "monthly_cost_usd": 0,  "category": "auth"},
        {"slug": "nextauth",      "name": "NextAuth.js",   "description": "Auth for Next.js with 50+ OAuth providers",        "tier": "free",     "monthly_cost_usd": 0,  "category": "auth"},
    ],
    "payments": [
        {"slug": "stripe",       "name": "Stripe",        "description": "Payments, subscriptions, invoices, Connect",       "tier": "paid", "monthly_cost_usd": 0, "category": "payments"},
        {"slug": "razorpay",     "name": "Razorpay",      "description": "Indian payments — UPI, cards, net banking, EMI",   "tier": "paid", "monthly_cost_usd": 0, "category": "payments"},
        {"slug": "paddle",       "name": "Paddle",        "description": "Merchant of record — handles global tax/VAT",      "tier": "paid", "monthly_cost_usd": 0, "category": "payments"},
        {"slug": "lemonsqueezy", "name": "Lemon Squeezy", "description": "Payments and subscriptions for indie SaaS",        "tier": "paid", "monthly_cost_usd": 0, "category": "payments"},
    ],
    "email": [
        {"slug": "sendgrid", "name": "SendGrid", "description": "Transactional email API by Twilio, 100/day free",    "tier": "freemium", "monthly_cost_usd": 0,  "category": "email"},
        {"slug": "resend",   "name": "Resend",   "description": "Developer-first email with React Email templates",   "tier": "freemium", "monthly_cost_usd": 0,  "category": "email"},
        {"slug": "postmark", "name": "Postmark", "description": "Best deliverability for transactional email",        "tier": "paid",     "monthly_cost_usd": 15, "category": "email"},
        {"slug": "mailgun",  "name": "Mailgun",  "description": "Email API with advanced analytics and logging",      "tier": "freemium", "monthly_cost_usd": 0,  "category": "email"},
    ],
    "notifications": [
        {"slug": "twilio",        "name": "Twilio",        "description": "SMS, WhatsApp, and voice notifications API",      "tier": "paid",     "monthly_cost_usd": 0, "category": "notifications"},
        {"slug": "firebase-fcm",  "name": "Firebase FCM",  "description": "Free push notifications for iOS, Android, web",  "tier": "freemium", "monthly_cost_usd": 0, "category": "notifications"},
        {"slug": "onesignal",     "name": "OneSignal",     "description": "Push, email, SMS, in-app all-in-one",             "tier": "freemium", "monthly_cost_usd": 0, "category": "notifications"},
    ],
    "deploy": [
        {"slug": "railway", "name": "Railway",  "description": "Deploy anything with Git push, $5/mo hobby",          "tier": "freemium", "monthly_cost_usd": 5, "category": "deploy"},
        {"slug": "vercel",  "name": "Vercel",   "description": "Frontend + serverless, generous free tier",            "tier": "freemium", "monthly_cost_usd": 0, "category": "deploy"},
        {"slug": "render",  "name": "Render",   "description": "Full-stack cloud — web, workers, cron, DB",            "tier": "freemium", "monthly_cost_usd": 7, "category": "deploy"},
        {"slug": "fly",     "name": "Fly.io",   "description": "Run Docker apps globally with edge deployment",        "tier": "freemium", "monthly_cost_usd": 0, "category": "deploy"},
        {"slug": "docker",  "name": "Docker",   "description": "Container packaging and local development runtime",    "tier": "free",     "monthly_cost_usd": 0, "category": "deploy"},
    ],
    "ai": [
        {"slug": "openai",    "name": "OpenAI API",       "description": "GPT-4o, embeddings, vision, Whisper speech",  "tier": "paid",     "monthly_cost_usd": 20, "category": "ai"},
        {"slug": "anthropic", "name": "Anthropic Claude", "description": "Claude 3.5 — long context, reasoning, code",  "tier": "paid",     "monthly_cost_usd": 15, "category": "ai"},
        {"slug": "groq",      "name": "Groq",             "description": "Ultra-fast inference — Llama3, Mixtral free", "tier": "freemium", "monthly_cost_usd": 0,  "category": "ai"},
        {"slug": "ollama",    "name": "Ollama",           "description": "Run LLMs locally — Llama3, Mistral, Phi3",    "tier": "free",     "monthly_cost_usd": 0,  "category": "ai"},
        {"slug": "langchain", "name": "LangChain",        "description": "LLM application framework and LCEL pipelines", "tier": "free",     "monthly_cost_usd": 0,  "category": "ai"},
        {"slug": "pinecone",  "name": "Pinecone",         "description": "Managed vector DB for semantic search/RAG",   "tier": "freemium", "monthly_cost_usd": 0,  "category": "ai"},
    ],
    "storage": [
        {"slug": "s3",                "name": "AWS S3",            "description": "Object storage for files, media, backups",        "tier": "paid",     "monthly_cost_usd": 2, "category": "storage"},
        {"slug": "cloudinary",        "name": "Cloudinary",        "description": "Image/video transform, optimization, CDN",        "tier": "freemium", "monthly_cost_usd": 0, "category": "storage"},
        {"slug": "supabase-storage",  "name": "Supabase Storage",  "description": "S3-compatible storage with row-level access",     "tier": "freemium", "monthly_cost_usd": 0, "category": "storage"},
        {"slug": "r2",                "name": "Cloudflare R2",     "description": "Zero-egress S3-compatible object storage",        "tier": "freemium", "monthly_cost_usd": 0, "category": "storage"},
    ],
    "monitoring": [
        {"slug": "sentry",   "name": "Sentry",   "description": "Error tracking, performance monitoring, session replay", "tier": "freemium", "monthly_cost_usd": 0,  "category": "monitoring"},
        {"slug": "posthog",  "name": "PostHog",  "description": "Open-source analytics, feature flags, A/B tests",       "tier": "freemium", "monthly_cost_usd": 0,  "category": "monitoring"},
        {"slug": "datadog",  "name": "Datadog",  "description": "Full-stack observability — metrics, APM, logs",          "tier": "paid",     "monthly_cost_usd": 31, "category": "monitoring"},
        {"slug": "grafana",  "name": "Grafana",  "description": "Open-source metrics and log visualization dashboards",   "tier": "freemium", "monthly_cost_usd": 0,  "category": "monitoring"},
    ],
    "search": [
        {"slug": "elasticsearch", "name": "Elasticsearch", "description": "Distributed full-text search and analytics", "tier": "freemium", "monthly_cost_usd": 0, "category": "search"},
        {"slug": "algolia",       "name": "Algolia",       "description": "Search as a service — instant, typo-tolerant", "tier": "freemium", "monthly_cost_usd": 0, "category": "search"},
        {"slug": "typesense",     "name": "Typesense",     "description": "Open-source instant search, self-hostable",  "tier": "free",     "monthly_cost_usd": 0, "category": "search"},
    ],
    "realtime": [
        {"slug": "websockets", "name": "WebSockets",    "description": "Native real-time bidirectional communication",  "tier": "free",     "monthly_cost_usd": 0, "category": "realtime"},
        {"slug": "pusher",     "name": "Pusher",        "description": "Hosted WebSocket service, 200k msgs/day free",  "tier": "freemium", "monthly_cost_usd": 0, "category": "realtime"},
        {"slug": "ably",       "name": "Ably",          "description": "Realtime pub/sub messaging at scale",           "tier": "freemium", "monthly_cost_usd": 0, "category": "realtime"},
        {"slug": "socket-io",  "name": "Socket.IO",     "description": "WebSocket library with rooms and namespaces",  "tier": "free",     "monthly_cost_usd": 0, "category": "realtime"},
    ],
}


@router.get("/stacks", summary="Get curated product-building stack catalog")
async def get_stacks(_: str = Depends(validate_api_key)):
    """
    Namango's curated catalog of real product-building tools organized by
    category (web, database, auth, payments, deploy, ai, etc.).

    Unlike /v1/marketplace (MCP agent servers), /v1/stacks lists the tools
    a developer would actually install and use when building a product.

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
