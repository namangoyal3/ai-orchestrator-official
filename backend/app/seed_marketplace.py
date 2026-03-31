"""
Marketplace seed — populates Skills, MCPs, and LLM models on startup if tables are empty.
"""
from sqlalchemy import select, func

from app.database import AsyncSessionLocal
from app.models import Skill, MCP, LLMModel


SEED_SKILLS = [
    ("Prompt Engineering", "Agent Skill", "Design and optimize prompts for large language models to achieve specific outcomes with maximum accuracy.", 9.5, "scraped"),
    ("RAG Pipeline Development", "Agent Skill", "Build retrieval-augmented generation systems that combine vector search with LLM generation for grounded responses.", 9.2, "scraped"),
    ("Fine-Tuning LLMs", "Agent Skill", "Customize pre-trained language models on domain-specific data for improved task performance.", 8.8, "scraped"),
    ("Multi-Agent Orchestration", "Agent Skill", "Coordinate multiple AI agents to collaborate on complex tasks with shared context and goals.", 9.0, "scraped"),
    ("Vector Database Management", "Agent Skill", "Design and manage vector stores for semantic search using Pinecone, Weaviate, or ChromaDB.", 8.5, "scraped"),
    ("Tool Use & Function Calling", "Agent Skill", "Enable LLMs to interact with external APIs and tools through structured function calling interfaces.", 9.1, "scraped"),
    ("Autonomous Agent Design", "Agent Skill", "Architect self-directed AI agents that can plan, execute, and reflect on multi-step tasks.", 8.9, "scraped"),
    ("Conversational AI", "Agent Skill", "Build natural language dialogue systems with context retention and personality adaptation.", 8.3, "scraped"),
    ("Code Generation & Review", "Agent Skill", "Use AI to generate, review, and refactor code across multiple programming languages.", 8.7, "scraped"),
    ("Data Extraction & ETL", "Agent Skill", "Extract structured data from unstructured sources using NLP and pattern recognition techniques.", 8.1, "scraped"),
    ("Semantic Search", "Agent Skill", "Implement meaning-based search systems that understand user intent beyond keyword matching.", 8.4, "scraped"),
    ("AI Safety & Alignment", "Agent Skill", "Implement guardrails, content filtering, and alignment techniques for responsible AI deployment.", 8.6, "scraped"),
    ("Knowledge Graph Construction", "Agent Skill", "Build and query knowledge graphs from unstructured text for relationship discovery and reasoning.", 7.9, "scraped"),
    ("Evaluation & Benchmarking", "Agent Skill", "Design evaluation frameworks and benchmarks to measure LLM performance and reliability.", 7.8, "scraped"),
    ("AI Workflow Automation", "Agent Skill", "Create automated pipelines that chain AI capabilities with business processes for end-to-end automation.", 8.7, "scraped"),
    ("Midjourney", "AI Tool", "AI-powered image generation tool that creates stunning visual art from text descriptions.", 9.0, "futurepedia"),
    ("Cursor", "AI Tool", "AI-first code editor that helps developers write, edit, and understand code faster.", 9.3, "futurepedia"),
    ("Perplexity AI", "AI Tool", "AI-powered search engine that provides direct answers with cited sources.", 8.9, "futurepedia"),
    ("Runway ML", "AI Tool", "Creative AI tools for video generation, editing, and visual effects production.", 8.5, "futurepedia"),
    ("Replit Agent", "AI Tool", "AI assistant for building complete applications through natural language instructions.", 8.7, "futurepedia"),
    ("Hugging Face", "AI Tool", "Open platform for sharing and deploying machine learning models, datasets, and demos.", 9.1, "futurepedia"),
    ("Eleven Labs", "AI Tool", "AI voice synthesis platform for creating realistic speech and voice cloning.", 8.4, "futurepedia"),
    ("Jasper AI", "AI Tool", "AI content creation platform for marketing teams to produce on-brand content at scale.", 7.8, "futurepedia"),
    ("Anthropic Console", "AI Tool", "Developer platform for building with Claude models including prompt engineering and evaluation.", 8.8, "futurepedia"),
    ("Vercel v0", "AI Tool", "AI-powered UI generation tool that creates React components from natural language descriptions.", 8.6, "futurepedia"),
]


