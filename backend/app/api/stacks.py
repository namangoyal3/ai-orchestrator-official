"""
Stacks API — curated product-building tool catalog for the Namango CLI.

Opinionated, high-signal catalog. Every tool here is something a builder
would actually choose. Noise removed: no obscure infra, no dead projects.

Powers `namango init` stack recommendations.

execution_type values:
  mcp        → configure as MCP server in editor (Claude Code, Cursor, etc.)
  api        → sign up for API key, add env var
  hosted     → one-click deploy to Railway/Vercel/Render
  self-host  → clone repo and self-host (Docker or similar)
  install    → npm/pip/brew install locally
  recommend-only → link out, no activation path yet
"""
from fastapi import APIRouter

router = APIRouter(prefix="/v1", tags=["Stacks"])

STACK_CATALOG: dict[str, list[dict]] = {

    # ── Frontend / Web ────────────────────────────────────────────────────────
    "web": [
        {
            "slug": "nextjs", "name": "Next.js", "tier": "free", "monthly_cost_usd": 0, "category": "web",
            "description": "React framework with SSR, API routes, and App Router. Default choice for most SaaS.",
            "execution_type": "install",
            "execution_config": {"install_cmd": "npx create-next-app@latest", "docs_url": "https://nextjs.org/docs"},
        },
        {
            "slug": "react", "name": "React", "tier": "free", "monthly_cost_usd": 0, "category": "web",
            "description": "UI component library. Use with Vite for SPAs, Next.js for full-stack.",
            "execution_type": "install",
            "execution_config": {"install_cmd": "npm create vite@latest -- --template react", "docs_url": "https://react.dev"},
        },
        {
            "slug": "tailwind", "name": "Tailwind CSS", "tier": "free", "monthly_cost_usd": 0, "category": "web",
            "description": "Utility-first CSS. Fastest way to build clean UIs without writing custom CSS.",
            "execution_type": "install",
            "execution_config": {"install_cmd": "npm install -D tailwindcss postcss autoprefixer && npx tailwindcss init", "docs_url": "https://tailwindcss.com/docs/installation"},
        },
        {
            "slug": "shadcn", "name": "shadcn/ui", "tier": "free", "monthly_cost_usd": 0, "category": "web",
            "description": "Copy-paste accessible React components. Pairs with Tailwind + Next.js.",
            "execution_type": "install",
            "execution_config": {"install_cmd": "npx shadcn@latest init", "docs_url": "https://ui.shadcn.com/docs/installation"},
        },
    ],

    # ── Backend ───────────────────────────────────────────────────────────────
    "backend": [
        {
            "slug": "fastapi", "name": "FastAPI", "tier": "free", "monthly_cost_usd": 0, "category": "backend",
            "description": "Best Python API framework. Fast, async, auto-docs. Ideal for AI/ML backends.",
            "execution_type": "install",
            "execution_config": {"install_cmd": "pip install fastapi uvicorn", "docs_url": "https://fastapi.tiangolo.com"},
        },
        {
            "slug": "express", "name": "Express.js", "tier": "free", "monthly_cost_usd": 0, "category": "backend",
            "description": "Minimal Node.js framework. Good for simple APIs and proxies.",
            "execution_type": "install",
            "execution_config": {"install_cmd": "npm install express", "docs_url": "https://expressjs.com"},
        },
        {
            "slug": "nestjs", "name": "NestJS", "tier": "free", "monthly_cost_usd": 0, "category": "backend",
            "description": "Structured TypeScript backend with dependency injection. Great for large teams.",
            "execution_type": "install",
            "execution_config": {"install_cmd": "npm i -g @nestjs/cli && nest new project-name", "docs_url": "https://docs.nestjs.com"},
        },
        {
            "slug": "hono", "name": "Hono", "tier": "free", "monthly_cost_usd": 0, "category": "backend",
            "description": "Ultra-fast edge-native API framework. Runs on Cloudflare Workers, Vercel Edge.",
            "execution_type": "install",
            "execution_config": {"install_cmd": "npm create hono@latest", "docs_url": "https://hono.dev/docs"},
        },
    ],

    # ── Database ──────────────────────────────────────────────────────────────
    "database": [
        {
            "slug": "supabase", "name": "Supabase", "tier": "freemium", "monthly_cost_usd": 0, "category": "database",
            "description": "Postgres + Auth + Storage + Realtime in one. Best default for new projects.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://supabase.com/dashboard", "env_vars": ["SUPABASE_URL", "SUPABASE_ANON_KEY"], "install_cmd": "npm install @supabase/supabase-js"},
        },
        {
            "slug": "postgresql", "name": "PostgreSQL", "tier": "free", "monthly_cost_usd": 0, "category": "database",
            "description": "Gold-standard open-source relational DB. Self-host or use Neon/Supabase.",
            "execution_type": "hosted",
            "execution_config": {"deploy_url": "https://railway.app/new/template/postgresql", "env_vars": ["DATABASE_URL"], "install_cmd": "npm install pg"},
        },
        {
            "slug": "neon", "name": "Neon", "tier": "freemium", "monthly_cost_usd": 0, "category": "database",
            "description": "Serverless Postgres with branching. Great for Railway/Vercel deploys.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://neon.tech/signup", "env_vars": ["DATABASE_URL"], "install_cmd": "npm install @neondatabase/serverless"},
        },
        {
            "slug": "mongodb", "name": "MongoDB", "tier": "freemium", "monthly_cost_usd": 0, "category": "database",
            "description": "Flexible document DB. Good for unstructured or rapidly evolving schemas.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://www.mongodb.com/cloud/atlas/register", "env_vars": ["MONGODB_URI"], "install_cmd": "npm install mongoose"},
        },
        {
            "slug": "sqlite", "name": "SQLite", "tier": "free", "monthly_cost_usd": 0, "category": "database",
            "description": "Zero-config embedded DB. Perfect for local dev and lightweight apps.",
            "execution_type": "install",
            "execution_config": {"install_cmd": "npm install better-sqlite3", "docs_url": "https://www.sqlite.org/docs.html"},
        },
        {
            "slug": "prisma", "name": "Prisma ORM", "tier": "free", "monthly_cost_usd": 0, "category": "database",
            "description": "Type-safe ORM with migrations and Prisma Studio. Use with any SQL DB.",
            "execution_type": "install",
            "execution_config": {"install_cmd": "npm install prisma @prisma/client && npx prisma init", "docs_url": "https://www.prisma.io/docs"},
        },
        {
            "slug": "drizzle", "name": "Drizzle ORM", "tier": "free", "monthly_cost_usd": 0, "category": "database",
            "description": "Lightweight TypeScript ORM. Faster than Prisma, great for edge runtimes.",
            "execution_type": "install",
            "execution_config": {"install_cmd": "npm install drizzle-orm drizzle-kit", "docs_url": "https://orm.drizzle.team/docs/overview"},
        },
    ],

    # ── Auth ──────────────────────────────────────────────────────────────────
    "auth": [
        {
            "slug": "clerk", "name": "Clerk", "tier": "freemium", "monthly_cost_usd": 0, "category": "auth",
            "description": "Best-in-class drop-in auth UI for Next.js. Social login, MFA, orgs — zero config.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://dashboard.clerk.com/sign-up", "env_vars": ["NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", "CLERK_SECRET_KEY"], "install_cmd": "npm install @clerk/nextjs"},
        },
        {
            "slug": "supabase-auth", "name": "Supabase Auth", "tier": "freemium", "monthly_cost_usd": 0, "category": "auth",
            "description": "Open-source auth with social login, magic links, and row-level security.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://supabase.com/dashboard", "env_vars": ["SUPABASE_URL", "SUPABASE_ANON_KEY"], "install_cmd": "npm install @supabase/supabase-js"},
        },
        {
            "slug": "nextauth", "name": "NextAuth.js", "tier": "free", "monthly_cost_usd": 0, "category": "auth",
            "description": "Auth for Next.js with 50+ OAuth providers. Free and self-hosted.",
            "execution_type": "install",
            "execution_config": {"install_cmd": "npm install next-auth", "env_vars": ["NEXTAUTH_SECRET", "NEXTAUTH_URL"], "docs_url": "https://next-auth.js.org/getting-started/introduction"},
        },
        {
            "slug": "auth0", "name": "Auth0", "tier": "freemium", "monthly_cost_usd": 23, "category": "auth",
            "description": "Enterprise identity platform — OAuth, OIDC, SAML, MFA. Best for B2B SaaS.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://auth0.com/signup", "env_vars": ["AUTH0_SECRET", "AUTH0_BASE_URL", "AUTH0_ISSUER_BASE_URL", "AUTH0_CLIENT_ID", "AUTH0_CLIENT_SECRET"], "install_cmd": "npm install @auth0/nextjs-auth0"},
        },
    ],

    # ── Payments ──────────────────────────────────────────────────────────────
    "payments": [
        {
            "slug": "stripe", "name": "Stripe", "tier": "paid", "monthly_cost_usd": 0, "category": "payments",
            "description": "Default choice for payments. Subscriptions, invoices, Connect, global.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://dashboard.stripe.com/register", "env_vars": ["STRIPE_SECRET_KEY", "STRIPE_PUBLISHABLE_KEY", "STRIPE_WEBHOOK_SECRET"], "install_cmd": "npm install stripe @stripe/stripe-js"},
        },
        {
            "slug": "lemonsqueezy", "name": "Lemon Squeezy", "tier": "paid", "monthly_cost_usd": 0, "category": "payments",
            "description": "Merchant of record for indie SaaS. Handles VAT/tax globally. Simpler than Stripe.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://app.lemonsqueezy.com/register", "env_vars": ["LEMONSQUEEZY_API_KEY", "LEMONSQUEEZY_WEBHOOK_SECRET"], "install_cmd": "npm install @lemonsqueezy/lemonsqueezy.js"},
        },
        {
            "slug": "razorpay", "name": "Razorpay", "tier": "paid", "monthly_cost_usd": 0, "category": "payments",
            "description": "Best for Indian market — UPI, cards, net banking, subscriptions.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://dashboard.razorpay.com/signup", "env_vars": ["RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET"], "install_cmd": "npm install razorpay"},
        },
    ],

    # ── AI / LLM ──────────────────────────────────────────────────────────────
    "ai": [
        {
            "slug": "anthropic", "name": "Anthropic Claude", "tier": "paid", "monthly_cost_usd": 15, "category": "ai",
            "description": "Best for reasoning, long context, and code. Claude 3.5/4 via API.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://console.anthropic.com", "env_vars": ["ANTHROPIC_API_KEY"], "install_cmd": "npm install @anthropic-ai/sdk"},
        },
        {
            "slug": "openai", "name": "OpenAI API", "tier": "paid", "monthly_cost_usd": 20, "category": "ai",
            "description": "GPT-4o, embeddings, vision, Whisper, DALL-E. Widest ecosystem.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://platform.openai.com/signup", "env_vars": ["OPENAI_API_KEY"], "install_cmd": "npm install openai"},
        },
        {
            "slug": "groq", "name": "Groq", "tier": "freemium", "monthly_cost_usd": 0, "category": "ai",
            "description": "Fastest LLM inference — Llama 3, Mixtral. Free tier available.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://console.groq.com", "env_vars": ["GROQ_API_KEY"], "install_cmd": "npm install groq-sdk"},
        },
        {
            "slug": "ollama", "name": "Ollama", "tier": "free", "monthly_cost_usd": 0, "category": "ai",
            "description": "Run LLMs locally — Llama 3, Mistral, Phi. Zero cost, full privacy.",
            "execution_type": "install",
            "execution_config": {"install_cmd": "curl -fsSL https://ollama.com/install.sh | sh && ollama pull llama3", "docs_url": "https://ollama.com/library"},
        },
        {
            "slug": "openrouter", "name": "OpenRouter", "tier": "freemium", "monthly_cost_usd": 0, "category": "ai",
            "description": "Single API for 100+ models. Route between Claude, GPT, Gemini, Llama.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://openrouter.ai/keys", "env_vars": ["OPENROUTER_API_KEY"], "install_cmd": "npm install openai"},
        },
        {
            "slug": "vercel-ai", "name": "Vercel AI SDK", "tier": "free", "monthly_cost_usd": 0, "category": "ai",
            "description": "Best SDK for streaming AI responses in Next.js. Provider-agnostic.",
            "execution_type": "install",
            "execution_config": {"install_cmd": "npm install ai", "docs_url": "https://sdk.vercel.ai/docs"},
        },
        {
            "slug": "langchain", "name": "LangChain", "tier": "free", "monthly_cost_usd": 0, "category": "ai",
            "description": "LLM chains, agents, RAG pipelines. Largest ecosystem of integrations.",
            "execution_type": "install",
            "execution_config": {"install_cmd": "npm install langchain @langchain/openai", "docs_url": "https://js.langchain.com/docs"},
        },
        {
            "slug": "pinecone", "name": "Pinecone", "tier": "freemium", "monthly_cost_usd": 0, "category": "ai",
            "description": "Managed vector DB for RAG and semantic search. Production-ready.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://app.pinecone.io/?sessionType=signup", "env_vars": ["PINECONE_API_KEY", "PINECONE_INDEX"], "install_cmd": "npm install @pinecone-database/pinecone"},
        },
        {
            "slug": "qdrant", "name": "Qdrant", "tier": "free", "monthly_cost_usd": 0, "category": "ai",
            "description": "Open-source vector DB. Self-hostable alternative to Pinecone.",
            "execution_type": "self-host",
            "execution_config": {"deploy_cmd": "docker run -p 6333:6333 qdrant/qdrant", "github_url": "https://github.com/qdrant/qdrant", "install_cmd": "pip install qdrant-client"},
        },
    ],

    # ── No-Code Workflow Automation ───────────────────────────────────────────
    "automation": [
        {
            "slug": "n8n", "name": "n8n", "tier": "free", "monthly_cost_usd": 0, "category": "automation",
            "description": "Visual drag-and-drop workflow automation. 400+ integrations, AI nodes, self-hostable. Best Zapier alternative.",
            "use_case_tags": ["workflow", "automation", "no-code", "zapier", "trigger", "visual", "drag-drop", "integration"],
            "github_url": "https://github.com/n8n-io/n8n", "stars": 182000,
            "execution_type": "self-host",
            "execution_config": {"deploy_cmd": "docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n", "deploy_url": "https://railway.app/new/template/n8n", "github_url": "https://github.com/n8n-io/n8n"},
        },
        {
            "slug": "dify", "name": "Dify", "tier": "free", "monthly_cost_usd": 0, "category": "automation",
            "description": "No-code LLM app and agent builder. RAG, visual workflow, prompt IDE. Production-ready.",
            "use_case_tags": ["llm", "agent", "no-code", "rag", "chatbot", "workflow", "prompt", "ai-app"],
            "github_url": "https://github.com/langgenius/dify", "stars": 135000,
            "execution_type": "self-host",
            "execution_config": {"deploy_cmd": "git clone https://github.com/langgenius/dify && cd dify/docker && docker compose up -d", "deploy_url": "https://railway.app/new/template/dify", "github_url": "https://github.com/langgenius/dify"},
        },
        {
            "slug": "activepieces", "name": "Activepieces", "tier": "free", "monthly_cost_usd": 0, "category": "automation",
            "description": "400+ MCP servers + AI workflow automation. Self-hostable TypeScript.",
            "use_case_tags": ["automation", "workflow", "mcp", "integration", "no-code", "zapier"],
            "github_url": "https://github.com/activepieces/activepieces", "stars": 21500,
            "execution_type": "self-host",
            "execution_config": {"deploy_cmd": "docker run -d -p 8080:80 activepieces/activepieces", "github_url": "https://github.com/activepieces/activepieces"},
        },
        {
            "slug": "automatisch", "name": "Automatisch", "tier": "free", "monthly_cost_usd": 0, "category": "automation",
            "description": "Clean open-source Zapier alternative. Trigger-action automation, no AI bloat.",
            "use_case_tags": ["automation", "workflow", "zapier", "trigger", "no-code"],
            "github_url": "https://github.com/automatisch/automatisch", "stars": 13700,
            "execution_type": "self-host",
            "execution_config": {"deploy_cmd": "git clone https://github.com/automatisch/automatisch && cd automatisch && docker compose up -d", "github_url": "https://github.com/automatisch/automatisch"},
        },
    ],

    # ── No-Code App Builders ──────────────────────────────────────────────────
    "no-code-builder": [
        {
            "slug": "budibase", "name": "Budibase", "tier": "free", "monthly_cost_usd": 0, "category": "no-code-builder",
            "description": "No-code internal app builder with AI agents and automations. Open-source Retool.",
            "use_case_tags": ["no-code", "internal-tool", "dashboard", "crud", "retool", "admin", "visual-builder"],
            "github_url": "https://github.com/Budibase/budibase", "stars": 27800,
            "execution_type": "self-host",
            "execution_config": {"deploy_cmd": "docker run --rm --name budibase -p 10000:10000 budibase/budibase", "deploy_url": "https://railway.app/new/template/budibase", "github_url": "https://github.com/Budibase/budibase"},
        },
        {
            "slug": "coze-studio", "name": "Coze Studio", "tier": "free", "monthly_cost_usd": 0, "category": "no-code-builder",
            "description": "ByteDance's visual AI agent IDE. Build, debug and deploy agents — no code needed.",
            "use_case_tags": ["agent", "no-code", "visual-builder", "chatbot", "ai-studio", "drag-drop"],
            "github_url": "https://github.com/coze-dev/coze-studio", "stars": 20400,
            "execution_type": "self-host",
            "execution_config": {"github_url": "https://github.com/coze-dev/coze-studio", "docs_url": "https://github.com/coze-dev/coze-studio#readme"},
        },
        {
            "slug": "fastgpt", "name": "FastGPT", "tier": "free", "monthly_cost_usd": 0, "category": "no-code-builder",
            "description": "No-code knowledge base + agent workflow builder. MCP support built-in.",
            "use_case_tags": ["knowledge-base", "rag", "no-code", "chatbot", "workflow", "mcp"],
            "github_url": "https://github.com/labring/FastGPT", "stars": 27600,
            "execution_type": "self-host",
            "execution_config": {"deploy_cmd": "git clone https://github.com/labring/FastGPT && cd FastGPT && docker compose up -d", "github_url": "https://github.com/labring/FastGPT"},
        },
        {
            "slug": "pyspur", "name": "PySpur", "tier": "free", "monthly_cost_usd": 0, "category": "no-code-builder",
            "description": "Visual playground for agentic workflows. Iterate 10x faster with live feedback.",
            "use_case_tags": ["agent", "workflow", "visual", "agentic", "no-code", "prototype"],
            "github_url": "https://github.com/PySpur-Dev/pyspur", "stars": 5700,
            "execution_type": "self-host",
            "execution_config": {"deploy_cmd": "pip install pyspur && pyspur app", "github_url": "https://github.com/PySpur-Dev/pyspur"},
        },
        {
            "slug": "baserow", "name": "Baserow", "tier": "free", "monthly_cost_usd": 0, "category": "no-code-builder",
            "description": "No-code Airtable alternative with database, automations, and AI agents.",
            "use_case_tags": ["no-code", "database", "airtable", "spreadsheet", "automation", "crud"],
            "github_url": "https://github.com/baserow/baserow", "stars": 4500,
            "execution_type": "self-host",
            "execution_config": {"deploy_cmd": "docker run -v baserow_data:/baserow/data -p 80:80 -p 443:443 baserow/baserow:latest", "github_url": "https://github.com/baserow/baserow"},
        },
        {
            "slug": "maxun", "name": "Maxun", "tier": "free", "monthly_cost_usd": 0, "category": "no-code-builder",
            "description": "No-code web scraping and AI data extraction. Point-and-click scraper builder.",
            "use_case_tags": ["scraping", "web-scraper", "no-code", "data-extraction", "crawling"],
            "github_url": "https://github.com/getmaxun/maxun", "stars": 15300,
            "execution_type": "self-host",
            "execution_config": {"github_url": "https://github.com/getmaxun/maxun", "docs_url": "https://github.com/getmaxun/maxun#readme"},
        },
    ],

    # ── AI Agent Frameworks ───────────────────────────────────────────────────
    "agent-framework": [
        {
            "slug": "crewai", "name": "CrewAI", "tier": "free", "monthly_cost_usd": 0, "category": "agent-framework",
            "description": "Most popular agent framework. Role-playing autonomous agents with collaborative intelligence.",
            "use_case_tags": ["agent", "multi-agent", "autonomous", "orchestration", "llm", "agentic"],
            "github_url": "https://github.com/crewAIInc/crewAI", "stars": 47900,
            "execution_type": "install",
            "execution_config": {"install_cmd": "pip install crewai crewai-tools", "docs_url": "https://docs.crewai.com"},
        },
        {
            "slug": "sim", "name": "Sim Studio", "tier": "free", "monthly_cost_usd": 0, "category": "agent-framework",
            "description": "Visual canvas to build, deploy, and orchestrate AI agent workforces.",
            "use_case_tags": ["agent", "visual", "orchestration", "workflow", "ai-agent", "canvas"],
            "github_url": "https://github.com/simstudioai/sim", "stars": 27400,
            "execution_type": "self-host",
            "execution_config": {"github_url": "https://github.com/simstudioai/sim", "docs_url": "https://simstudio.ai/docs"},
        },
        {
            "slug": "agentgpt", "name": "AgentGPT", "tier": "free", "monthly_cost_usd": 0, "category": "agent-framework",
            "description": "Assemble and deploy autonomous AI agents in the browser. No setup needed.",
            "use_case_tags": ["agent", "autonomous", "browser", "no-code", "ai-agent"],
            "github_url": "https://github.com/reworkd/AgentGPT", "stars": 35900,
            "execution_type": "self-host",
            "execution_config": {"deploy_cmd": "git clone https://github.com/reworkd/AgentGPT && cd AgentGPT && ./setup.sh", "github_url": "https://github.com/reworkd/AgentGPT"},
        },
        {
            "slug": "haystack", "name": "Haystack", "tier": "free", "monthly_cost_usd": 0, "category": "agent-framework",
            "description": "Production-ready LLM orchestration framework for RAG, agents, and pipelines.",
            "use_case_tags": ["rag", "llm", "orchestration", "pipeline", "search", "agent"],
            "github_url": "https://github.com/deepset-ai/haystack", "stars": 24700,
            "execution_type": "install",
            "execution_config": {"install_cmd": "pip install haystack-ai", "docs_url": "https://docs.haystack.deepset.ai"},
        },
        {
            "slug": "skyvern", "name": "Skyvern", "tier": "free", "monthly_cost_usd": 0, "category": "agent-framework",
            "description": "AI browser automation. Automate any web workflow with vision + LLMs.",
            "use_case_tags": ["browser-automation", "agent", "web", "vision", "scraping", "workflow"],
            "github_url": "https://github.com/Skyvern-AI/skyvern", "stars": 21000,
            "execution_type": "api",
            "execution_config": {"signup_url": "https://app.skyvern.com/signup", "env_vars": ["SKYVERN_API_KEY", "SKYVERN_BASE_URL"], "install_cmd": "pip install skyvern"},
        },
        {
            "slug": "superagi", "name": "SuperAGI", "tier": "free", "monthly_cost_usd": 0, "category": "agent-framework",
            "description": "Dev-first autonomous AI agent framework. Build, manage, and run production agents.",
            "use_case_tags": ["agent", "autonomous", "agentic", "framework", "ai-agent"],
            "github_url": "https://github.com/TransformerOptimus/SuperAGI", "stars": 17400,
            "execution_type": "self-host",
            "execution_config": {"deploy_cmd": "git clone https://github.com/TransformerOptimus/SuperAGI && cd SuperAGI && docker compose up -d", "github_url": "https://github.com/TransformerOptimus/SuperAGI"},
        },
        {
            "slug": "trigger-dev", "name": "Trigger.dev", "tier": "freemium", "monthly_cost_usd": 0, "category": "agent-framework",
            "description": "Build and deploy fully-managed AI agents and background jobs. Cloud or self-hosted.",
            "use_case_tags": ["background-jobs", "workflow", "automation", "agent", "scheduling"],
            "github_url": "https://github.com/triggerdotdev/trigger.dev", "stars": 14300,
            "execution_type": "api",
            "execution_config": {"signup_url": "https://cloud.trigger.dev/login", "env_vars": ["TRIGGER_SECRET_KEY"], "install_cmd": "npx trigger.dev@latest init"},
        },
        {
            "slug": "agent-squad", "name": "Agent Squad", "tier": "free", "monthly_cost_usd": 0, "category": "agent-framework",
            "description": "AWS open-source framework for multi-agent systems and complex conversations.",
            "use_case_tags": ["agent", "multi-agent", "conversation", "aws", "orchestration"],
            "github_url": "https://github.com/awslabs/agent-squad", "stars": 7600,
            "execution_type": "install",
            "execution_config": {"install_cmd": "pip install agent-squad", "docs_url": "https://github.com/awslabs/agent-squad#readme"},
        },
    ],

    # ── MCP Ecosystem ─────────────────────────────────────────────────────────
    "mcp": [
        {
            "slug": "fastapi-mcp", "name": "FastAPI MCP", "tier": "free", "monthly_cost_usd": 0, "category": "mcp",
            "description": "Expose any FastAPI endpoint as an MCP tool instantly. With auth.",
            "use_case_tags": ["mcp", "api", "tool-calling", "fastapi", "integration"],
            "github_url": "https://github.com/tadata-org/fastapi_mcp", "stars": 11700,
            "execution_type": "install",
            "execution_config": {"install_cmd": "pip install fastapi-mcp", "docs_url": "https://github.com/tadata-org/fastapi_mcp#readme"},
        },
        {
            "slug": "mcp-agent", "name": "MCP Agent", "tier": "free", "monthly_cost_usd": 0, "category": "mcp",
            "description": "Build effective agents using MCP and simple workflow patterns.",
            "use_case_tags": ["mcp", "agent", "workflow", "tool-calling"],
            "github_url": "https://github.com/lastmile-ai/mcp-agent", "stars": 8200,
            "execution_type": "install",
            "execution_config": {"install_cmd": "pip install mcp-agent", "docs_url": "https://github.com/lastmile-ai/mcp-agent#readme"},
        },
        {
            "slug": "mcp-go", "name": "MCP Go", "tier": "free", "monthly_cost_usd": 0, "category": "mcp",
            "description": "Go SDK for MCP — build high-performance MCP servers in Go.",
            "use_case_tags": ["mcp", "go", "server", "tool-calling"],
            "github_url": "https://github.com/mark3labs/mcp-go", "stars": 8500,
            "execution_type": "install",
            "execution_config": {"install_cmd": "go get github.com/mark3labs/mcp-go", "docs_url": "https://github.com/mark3labs/mcp-go#readme"},
        },
        {
            "slug": "mcp-registry", "name": "MCP Registry", "tier": "free", "monthly_cost_usd": 0, "category": "mcp",
            "description": "Official community-driven registry of MCP servers.",
            "use_case_tags": ["mcp", "registry", "servers", "marketplace"],
            "github_url": "https://github.com/modelcontextprotocol/registry", "stars": 6600,
            "execution_type": "recommend-only",
            "execution_config": {"docs_url": "https://github.com/modelcontextprotocol/registry"},
        },
        {
            "slug": "mcp-playwright", "name": "MCP Playwright", "tier": "free", "monthly_cost_usd": 0, "category": "mcp",
            "description": "Playwright MCP server — give agents full browser automation capabilities.",
            "use_case_tags": ["mcp", "browser", "automation", "testing", "playwright"],
            "github_url": "https://github.com/executeautomation/mcp-playwright", "stars": 5400,
            "execution_type": "mcp",
            "execution_config": {"mcp_server_url": "npx @executeautomation/playwright-mcp-server", "install_cmd": "npm install @executeautomation/playwright-mcp-server", "editor_config": {"claude": {"command": "npx", "args": ["@executeautomation/playwright-mcp-server"]}}},
        },
    ],

    # ── Deploy / Hosting ──────────────────────────────────────────────────────
    "deploy": [
        {
            "slug": "vercel", "name": "Vercel", "tier": "freemium", "monthly_cost_usd": 0, "category": "deploy",
            "description": "Best for Next.js. Auto-deploys, edge functions, preview URLs. Generous free tier.",
            "execution_type": "hosted",
            "execution_config": {"signup_url": "https://vercel.com/signup", "deploy_url": "https://vercel.com/new", "install_cmd": "npm i -g vercel && vercel"},
        },
        {
            "slug": "railway", "name": "Railway", "tier": "freemium", "monthly_cost_usd": 5, "category": "deploy",
            "description": "Deploy anything with Git push. Databases, workers, cron — all in one. $5/mo hobby.",
            "execution_type": "hosted",
            "execution_config": {"signup_url": "https://railway.app/login", "deploy_url": "https://railway.app/new", "install_cmd": "npm i -g @railway/cli && railway login && railway up"},
        },
        {
            "slug": "render", "name": "Render", "tier": "freemium", "monthly_cost_usd": 7, "category": "deploy",
            "description": "Full-stack cloud — web services, workers, cron, managed DB. Heroku replacement.",
            "execution_type": "hosted",
            "execution_config": {"signup_url": "https://dashboard.render.com/register", "deploy_url": "https://dashboard.render.com/select-repo"},
        },
        {
            "slug": "fly", "name": "Fly.io", "tier": "freemium", "monthly_cost_usd": 0, "category": "deploy",
            "description": "Run Docker containers globally at the edge. Best for latency-sensitive apps.",
            "execution_type": "hosted",
            "execution_config": {"signup_url": "https://fly.io/app/sign-up", "install_cmd": "brew install flyctl && fly auth login && fly launch"},
        },
        {
            "slug": "docker", "name": "Docker", "tier": "free", "monthly_cost_usd": 0, "category": "deploy",
            "description": "Container packaging for consistent environments. Foundation for all cloud deploy.",
            "execution_type": "install",
            "execution_config": {"install_cmd": "brew install --cask docker", "docs_url": "https://docs.docker.com/get-started"},
        },
    ],

    # ── Email ─────────────────────────────────────────────────────────────────
    "email": [
        {
            "slug": "resend", "name": "Resend", "tier": "freemium", "monthly_cost_usd": 0, "category": "email",
            "description": "Best developer email API. React Email templates, 3K emails/mo free.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://resend.com/signup", "env_vars": ["RESEND_API_KEY"], "install_cmd": "npm install resend"},
        },
        {
            "slug": "sendgrid", "name": "SendGrid", "tier": "freemium", "monthly_cost_usd": 0, "category": "email",
            "description": "Reliable transactional email. 100/day free. Good for high volume.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://signup.sendgrid.com", "env_vars": ["SENDGRID_API_KEY"], "install_cmd": "npm install @sendgrid/mail"},
        },
        {
            "slug": "mailgun", "name": "Mailgun", "tier": "freemium", "monthly_cost_usd": 0, "category": "email",
            "description": "Email API with advanced analytics, logging, and inbound email parsing.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://signup.mailgun.com/new/signup", "env_vars": ["MAILGUN_API_KEY", "MAILGUN_DOMAIN"], "install_cmd": "npm install mailgun.js"},
        },
    ],

    # ── Storage ───────────────────────────────────────────────────────────────
    "storage": [
        {
            "slug": "r2", "name": "Cloudflare R2", "tier": "freemium", "monthly_cost_usd": 0, "category": "storage",
            "description": "Zero-egress S3-compatible object storage. Cheapest for high-bandwidth apps.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://dash.cloudflare.com/sign-up", "env_vars": ["R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME"], "install_cmd": "npm install @aws-sdk/client-s3"},
        },
        {
            "slug": "supabase-storage", "name": "Supabase Storage", "tier": "freemium", "monthly_cost_usd": 0, "category": "storage",
            "description": "S3-compatible storage with Postgres row-level security. Great with Supabase DB.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://supabase.com/dashboard", "env_vars": ["SUPABASE_URL", "SUPABASE_ANON_KEY"], "install_cmd": "npm install @supabase/supabase-js"},
        },
        {
            "slug": "cloudinary", "name": "Cloudinary", "tier": "freemium", "monthly_cost_usd": 0, "category": "storage",
            "description": "Image and video CDN with transforms, optimization, and AI tagging.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://cloudinary.com/users/register_free", "env_vars": ["CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"], "install_cmd": "npm install cloudinary"},
        },
        {
            "slug": "s3", "name": "AWS S3", "tier": "paid", "monthly_cost_usd": 2, "category": "storage",
            "description": "Gold standard object storage. Use for AWS-native stacks or compliance needs.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://aws.amazon.com/s3/", "env_vars": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION", "S3_BUCKET_NAME"], "install_cmd": "npm install @aws-sdk/client-s3"},
        },
    ],

    # ── Monitoring / Analytics ────────────────────────────────────────────────
    "monitoring": [
        {
            "slug": "sentry", "name": "Sentry", "tier": "freemium", "monthly_cost_usd": 0, "category": "monitoring",
            "description": "Error tracking and performance monitoring. First tool to add to any production app.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://sentry.io/signup/", "env_vars": ["SENTRY_DSN"], "install_cmd": "npm install @sentry/nextjs && npx @sentry/wizard@latest -i nextjs"},
        },
        {
            "slug": "posthog", "name": "PostHog", "tier": "freemium", "monthly_cost_usd": 0, "category": "monitoring",
            "description": "Open-source product analytics, feature flags, session replay, A/B testing.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://app.posthog.com/signup", "env_vars": ["NEXT_PUBLIC_POSTHOG_KEY", "NEXT_PUBLIC_POSTHOG_HOST"], "install_cmd": "npm install posthog-js"},
        },
        {
            "slug": "grafana", "name": "Grafana", "tier": "freemium", "monthly_cost_usd": 0, "category": "monitoring",
            "description": "Open-source metrics and log visualization. Connect to any data source.",
            "execution_type": "self-host",
            "execution_config": {"deploy_cmd": "docker run -d -p 3000:3000 grafana/grafana", "deploy_url": "https://grafana.com/auth/sign-up/create-user"},
        },
        {
            "slug": "datadog", "name": "Datadog", "tier": "paid", "monthly_cost_usd": 31, "category": "monitoring",
            "description": "Full-stack observability — APM, metrics, logs, synthetics. Enterprise choice.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://app.datadoghq.com/signup", "env_vars": ["DD_API_KEY", "DD_APP_KEY"], "install_cmd": "npm install dd-trace"},
        },
    ],

    # ── Realtime ──────────────────────────────────────────────────────────────
    "realtime": [
        {
            "slug": "socket-io", "name": "Socket.IO", "tier": "free", "monthly_cost_usd": 0, "category": "realtime",
            "description": "WebSocket library with rooms and namespaces. Most used realtime lib for Node.js.",
            "execution_type": "install",
            "execution_config": {"install_cmd": "npm install socket.io socket.io-client", "docs_url": "https://socket.io/docs/v4/"},
        },
        {
            "slug": "pusher", "name": "Pusher", "tier": "freemium", "monthly_cost_usd": 0, "category": "realtime",
            "description": "Hosted WebSocket channels. 200k messages/day free. Zero infra management.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://dashboard.pusher.com/accounts/sign_up", "env_vars": ["PUSHER_APP_ID", "PUSHER_KEY", "PUSHER_SECRET", "PUSHER_CLUSTER"], "install_cmd": "npm install pusher pusher-js"},
        },
        {
            "slug": "ably", "name": "Ably", "tier": "freemium", "monthly_cost_usd": 0, "category": "realtime",
            "description": "Realtime pub/sub at scale. Better SLA and global edge than Pusher.",
            "execution_type": "api",
            "execution_config": {"signup_url": "https://ably.com/signup", "env_vars": ["ABLY_API_KEY"], "install_cmd": "npm install ably"},
        },
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
