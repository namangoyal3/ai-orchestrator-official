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
        {"slug": "fastapi",   "name": "FastAPI",     "description": "High-performance async Python web framework",    "tier": "free",     "monthly_cost_usd": 0, "category": "web"},
        {"slug": "django",    "name": "Django",      "description": "Batteries-included Python web framework",         "tier": "free",     "monthly_cost_usd": 0, "category": "web"},
        {"slug": "express",   "name": "Express.js",  "description": "Minimal, flexible Node.js web framework",         "tier": "free",     "monthly_cost_usd": 0, "category": "web"},
        {"slug": "nextjs",    "name": "Next.js",     "description": "React framework with SSR, API routes, and Edge",  "tier": "free",     "monthly_cost_usd": 0, "category": "web"},
        {"slug": "flask",     "name": "Flask",       "description": "Lightweight Python web microframework",           "tier": "free",     "monthly_cost_usd": 0, "category": "web"},
        {"slug": "nuxt",      "name": "Nuxt.js",     "description": "Vue.js framework with SSR and full-stack support","tier": "free",     "monthly_cost_usd": 0, "category": "web"},
        {"slug": "nestjs",    "name": "NestJS",      "description": "TypeScript Node.js framework for scalable APIs",  "tier": "free",     "monthly_cost_usd": 0, "category": "web"},
        {"slug": "hono",      "name": "Hono",        "description": "Ultra-fast web framework for edge runtimes",      "tier": "free",     "monthly_cost_usd": 0, "category": "web"},
        {"slug": "trpc",      "name": "tRPC",        "description": "End-to-end type-safe APIs without schemas",       "tier": "free",     "monthly_cost_usd": 0, "category": "web"},
        {"slug": "astro",     "name": "Astro",       "description": "Static site builder with island architecture",    "tier": "free",     "monthly_cost_usd": 0, "category": "web"},
        {"slug": "react",     "name": "React",       "description": "UI library for building component-based frontends","tier": "free",     "monthly_cost_usd": 0, "category": "web"},
        {"slug": "tailwind",  "name": "Tailwind CSS","description": "Utility-first CSS framework, pairs with any JS framework","tier": "free","monthly_cost_usd": 0,"category": "web"},
        {"slug": "shadcn",    "name": "shadcn/ui",   "description": "Copy-paste accessible React components built on Radix","tier": "free","monthly_cost_usd": 0,"category": "web"},
        {"slug": "vite",      "name": "Vite",        "description": "Fast frontend build tool and dev server for React/Vue","tier": "free","monthly_cost_usd": 0,"category": "web"},
    ],
    "database": [
        {"slug": "postgresql",  "name": "PostgreSQL",   "description": "Reliable open-source relational database",            "tier": "free",     "monthly_cost_usd": 0,  "category": "database"},
        {"slug": "mongodb",     "name": "MongoDB",      "description": "Flexible NoSQL document database",                     "tier": "freemium", "monthly_cost_usd": 0,  "category": "database"},
        {"slug": "sqlite",      "name": "SQLite",       "description": "Zero-config embedded SQL, perfect for prototyping",    "tier": "free",     "monthly_cost_usd": 0,  "category": "database"},
        {"slug": "supabase",    "name": "Supabase",     "description": "Open-source Firebase with Postgres + Auth + Storage",  "tier": "freemium", "monthly_cost_usd": 0,  "category": "database"},
        {"slug": "planetscale", "name": "PlanetScale",  "description": "Serverless MySQL with branching for safe migrations",  "tier": "freemium", "monthly_cost_usd": 0,  "category": "database"},
        {"slug": "neon",        "name": "Neon",         "description": "Serverless Postgres with auto-scaling and branching",  "tier": "freemium", "monthly_cost_usd": 0,  "category": "database"},
        {"slug": "turso",       "name": "Turso",        "description": "Edge SQLite database with global replication",         "tier": "freemium", "monthly_cost_usd": 0,  "category": "database"},
        {"slug": "prisma",      "name": "Prisma",       "description": "Type-safe ORM with migrations and Prisma Studio",      "tier": "free",     "monthly_cost_usd": 0,  "category": "database"},
        {"slug": "drizzle",     "name": "Drizzle ORM",  "description": "Lightweight TypeScript ORM with SQL-like syntax",      "tier": "free",     "monthly_cost_usd": 0,  "category": "database"},
        {"slug": "dynamodb",    "name": "DynamoDB",     "description": "AWS managed NoSQL with single-digit ms latency",       "tier": "paid",     "monthly_cost_usd": 0,  "category": "database"},
    ],
    "cache": [
        {"slug": "redis",      "name": "Redis",         "description": "In-memory cache, sessions, pub/sub messaging",         "tier": "free",     "monthly_cost_usd": 0, "category": "cache"},
        {"slug": "upstash",    "name": "Upstash Redis", "description": "Serverless Redis, pay-per-request pricing",            "tier": "freemium", "monthly_cost_usd": 0, "category": "cache"},
        {"slug": "memcached",  "name": "Memcached",     "description": "Simple, fast distributed memory caching",              "tier": "free",     "monthly_cost_usd": 0, "category": "cache"},
        {"slug": "keydb",      "name": "KeyDB",         "description": "Multi-threaded Redis drop-in with 5x throughput",      "tier": "free",     "monthly_cost_usd": 0, "category": "cache"},
        {"slug": "dragonfly",  "name": "Dragonfly",     "description": "25x faster Redis-compatible in-memory store",          "tier": "free",     "monthly_cost_usd": 0, "category": "cache"},
    ],
    "queue": [
        {"slug": "celery",   "name": "Celery",    "description": "Distributed task queue for Python with Redis/RabbitMQ",     "tier": "free",     "monthly_cost_usd": 0, "category": "queue"},
        {"slug": "bullmq",   "name": "BullMQ",    "description": "Redis-backed job queue for Node.js with retries",           "tier": "free",     "monthly_cost_usd": 0, "category": "queue"},
        {"slug": "inngest",  "name": "Inngest",   "description": "Event-driven serverless background jobs",                   "tier": "freemium", "monthly_cost_usd": 0, "category": "queue"},
        {"slug": "rabbitmq", "name": "RabbitMQ",  "description": "Message broker for distributed systems",                    "tier": "free",     "monthly_cost_usd": 0, "category": "queue"},
        {"slug": "kafka",    "name": "Apache Kafka","description": "High-throughput distributed event streaming platform",    "tier": "free",     "monthly_cost_usd": 0, "category": "queue"},
        {"slug": "sqs",      "name": "AWS SQS",   "description": "Fully managed message queuing service by AWS",              "tier": "paid",     "monthly_cost_usd": 0, "category": "queue"},
        {"slug": "temporal", "name": "Temporal",  "description": "Durable workflow engine for long-running processes",        "tier": "freemium", "monthly_cost_usd": 0, "category": "queue"},
    ],
    "auth": [
        {"slug": "jwt",           "name": "JWT",            "description": "Stateless token-based auth — zero infra",           "tier": "free",     "monthly_cost_usd": 0,  "category": "auth"},
        {"slug": "auth0",         "name": "Auth0",          "description": "Identity platform with OAuth, OIDC, SAML, MFA",     "tier": "freemium", "monthly_cost_usd": 23, "category": "auth"},
        {"slug": "supabase-auth", "name": "Supabase Auth",  "description": "Open-source auth with social login and RLS",        "tier": "freemium", "monthly_cost_usd": 0,  "category": "auth"},
        {"slug": "clerk",         "name": "Clerk",          "description": "Drop-in auth UI components for React/Next.js",      "tier": "freemium", "monthly_cost_usd": 0,  "category": "auth"},
        {"slug": "nextauth",      "name": "NextAuth.js",    "description": "Auth for Next.js with 50+ OAuth providers",         "tier": "free",     "monthly_cost_usd": 0,  "category": "auth"},
        {"slug": "lucia",         "name": "Lucia",          "description": "Lightweight, framework-agnostic auth library",      "tier": "free",     "monthly_cost_usd": 0,  "category": "auth"},
        {"slug": "passport",      "name": "Passport.js",    "description": "Authentication middleware for Node.js, 500+ strategies","tier": "free", "monthly_cost_usd": 0,  "category": "auth"},
        {"slug": "better-auth",   "name": "Better Auth",    "description": "TypeScript-first auth library with plugins system",  "tier": "free",     "monthly_cost_usd": 0,  "category": "auth"},
    ],
    "payments": [
        {"slug": "stripe",       "name": "Stripe",        "description": "Payments, subscriptions, invoices, Connect",          "tier": "paid", "monthly_cost_usd": 0, "category": "payments"},
        {"slug": "razorpay",     "name": "Razorpay",      "description": "Indian payments — UPI, cards, net banking, EMI",      "tier": "paid", "monthly_cost_usd": 0, "category": "payments"},
        {"slug": "paddle",       "name": "Paddle",        "description": "Merchant of record — handles global tax/VAT",         "tier": "paid", "monthly_cost_usd": 0, "category": "payments"},
        {"slug": "lemonsqueezy", "name": "Lemon Squeezy", "description": "Payments and subscriptions for indie SaaS",           "tier": "paid", "monthly_cost_usd": 0, "category": "payments"},
        {"slug": "paypal",       "name": "PayPal",        "description": "Global payments with PayPal and Venmo",               "tier": "paid", "monthly_cost_usd": 0, "category": "payments"},
        {"slug": "braintree",    "name": "Braintree",     "description": "PayPal-owned SDK for cards, PayPal, Venmo, crypto",   "tier": "paid", "monthly_cost_usd": 0, "category": "payments"},
    ],
    "email": [
        {"slug": "sendgrid",    "name": "SendGrid",       "description": "Transactional email API by Twilio, 100/day free",     "tier": "freemium", "monthly_cost_usd": 0,  "category": "email"},
        {"slug": "resend",      "name": "Resend",         "description": "Developer-first email with React Email templates",    "tier": "freemium", "monthly_cost_usd": 0,  "category": "email"},
        {"slug": "postmark",    "name": "Postmark",       "description": "Best deliverability for transactional email",         "tier": "paid",     "monthly_cost_usd": 15, "category": "email"},
        {"slug": "mailgun",     "name": "Mailgun",        "description": "Email API with advanced analytics and logging",       "tier": "freemium", "monthly_cost_usd": 0,  "category": "email"},
        {"slug": "ses",         "name": "AWS SES",        "description": "Scalable cloud email service, $0.10 per 1000 emails", "tier": "paid",     "monthly_cost_usd": 0,  "category": "email"},
        {"slug": "loops",       "name": "Loops",          "description": "Email platform built for SaaS product emails",        "tier": "freemium", "monthly_cost_usd": 0,  "category": "email"},
        {"slug": "react-email", "name": "React Email",    "description": "Build responsive HTML emails with React components",  "tier": "free",     "monthly_cost_usd": 0,  "category": "email"},
    ],
    "notifications": [
        {"slug": "twilio",       "name": "Twilio",        "description": "SMS, WhatsApp, and voice notifications API",           "tier": "paid",     "monthly_cost_usd": 0, "category": "notifications"},
        {"slug": "firebase-fcm", "name": "Firebase FCM",  "description": "Free push notifications for iOS, Android, web",       "tier": "freemium", "monthly_cost_usd": 0, "category": "notifications"},
        {"slug": "onesignal",    "name": "OneSignal",     "description": "Push, email, SMS, in-app — all in one platform",      "tier": "freemium", "monthly_cost_usd": 0, "category": "notifications"},
        {"slug": "novu",         "name": "Novu",          "description": "Open-source notification infrastructure for devs",    "tier": "freemium", "monthly_cost_usd": 0, "category": "notifications"},
        {"slug": "knock",        "name": "Knock",         "description": "Notification infrastructure with workflow engine",    "tier": "freemium", "monthly_cost_usd": 0, "category": "notifications"},
    ],
    "deploy": [
        {"slug": "railway",     "name": "Railway",       "description": "Deploy anything with Git push, $5/mo hobby tier",      "tier": "freemium", "monthly_cost_usd": 5,  "category": "deploy"},
        {"slug": "vercel",      "name": "Vercel",        "description": "Frontend + serverless functions, generous free tier",   "tier": "freemium", "monthly_cost_usd": 0,  "category": "deploy"},
        {"slug": "render",      "name": "Render",        "description": "Full-stack cloud — web services, workers, cron, DB",   "tier": "freemium", "monthly_cost_usd": 7,  "category": "deploy"},
        {"slug": "fly",         "name": "Fly.io",        "description": "Run Docker apps globally with edge deployment",         "tier": "freemium", "monthly_cost_usd": 0,  "category": "deploy"},
        {"slug": "docker",      "name": "Docker",        "description": "Container packaging and local development runtime",     "tier": "free",     "monthly_cost_usd": 0,  "category": "deploy"},
        {"slug": "aws-ecs",     "name": "AWS ECS",       "description": "Container orchestration on AWS with Fargate",          "tier": "paid",     "monthly_cost_usd": 0,  "category": "deploy"},
        {"slug": "k8s",         "name": "Kubernetes",    "description": "Container orchestration for large-scale production",   "tier": "free",     "monthly_cost_usd": 0,  "category": "deploy"},
        {"slug": "netlify",     "name": "Netlify",       "description": "Jamstack hosting with CI/CD and edge functions",       "tier": "freemium", "monthly_cost_usd": 0,  "category": "deploy"},
        {"slug": "coolify",     "name": "Coolify",       "description": "Self-hosted Heroku/Netlify alternative, open source",  "tier": "free",     "monthly_cost_usd": 0,  "category": "deploy"},
    ],
    "ai": [
        {"slug": "openai",      "name": "OpenAI API",        "description": "GPT-4o, embeddings, vision, Whisper, DALL·E",       "tier": "paid",     "monthly_cost_usd": 20, "category": "ai"},
        {"slug": "anthropic",   "name": "Anthropic Claude",  "description": "Claude 3.5/4 — long context, reasoning, code",      "tier": "paid",     "monthly_cost_usd": 15, "category": "ai"},
        {"slug": "groq",        "name": "Groq",              "description": "Ultra-fast inference — Llama3, Mixtral free tier",   "tier": "freemium", "monthly_cost_usd": 0,  "category": "ai"},
        {"slug": "ollama",      "name": "Ollama",            "description": "Run LLMs locally — Llama3, Mistral, Phi3, Gemma",   "tier": "free",     "monthly_cost_usd": 0,  "category": "ai"},
        {"slug": "langchain",   "name": "LangChain",         "description": "LLM application framework and LCEL pipelines",      "tier": "free",     "monthly_cost_usd": 0,  "category": "ai"},
        {"slug": "pinecone",    "name": "Pinecone",          "description": "Managed vector DB for semantic search and RAG",      "tier": "freemium", "monthly_cost_usd": 0,  "category": "ai"},
        {"slug": "llamaindex",  "name": "LlamaIndex",        "description": "Data framework for LLM apps — RAG, agents, tools",  "tier": "free",     "monthly_cost_usd": 0,  "category": "ai"},
        {"slug": "huggingface", "name": "Hugging Face",      "description": "400k+ open models, datasets, and Spaces hosting",   "tier": "freemium", "monthly_cost_usd": 0,  "category": "ai"},
        {"slug": "weaviate",    "name": "Weaviate",          "description": "Open-source vector database with hybrid search",     "tier": "freemium", "monthly_cost_usd": 0,  "category": "ai"},
        {"slug": "together-ai", "name": "Together AI",       "description": "Fast inference for open-source models, pay-as-go",  "tier": "paid",     "monthly_cost_usd": 0,  "category": "ai"},
        {"slug": "replicate",   "name": "Replicate",         "description": "Run open-source AI models via API, pay-per-use",    "tier": "paid",     "monthly_cost_usd": 0,  "category": "ai"},
        {"slug": "vercel-ai",   "name": "Vercel AI SDK",     "description": "React hooks for streaming AI responses",            "tier": "free",     "monthly_cost_usd": 0,  "category": "ai"},
    ],
    "storage": [
        {"slug": "s3",               "name": "AWS S3",           "description": "Object storage for files, media, and backups",   "tier": "paid",     "monthly_cost_usd": 2, "category": "storage"},
        {"slug": "cloudinary",       "name": "Cloudinary",       "description": "Image/video transform, optimization, CDN",       "tier": "freemium", "monthly_cost_usd": 0, "category": "storage"},
        {"slug": "supabase-storage", "name": "Supabase Storage", "description": "S3-compatible storage with row-level access",    "tier": "freemium", "monthly_cost_usd": 0, "category": "storage"},
        {"slug": "r2",               "name": "Cloudflare R2",    "description": "Zero-egress S3-compatible object storage",       "tier": "freemium", "monthly_cost_usd": 0, "category": "storage"},
        {"slug": "uploadthing",      "name": "UploadThing",      "description": "File uploads for Next.js/React, 2GB free",       "tier": "freemium", "monthly_cost_usd": 0, "category": "storage"},
        {"slug": "backblaze",        "name": "Backblaze B2",     "description": "S3-compatible cloud storage at 1/4 the cost",    "tier": "freemium", "monthly_cost_usd": 0, "category": "storage"},
    ],
    "monitoring": [
        {"slug": "sentry",      "name": "Sentry",       "description": "Error tracking, performance monitoring, session replay",  "tier": "freemium", "monthly_cost_usd": 0,  "category": "monitoring"},
        {"slug": "posthog",     "name": "PostHog",      "description": "Open-source analytics, feature flags, A/B tests",        "tier": "freemium", "monthly_cost_usd": 0,  "category": "monitoring"},
        {"slug": "datadog",     "name": "Datadog",      "description": "Full-stack observability — metrics, APM, logs, traces",  "tier": "paid",     "monthly_cost_usd": 31, "category": "monitoring"},
        {"slug": "grafana",     "name": "Grafana",      "description": "Open-source metrics and log visualization dashboards",   "tier": "freemium", "monthly_cost_usd": 0,  "category": "monitoring"},
        {"slug": "newrelic",    "name": "New Relic",    "description": "Observability platform with 100GB/month free tier",      "tier": "freemium", "monthly_cost_usd": 0,  "category": "monitoring"},
        {"slug": "highlight",   "name": "Highlight.io", "description": "Open-source session replay and error monitoring",        "tier": "freemium", "monthly_cost_usd": 0,  "category": "monitoring"},
        {"slug": "betterstack", "name": "Better Stack", "description": "Uptime monitoring, logs, and on-call alerting",          "tier": "freemium", "monthly_cost_usd": 0,  "category": "monitoring"},
    ],
    "search": [
        {"slug": "elasticsearch", "name": "Elasticsearch", "description": "Distributed full-text search and analytics engine",    "tier": "freemium", "monthly_cost_usd": 0, "category": "search"},
        {"slug": "algolia",       "name": "Algolia",        "description": "Search as a service — instant, typo-tolerant",        "tier": "freemium", "monthly_cost_usd": 0, "category": "search"},
        {"slug": "typesense",     "name": "Typesense",      "description": "Open-source instant search, self-hostable",           "tier": "free",     "monthly_cost_usd": 0, "category": "search"},
        {"slug": "meilisearch",   "name": "Meilisearch",    "description": "Blazing fast, open-source full-text search",          "tier": "freemium", "monthly_cost_usd": 0, "category": "search"},
        {"slug": "opensearch",    "name": "OpenSearch",     "description": "Open-source fork of Elasticsearch by AWS",            "tier": "free",     "monthly_cost_usd": 0, "category": "search"},
    ],
    "realtime": [
        {"slug": "websockets",  "name": "WebSockets",   "description": "Native real-time bidirectional communication",             "tier": "free",     "monthly_cost_usd": 0, "category": "realtime"},
        {"slug": "pusher",      "name": "Pusher",        "description": "Hosted WebSocket service, 200k messages/day free",        "tier": "freemium", "monthly_cost_usd": 0, "category": "realtime"},
        {"slug": "ably",        "name": "Ably",          "description": "Realtime pub/sub messaging at scale with presence",       "tier": "freemium", "monthly_cost_usd": 0, "category": "realtime"},
        {"slug": "socket-io",   "name": "Socket.IO",     "description": "WebSocket library with rooms, namespaces, fallbacks",     "tier": "free",     "monthly_cost_usd": 0, "category": "realtime"},
        {"slug": "liveblocks",  "name": "Liveblocks",    "description": "Collaborative real-time features — cursors, presence",   "tier": "freemium", "monthly_cost_usd": 0, "category": "realtime"},
        {"slug": "partykit",    "name": "PartyKit",      "description": "Deploy real-time collaborative apps on edge workers",     "tier": "freemium", "monthly_cost_usd": 0, "category": "realtime"},
    ],
    "testing": [
        {"slug": "pytest",    "name": "pytest",      "description": "Python testing framework — simple, powerful, extensible",    "tier": "free", "monthly_cost_usd": 0, "category": "testing"},
        {"slug": "jest",      "name": "Jest",        "description": "JavaScript testing framework with snapshots and mocks",      "tier": "free", "monthly_cost_usd": 0, "category": "testing"},
        {"slug": "vitest",    "name": "Vitest",      "description": "Vite-native unit testing framework, Jest-compatible",        "tier": "free", "monthly_cost_usd": 0, "category": "testing"},
        {"slug": "playwright","name": "Playwright",  "description": "End-to-end browser testing for modern web apps",             "tier": "free", "monthly_cost_usd": 0, "category": "testing"},
        {"slug": "cypress",   "name": "Cypress",     "description": "E2E testing with time-travel debugging and real browser",    "tier": "freemium", "monthly_cost_usd": 0, "category": "testing"},
    ],
    "devtools": [
        {"slug": "terraform",  "name": "Terraform",    "description": "Infrastructure as Code — provision any cloud provider",   "tier": "free", "monthly_cost_usd": 0, "category": "devtools"},
        {"slug": "github-ci",  "name": "GitHub Actions","description": "CI/CD pipelines built into GitHub, 2000 min/mo free",   "tier": "freemium", "monthly_cost_usd": 0, "category": "devtools"},
        {"slug": "nx",         "name": "Nx",           "description": "Monorepo build system with smart caching",                "tier": "freemium", "monthly_cost_usd": 0, "category": "devtools"},
        {"slug": "turborepo",  "name": "Turborepo",    "description": "High-performance monorepo build tool by Vercel",          "tier": "free", "monthly_cost_usd": 0, "category": "devtools"},
        {"slug": "zod",        "name": "Zod",          "description": "TypeScript-first schema validation with static types",    "tier": "free", "monthly_cost_usd": 0, "category": "devtools"},
    ],
    "automation": [
        {"slug": "n8n",             "name": "n8n",             "description": "Visual no-code workflow automation with 400+ integrations and AI nodes. Self-hostable Zapier alternative.", "tier": "free", "monthly_cost_usd": 0, "category": "automation", "github_url": "https://github.com/n8n-io/n8n",             "stars": 182000},
        {"slug": "dify",            "name": "Dify",            "description": "Production-ready no-code LLM app and agent builder with RAG, visual workflow, and prompt IDE.",            "tier": "free", "monthly_cost_usd": 0, "category": "automation", "github_url": "https://github.com/langgenius/dify",         "stars": 135000},
        {"slug": "automatisch",     "name": "Automatisch",     "description": "Open-source Zapier alternative. Build trigger-action workflow automation without code.",                   "tier": "free", "monthly_cost_usd": 0, "category": "automation", "github_url": "https://github.com/automatisch/automatisch", "stars": 13700},
        {"slug": "activepieces",    "name": "Activepieces",    "description": "Open-source automation with 400+ MCP servers and AI agent workflows.",                                     "tier": "free", "monthly_cost_usd": 0, "category": "automation", "github_url": "https://github.com/activepieces/activepieces","stars": 21500},
    ],
    "no-code-builder": [
        {"slug": "budibase",    "name": "Budibase",    "description": "No-code platform to build internal apps, AI agents, and automations. Open-source Retool alternative.", "tier": "free", "monthly_cost_usd": 0, "category": "no-code-builder", "github_url": "https://github.com/Budibase/budibase",        "stars": 27800},
        {"slug": "coze-studio", "name": "Coze Studio", "description": "ByteDance's visual AI agent IDE — build, debug and deploy agents with an all-in-one no-code canvas.",   "tier": "free", "monthly_cost_usd": 0, "category": "no-code-builder", "github_url": "https://github.com/coze-dev/coze-studio",     "stars": 20400},
        {"slug": "fastgpt",     "name": "FastGPT",     "description": "No-code knowledge base and agent workflow builder built on LLMs, with MCP support.",                      "tier": "free", "monthly_cost_usd": 0, "category": "no-code-builder", "github_url": "https://github.com/labring/FastGPT",          "stars": 27600},
        {"slug": "pyspur",      "name": "PySpur",      "description": "Visual playground for iterating agentic workflows 10x faster. Lightweight and dev-friendly.",             "tier": "free", "monthly_cost_usd": 0, "category": "no-code-builder", "github_url": "https://github.com/PySpur-Dev/pyspur",        "stars": 5700},
        {"slug": "baserow",     "name": "Baserow",     "description": "No-code Airtable alternative with built-in database, automations, and AI agents.",                        "tier": "free", "monthly_cost_usd": 0, "category": "no-code-builder", "github_url": "https://github.com/baserow/baserow",          "stars": 4500},
        {"slug": "maxun",       "name": "Maxun",       "description": "No-code web scraping and AI data extraction platform. Point-and-click scraper builder.",                  "tier": "free", "monthly_cost_usd": 0, "category": "no-code-builder", "github_url": "https://github.com/getmaxun/maxun",           "stars": 15300},
    ],
    "agent-framework": [
        {"slug": "crewai",         "name": "CrewAI",         "description": "Framework for orchestrating role-playing autonomous AI agents with collaborative intelligence.",    "tier": "free", "monthly_cost_usd": 0, "category": "agent-framework", "github_url": "https://github.com/crewAIInc/crewAI",          "stars": 47900},
        {"slug": "sim",            "name": "Sim Studio",     "description": "Visual canvas to build, deploy, and orchestrate AI agent workforces.",                             "tier": "free", "monthly_cost_usd": 0, "category": "agent-framework", "github_url": "https://github.com/simstudioai/sim",           "stars": 27400},
        {"slug": "agentgpt",       "name": "AgentGPT",       "description": "Assemble, configure and deploy autonomous AI agents in the browser.",                              "tier": "free", "monthly_cost_usd": 0, "category": "agent-framework", "github_url": "https://github.com/reworkd/AgentGPT",          "stars": 35900},
        {"slug": "agent-squad",    "name": "Agent Squad",    "description": "AWS open-source framework for managing multiple AI agents and complex conversations.",             "tier": "free", "monthly_cost_usd": 0, "category": "agent-framework", "github_url": "https://github.com/awslabs/agent-squad",       "stars": 7600},
        {"slug": "superagi",       "name": "SuperAGI",       "description": "Dev-first open-source autonomous AI agent framework. Build, manage and run agents.",               "tier": "free", "monthly_cost_usd": 0, "category": "agent-framework", "github_url": "https://github.com/TransformerOptimus/SuperAGI","stars": 17400},
        {"slug": "haystack",       "name": "Haystack",       "description": "Open-source AI orchestration framework for production-ready, context-engineered LLM apps.",       "tier": "free", "monthly_cost_usd": 0, "category": "agent-framework", "github_url": "https://github.com/deepset-ai/haystack",       "stars": 24700},
        {"slug": "skyvern",        "name": "Skyvern",        "description": "AI-powered browser workflow automation. Automate any web task with vision + LLMs.",               "tier": "free", "monthly_cost_usd": 0, "category": "agent-framework", "github_url": "https://github.com/Skyvern-AI/skyvern",        "stars": 21000},
        {"slug": "trigger-dev",    "name": "Trigger.dev",    "description": "Build and deploy fully-managed AI agents and background workflow jobs.",                           "tier": "freemium", "monthly_cost_usd": 0, "category": "agent-framework", "github_url": "https://github.com/triggerdotdev/trigger.dev","stars": 14300},
    ],
}


@router.get("/stacks", summary="Get curated product-building stack catalog")
async def get_stacks():
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