SEED_MCPS = [
    ("github", "GitHub MCP", "Access GitHub repositories, issues, PRs, and code search through the Model Context Protocol.", "https://github.com/modelcontextprotocol/servers/tree/main/src/github"),
    ("postgres", "PostgreSQL MCP", "Query and manage PostgreSQL databases with schema inspection and safe read/write operations.", "https://github.com/modelcontextprotocol/servers/tree/main/src/postgres"),
    ("sqlite", "SQLite MCP", "Interact with SQLite databases for lightweight data storage and retrieval.", "https://github.com/modelcontextprotocol/servers/tree/main/src/sqlite"),
    ("google-drive", "Google Drive MCP", "Search, read, and manage files in Google Drive including Docs, Sheets, and Slides.", "https://github.com/modelcontextprotocol/servers/tree/main/src/google-drive"),
    ("slack", "Slack MCP", "Send messages, read channels, and manage Slack workspace interactions.", "https://github.com/modelcontextprotocol/servers/tree/main/src/slack"),
    ("playwright", "Playwright MCP", "Automate web browsers for scraping, testing, and interaction with dynamic web pages.", "https://github.com/modelcontextprotocol/servers/tree/main/src/playwright"),
    ("filesystem", "Filesystem MCP", "Read, write, and manage local files and directories securely.", "https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem"),
    ("memory", "Memory MCP", "Persistent memory storage for maintaining context across conversations and sessions.", "https://github.com/modelcontextprotocol/servers/tree/main/src/memory"),
    ("puppeteer", "Puppeteer MCP", "Control headless Chrome for web scraping, screenshots, and PDF generation.", "https://github.com/modelcontextprotocol/servers/tree/main/src/puppeteer"),
    ("brave-search", "Brave Search MCP", "Privacy-focused web search with AI-friendly structured results.", "https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search"),
    ("fetch", "Fetch MCP", "Make HTTP requests to any URL and return parsed content.", "https://github.com/modelcontextprotocol/servers/tree/main/src/fetch"),
    ("google-maps", "Google Maps MCP", "Geocoding, directions, places search, and distance calculations.", "https://github.com/modelcontextprotocol/servers/tree/main/src/google-maps"),
    ("sentry", "Sentry MCP", "Access error tracking, performance monitoring, and issue management from Sentry.", "https://github.com/modelcontextprotocol/servers/tree/main/src/sentry"),
    ("sequentialthinking", "Sequential Thinking MCP", "Structured step-by-step reasoning for complex problem solving.", "https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking"),
    ("gitlab", "GitLab MCP", "Manage GitLab repositories, merge requests, issues, and CI/CD pipelines.", "https://github.com/modelcontextprotocol/servers/tree/main/src/gitlab"),
    ("redis", "Redis MCP", "Interact with Redis for caching, pub/sub, and key-value data operations.", "https://github.com/modelcontextprotocol/servers/tree/main/src/redis"),
    ("notion", "Notion MCP", "Read and manage Notion pages, databases, and workspace content.", "https://github.com/nicholasgriffintn/notion-mcp-server"),
    ("linear", "Linear MCP", "Manage Linear issues, projects, and engineering workflows.", "https://github.com/jerhadf/linear-mcp-server"),
    ("figma", "Figma MCP", "Access Figma files, components, and design tokens for design-to-code workflows.", "https://github.com/nicholasgriffintn/figma-mcp-server"),
    ("stripe", "Stripe MCP", "Manage Stripe payments, customers, subscriptions, and invoices.", "https://github.com/stripe/stripe-mcp-server"),
    ("supabase", "Supabase MCP", "Full Supabase integration for database, auth, storage, and edge functions.", "https://github.com/supabase/supabase-mcp"),
    ("vercel", "Vercel MCP", "Deploy and manage Vercel projects, domains, and serverless functions.", "https://github.com/nicholasgriffintn/vercel-mcp-server"),
    ("aws", "AWS MCP", "Interact with AWS services including S3, Lambda, DynamoDB, and more.", "https://github.com/aws/aws-mcp-servers"),
    ("docker", "Docker MCP", "Manage Docker containers, images, networks, and compose stacks.", "https://github.com/nicholasgriffintn/docker-mcp-server"),
    ("kubernetes", "Kubernetes MCP", "Deploy and manage Kubernetes clusters, pods, and services.", "https://github.com/nicholasgriffintn/kubernetes-mcp-server"),
    ("mongodb", "MongoDB MCP", "Query and manage MongoDB collections and documents.", "https://github.com/nicholasgriffintn/mongodb-mcp-server"),
    ("elasticsearch", "Elasticsearch MCP", "Full-text search, aggregations, and index management for Elasticsearch.", "https://github.com/nicholasgriffintn/elasticsearch-mcp-server"),
    ("twilio", "Twilio MCP", "Send SMS, make calls, and manage communication workflows.", "https://github.com/nicholasgriffintn/twilio-mcp-server"),
    ("sendgrid", "SendGrid MCP", "Send transactional and marketing emails through SendGrid.", "https://github.com/nicholasgriffintn/sendgrid-mcp-server"),
    ("openai", "OpenAI MCP", "Access OpenAI models for embeddings, completions, and image generation.", "https://github.com/nicholasgriffintn/openai-mcp-server"),
    ("anthropic", "Anthropic MCP", "Integrate Claude models for advanced reasoning and content generation.", "https://github.com/nicholasgriffintn/anthropic-mcp-server"),
    ("jira", "Jira MCP", "Manage Jira issues, sprints, boards, and project workflows.", "https://github.com/nicholasgriffintn/jira-mcp-server"),
    ("confluence", "Confluence MCP", "Search and manage Confluence pages, spaces, and documentation.", "https://github.com/nicholasgriffintn/confluence-mcp-server"),
    ("shopify", "Shopify MCP", "Manage Shopify stores, products, orders, and customer data.", "https://github.com/nicholasgriffintn/shopify-mcp-server"),
    ("hubspot", "HubSpot MCP", "CRM operations including contacts, deals, and marketing automation.", "https://github.com/nicholasgriffintn/hubspot-mcp-server"),
    ("airtable", "Airtable MCP", "Read and manage Airtable bases, tables, and records.", "https://github.com/nicholasgriffintn/airtable-mcp-server"),
    ("discord", "Discord MCP", "Send messages, manage channels, and interact with Discord servers.", "https://github.com/nicholasgriffintn/discord-mcp-server"),
    ("telegram", "Telegram MCP", "Send messages and manage Telegram bot interactions.", "https://github.com/nicholasgriffintn/telegram-mcp-server"),
    ("pinecone", "Pinecone MCP", "Vector database operations for semantic search and RAG pipelines.", "https://github.com/nicholasgriffintn/pinecone-mcp-server"),
]


