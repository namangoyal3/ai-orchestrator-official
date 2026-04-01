"""
Marketplace seed — populates Skills, MCPs, and LLM models on startup if tables are empty.
"""
from sqlalchemy import select, func

from app.database import AsyncSessionLocal
from app.models import Skill, MCP, LLMModel


SEED_SKILLS = [
    # ── Agent Skills ──────────────────────────────────────────────────────────
    ("Prompt Engineering",           "Agent Skill", "Design and optimize prompts for large language models to achieve specific outcomes with maximum accuracy.", 9.5, "scraped"),
    ("RAG Pipeline Development",     "Agent Skill", "Build retrieval-augmented generation systems that combine vector search with LLM generation for grounded responses.", 9.2, "scraped"),
    ("Fine-Tuning LLMs",             "Agent Skill", "Customize pre-trained language models on domain-specific data for improved task performance.", 8.8, "scraped"),
    ("Multi-Agent Orchestration",    "Agent Skill", "Coordinate multiple AI agents to collaborate on complex tasks with shared context and goals.", 9.0, "scraped"),
    ("Vector Database Management",   "Agent Skill", "Design and manage vector stores for semantic search using Pinecone, Weaviate, or ChromaDB.", 8.5, "scraped"),
    ("Tool Use & Function Calling",  "Agent Skill", "Enable LLMs to interact with external APIs and tools through structured function calling interfaces.", 9.1, "scraped"),
    ("Autonomous Agent Design",      "Agent Skill", "Architect self-directed AI agents that can plan, execute, and reflect on multi-step tasks.", 8.9, "scraped"),
    ("Conversational AI",            "Agent Skill", "Build natural language dialogue systems with context retention and personality adaptation.", 8.3, "scraped"),
    ("Code Generation & Review",     "Agent Skill", "Use AI to generate, review, and refactor code across multiple programming languages.", 8.7, "scraped"),
    ("Data Extraction & ETL",        "Agent Skill", "Extract structured data from unstructured sources using NLP and pattern recognition techniques.", 8.1, "scraped"),
    ("Semantic Search",              "Agent Skill", "Implement meaning-based search systems that understand user intent beyond keyword matching.", 8.4, "scraped"),
    ("AI Safety & Alignment",        "Agent Skill", "Implement guardrails, content filtering, and alignment techniques for responsible AI deployment.", 8.6, "scraped"),
    ("Knowledge Graph Construction", "Agent Skill", "Build and query knowledge graphs from unstructured text for relationship discovery and reasoning.", 7.9, "scraped"),
    ("Evaluation & Benchmarking",    "Agent Skill", "Design evaluation frameworks and benchmarks to measure LLM performance and reliability.", 7.8, "scraped"),
    ("AI Workflow Automation",       "Agent Skill", "Create automated pipelines that chain AI capabilities with business processes for end-to-end automation.", 8.7, "scraped"),
    ("Document Intelligence",        "Agent Skill", "Extract insights, summaries, and structured data from PDFs, contracts, and long-form documents.", 8.5, "scraped"),
    ("Multimodal AI",                "Agent Skill", "Build systems that reason across text, images, audio, and video using multimodal models.", 8.8, "scraped"),
    ("LLM Observability",            "Agent Skill", "Instrument AI systems with tracing, logging, and evaluation for production reliability.", 8.2, "scraped"),
    ("Streaming Inference",          "Agent Skill", "Implement real-time token streaming for responsive AI-powered user interfaces.", 7.9, "scraped"),
    ("Context Window Management",    "Agent Skill", "Optimize long-context handling with chunking, summarization, and sliding window strategies.", 8.3, "scraped"),
    ("Chain-of-Thought Reasoning",   "Agent Skill", "Apply structured reasoning techniques to improve LLM accuracy on complex problems.", 8.9, "scraped"),
    ("AI-Powered Search",            "Agent Skill", "Build hybrid search systems combining dense vector retrieval with sparse keyword matching.", 8.6, "scraped"),
    ("Structured Output Parsing",    "Agent Skill", "Extract reliable JSON and typed outputs from LLMs using constrained decoding and validation.", 8.4, "scraped"),
    ("Agent Memory Systems",         "Agent Skill", "Design short-term and long-term memory architectures for persistent AI agent state.", 8.7, "scraped"),
    ("LLM Caching & Cost Control",   "Agent Skill", "Reduce inference costs with semantic caching, prompt deduplication, and model routing.", 8.0, "scraped"),
    ("AI Code Interpreter",          "Agent Skill", "Build safe code execution sandboxes for AI agents to run Python, SQL, and shell commands.", 8.5, "scraped"),
    ("Guardrails & Content Moderation","Agent Skill","Implement output filtering, toxicity detection, and policy enforcement for AI applications.", 8.6, "scraped"),
    ("AI Data Labeling",             "Agent Skill", "Build active learning pipelines and human-in-the-loop systems for training data generation.", 7.7, "scraped"),
    ("LLM API Gateway",              "Agent Skill", "Design proxy layers for model routing, rate limiting, cost tracking, and API key management.", 8.8, "scraped"),
    ("Synthetic Data Generation",    "Agent Skill", "Generate realistic training data using LLMs to augment scarce real-world datasets.", 8.1, "scraped"),
    # ── AI Tools ─────────────────────────────────────────────────────────────
    ("Midjourney",        "AI Tool", "AI-powered image generation tool that creates stunning visual art from text descriptions.", 9.0, "futurepedia"),
    ("Cursor",            "AI Tool", "AI-first code editor that helps developers write, edit, and understand code faster.", 9.3, "futurepedia"),
    ("Perplexity AI",     "AI Tool", "AI-powered search engine that provides direct answers with cited sources.", 8.9, "futurepedia"),
    ("Runway ML",         "AI Tool", "Creative AI tools for video generation, editing, and visual effects production.", 8.5, "futurepedia"),
    ("Replit Agent",      "AI Tool", "AI assistant for building complete applications through natural language instructions.", 8.7, "futurepedia"),
    ("Hugging Face",      "AI Tool", "Open platform for sharing and deploying machine learning models, datasets, and demos.", 9.1, "futurepedia"),
    ("Eleven Labs",       "AI Tool", "AI voice synthesis platform for creating realistic speech and voice cloning.", 8.4, "futurepedia"),
    ("Jasper AI",         "AI Tool", "AI content creation platform for marketing teams to produce on-brand content at scale.", 7.8, "futurepedia"),
    ("Anthropic Console", "AI Tool", "Developer platform for building with Claude models including prompt engineering and evaluation.", 8.8, "futurepedia"),
    ("Vercel v0",         "AI Tool", "AI-powered UI generation tool that creates React components from natural language descriptions.", 8.6, "futurepedia"),
    ("Stable Diffusion",  "AI Tool", "Open-source image generation model that runs locally or in the cloud.", 8.7, "futurepedia"),
    ("LangChain",         "AI Tool", "Framework for building LLM-powered applications with chains, agents, and memory.", 9.0, "futurepedia"),
    ("LangGraph",         "AI Tool", "Graph-based agent orchestration framework for building stateful multi-agent workflows.", 8.8, "futurepedia"),
    ("CrewAI",            "AI Tool", "Multi-agent framework for role-based AI teams that collaborate on complex tasks.", 8.6, "futurepedia"),
    ("AutoGen",           "AI Tool", "Microsoft framework for building conversational multi-agent AI systems.", 8.5, "futurepedia"),
    ("LlamaIndex",        "AI Tool", "Data framework for connecting custom data sources to large language models.", 9.0, "futurepedia"),
    ("Weaviate",          "AI Tool", "Open-source vector database with built-in ML model integration.", 8.4, "futurepedia"),
    ("Chroma",            "AI Tool", "Lightweight open-source embedding database for AI-native applications.", 8.2, "futurepedia"),
    ("Pinecone",          "AI Tool", "Managed vector database for production-scale semantic search and RAG.", 8.5, "futurepedia"),
    ("Qdrant",            "AI Tool", "High-performance vector search engine with filtering and payload storage.", 8.3, "futurepedia"),
    ("Weights & Biases",  "AI Tool", "MLOps platform for experiment tracking, model versioning, and evaluation.", 8.7, "futurepedia"),
    ("Modal",             "AI Tool", "Serverless cloud platform for running AI inference and training workloads.", 8.4, "futurepedia"),
    ("Replicate",         "AI Tool", "Run and fine-tune open-source ML models via API without managing infrastructure.", 8.3, "futurepedia"),
    ("Together AI",       "AI Tool", "Fast inference API for open-source LLMs with fine-tuning support.", 8.2, "futurepedia"),
    ("Groq",              "AI Tool", "Ultra-fast LLM inference hardware and API for latency-critical applications.", 8.6, "futurepedia"),
    ("Ollama",            "AI Tool", "Run large language models locally on your own hardware with a simple API.", 8.8, "futurepedia"),
    ("LiteLLM",           "AI Tool", "Unified API proxy for 100+ LLM providers with cost tracking and fallbacks.", 8.5, "futurepedia"),
    ("Dify",              "AI Tool", "Open-source LLMOps platform for building production AI applications and workflows.", 8.4, "futurepedia"),
    ("Flowise",           "AI Tool", "Drag-and-drop UI for building LangChain and LlamaIndex flows visually.", 8.1, "futurepedia"),
    ("n8n",               "AI Tool", "Open-source workflow automation with native AI node integrations.", 8.3, "futurepedia"),
    ("Zapier AI",         "AI Tool", "AI-powered automation connecting 6000+ apps with natural language triggers.", 8.0, "futurepedia"),
    ("Relevance AI",      "AI Tool", "No-code platform for building AI agents and automations for business workflows.", 7.9, "futurepedia"),
    ("OpenRouter",        "AI Tool", "Unified API routing across 200+ AI models with automatic fallback and cost optimization.", 8.7, "futurepedia"),
    ("Helicone",          "AI Tool", "Open-source LLM observability platform with request logging and analytics.", 8.1, "futurepedia"),
    ("Langfuse",          "AI Tool", "Open-source LLM engineering platform for tracing, evals, and prompt management.", 8.3, "futurepedia"),
    ("PromptLayer",       "AI Tool", "Prompt versioning, testing, and analytics platform for LLM applications.", 7.8, "futurepedia"),
    ("Instructor",        "AI Tool", "Python library for structured LLM outputs using Pydantic models.", 8.5, "futurepedia"),
    ("Outlines",          "AI Tool", "Structured text generation library with regex and JSON schema constraints.", 8.2, "futurepedia"),
    ("Guardrails AI",     "AI Tool", "Input/output validation framework for reliable and safe LLM responses.", 8.0, "futurepedia"),
    ("Haystack",          "AI Tool", "End-to-end NLP framework for building search systems and RAG pipelines.", 8.4, "futurepedia"),
    ("DSPy",              "AI Tool", "Stanford framework for programming language models with automatic optimization.", 8.6, "futurepedia"),
    ("Magentic",          "AI Tool", "Pythonic interface for integrating LLMs into functions using decorators.", 7.9, "futurepedia"),
    ("Agentops",          "AI Tool", "AI agent monitoring platform with session replay and cost tracking.", 7.8, "futurepedia"),
    ("Composio",          "AI Tool", "100+ pre-built tool integrations for AI agents with managed auth.", 8.3, "futurepedia"),
    ("E2B",               "AI Tool", "Secure cloud sandboxes for AI-generated code execution and computer use.", 8.4, "futurepedia"),
    ("BrowserBase",       "AI Tool", "Headless browser infrastructure for AI agents that need to browse the web.", 8.1, "futurepedia"),
    ("Firecrawl",         "AI Tool", "Web scraping API that converts websites into clean markdown for LLM ingestion.", 8.2, "futurepedia"),
    ("Jina AI",           "AI Tool", "Multimodal embedding and reranking APIs for building neural search systems.", 8.0, "futurepedia"),
    ("Cohere",            "AI Tool", "Enterprise NLP platform with embeddings, reranking, and command models.", 8.3, "futurepedia"),
    ("Mistral AI",        "AI Tool", "Open-weight and API models with strong multilingual and code capabilities.", 8.5, "futurepedia"),
    ("Together Inference","AI Tool", "High-throughput open-source model serving with fine-tuning pipelines.", 8.1, "futurepedia"),
    ("Cerebras",          "AI Tool", "Wafer-scale AI chip delivering 20x faster inference than GPU clusters.", 8.0, "futurepedia"),
    ("Scale AI",          "AI Tool", "Data labeling, RLHF, and enterprise AI fine-tuning platform.", 8.2, "futurepedia"),
    ("Galileo AI",        "AI Tool", "LLM evaluation and hallucination detection platform for production AI.", 7.9, "futurepedia"),
    ("Arize AI",          "AI Tool", "ML observability and LLM tracing platform for production model monitoring.", 8.0, "futurepedia"),
    ("Portkey",           "AI Tool", "AI gateway with 200+ model integrations, caching, and observability.", 8.2, "futurepedia"),
    ("Azure AI Studio",   "AI Tool", "Microsoft platform for building, fine-tuning, and deploying AI models.", 8.3, "futurepedia"),
    ("AWS Bedrock",       "AI Tool", "Fully managed service for foundation models from Anthropic, Meta, and Mistral.", 8.4, "futurepedia"),
    ("Google Vertex AI",  "AI Tool", "Enterprise ML platform with Gemini, PaLM, and custom model training.", 8.3, "futurepedia"),
    ("Cloudflare AI",     "AI Tool", "Edge AI inference with Workers AI for low-latency global model serving.", 8.0, "futurepedia"),
    ("Supabase pgvector", "AI Tool", "Postgres vector extension for storing and querying embeddings in Supabase.", 8.4, "futurepedia"),
    ("Neon",              "AI Tool", "Serverless Postgres with branching and auto-scaling for AI applications.", 8.1, "futurepedia"),
    ("Upstash",           "AI Tool", "Serverless Redis and Kafka for AI pipelines with per-request billing.", 8.0, "futurepedia"),
    ("Inngest",           "AI Tool", "Event-driven serverless queues for durable AI workflow execution.", 8.2, "futurepedia"),
    ("Trigger.dev",       "AI Tool", "Open-source background job platform for long-running AI tasks.", 8.1, "futurepedia"),
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