SEED_LLM_MODELS = [
    ("anthropic/claude-opus-4-6", "Claude Opus 4", "anthropic", "Most capable model for complex reasoning, architecture, and strategy", 200000, 15.0, 75.0),
    ("anthropic/claude-sonnet-4-6", "Claude Sonnet 4", "anthropic", "Balanced model for research, analysis, and code review", 200000, 3.0, 15.0),
    ("anthropic/claude-haiku-4-5", "Claude Haiku 4", "anthropic", "Fast and cost-efficient for simple tasks and high volume", 200000, 0.25, 1.25),
    ("openai/gpt-4o", "GPT-4o", "openai", "Multimodal flagship model with broad knowledge and code generation", 128000, 2.5, 10.0),
    ("openai/gpt-4o-mini", "GPT-4o Mini", "openai", "Fast, affordable model for high-volume and cost-sensitive tasks", 128000, 0.15, 0.6),
    ("google/gemini-2.0-flash", "Gemini 2.0 Flash", "google", "Long context model ideal for document analysis and multimodal tasks", 1000000, 0.075, 0.3),
    ("google/gemini-2.5-pro-preview", "Gemini 2.5 Pro", "google", "Advanced reasoning with million-token context window", 1000000, 1.25, 10.0),
    ("meta-llama/llama-4-maverick", "Llama 4 Maverick", "meta-llama", "Open-weight model with strong reasoning and tool use", 128000, 0.2, 0.6),
    ("deepseek/deepseek-r1", "DeepSeek R1", "deepseek", "Reasoning-focused model with chain-of-thought capabilities", 128000, 0.55, 2.19),
    ("mistralai/mistral-large-2", "Mistral Large 2", "mistralai", "Powerful multilingual model with strong code generation", 128000, 2.0, 6.0),
    ("cohere/command-r-plus", "Command R+", "cohere", "Enterprise-grade model optimized for RAG and tool use", 128000, 2.5, 10.0),
    ("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet", "anthropic", "Previous generation balanced model, still excellent for coding", 200000, 3.0, 15.0),
    ("openai/o3-mini", "o3-mini", "openai", "Reasoning model with adjustable thinking depth", 128000, 1.1, 4.4),
    ("qwen/qwen-2.5-72b", "Qwen 2.5 72B", "qwen", "Strong multilingual model with competitive reasoning", 128000, 0.36, 0.72),
    ("x-ai/grok-3", "Grok 3", "x-ai", "Real-time knowledge model with strong analytical capabilities", 128000, 3.0, 15.0),
]


async def seed_marketplace():
    async with AsyncSessionLocal() as db:
        skill_count = await db.scalar(select(func.count()).select_from(Skill))
        if not skill_count:
            for name, category, description, score, source in SEED_SKILLS:
                db.add(Skill(
                    name=name,
                    category=category,
                    description=description,
                    demand_score=score,
                    source=source,
                ))
            print(f"Seeded {len(SEED_SKILLS)} skills")

        mcp_count = await db.scalar(select(func.count()).select_from(MCP))
        if not mcp_count:
            for slug, name, description, repo_url in SEED_MCPS:
                db.add(MCP(
                    name=name,
                    slug=slug,
                    description=description,
                    repo_url=repo_url,
                    source="mcpmarket",
                    is_active=True,
                ))
            print(f"Seeded {len(SEED_MCPS)} MCP servers")

        llm_count = await db.scalar(select(func.count()).select_from(LLMModel))
        if not llm_count:
            for model_id, display_name, provider, desc, ctx, cost_in, cost_out in SEED_LLM_MODELS:
                db.add(LLMModel(
                    id=model_id,
                    display_name=display_name,
                    provider=provider,
                    description=desc,
                    context_length=ctx,
                    cost_per_1m_input=cost_in,
                    cost_per_1m_output=cost_out,
                    source="openrouter",
                    is_active=True,
                ))
            print(f"Seeded {len(SEED_LLM_MODELS)} LLM models")

        await db.commit()
