"""
Seed script — creates demo org, API key, and sample analytics data on first startup.
"""
import hashlib
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import Organization, APIKey, RequestLog


DEMO_ORG_SLUG = "demo-org"
DEMO_KEY_RAW = "gw-demo-key-change-in-production-12345678"

SAMPLE_PROMPTS = [
    ("Write a Python function to parse JSON from an API response", "coding", "high", "claude-opus-4-6", ["code"], ["github_repo_info"]),
    ("Summarize the key points of transformer architecture", "summarization", "medium", "claude-sonnet-4-6", ["research"], ["web_search"]),
    ("What is the weather like in Mumbai?", "simple_qa", "low", "claude-haiku-4-5-20251001", [], ["weather"]),
    ("Analyze the growth trends in Indian SaaS market 2024", "analysis", "high", "claude-opus-4-6", ["data_analysis"], ["web_search", "web_scrape"]),
    ("Write a blog post about the future of AI agents", "writing", "medium", "claude-sonnet-4-6", ["content_writer"], []),
    ("Extract all email addresses from this document", "extraction", "low", "claude-haiku-4-5-20251001", [], ["extract_entities"]),
    ("Create a 90-day product roadmap for a B2B SaaS", "planning", "high", "claude-opus-4-6", ["planning"], []),
    ("Translate this paragraph to Spanish", "translation", "low", "claude-haiku-4-5-20251001", [], ["translate"]),
    ("Debug this React component that's causing re-renders", "coding", "high", "claude-opus-4-6", ["code"], []),
    ("Research competitors of Stripe in India", "research", "medium", "claude-sonnet-4-6", ["research"], ["web_search", "web_scrape"]),
    ("Classify customer support tickets by urgency", "classification", "low", "claude-haiku-4-5-20251001", ["customer_support"], []),
    ("Build a financial model for a D2C brand", "data_analysis", "high", "claude-opus-4-6", ["data_analysis"], ["calculator"]),
    ("Write unit tests for this authentication module", "coding", "medium", "claude-sonnet-4-6", ["code"], []),
    ("Summarize Q3 earnings report", "document_qa", "medium", "claude-sonnet-4-6", ["document_qa"], ["parse_pdf"]),
    ("What are the best practices for RAG pipelines?", "research", "medium", "claude-sonnet-4-6", ["research"], ["web_search"]),
    ("Generate 10 product name ideas for an AI startup", "writing", "low", "claude-haiku-4-5-20251001", ["content_writer"], []),
    ("Analyze this dataset for anomalies", "data_analysis", "high", "claude-opus-4-6", ["data_analysis"], ["calculator", "json_query"]),
    ("Write API documentation for this endpoint", "writing", "medium", "claude-sonnet-4-6", ["code", "content_writer"], []),
    ("Find the latest news about OpenAI", "research", "low", "claude-haiku-4-5-20251001", ["research"], ["news_search"]),
    ("Plan a go-to-market strategy for Southeast Asia", "planning", "high", "claude-opus-4-6", ["planning", "research"], ["web_search"]),
]


async def seed_database():
    async with AsyncSessionLocal() as db:
        # Check if already seeded
        result = await db.execute(select(Organization).where(Organization.slug == DEMO_ORG_SLUG))
        if result.scalar_one_or_none():
            return

        # Create demo org
        org = Organization(name="Demo Organization", slug=DEMO_ORG_SLUG, plan="pro")
        db.add(org)
        await db.flush()

        # Create demo API key
        key_hash = hashlib.sha256(DEMO_KEY_RAW.encode()).hexdigest()
        api_key = APIKey(
            org_id=org.id,
            name="Demo Key",
            key_hash=key_hash,
            key_prefix="gw-demo",
            permissions=["read", "write", "admin"],
            rate_limit_rpm=1000,
            rate_limit_daily=100000,
        )
        db.add(api_key)
        await db.flush()

        # Seed sample request logs (last 14 days)
        now = datetime.now(timezone.utc).replace(tzinfo=None) # Make naive for Postgres DateTime column
        for i, (prompt, category, complexity, model, agents, tools) in enumerate(SAMPLE_PROMPTS):
            # Spread over last 14 days
            days_ago = random.uniform(0, 14)
            created = now - timedelta(days=days_ago)

            # Realistic metrics
            latency = random.randint(800, 4500)
            input_tokens = random.randint(150, 2000)
            output_tokens = random.randint(200, 3000)
            token_costs = {
                "claude-opus-4-6": (5.00, 25.00),
                "claude-sonnet-4-6": (3.00, 15.00),
                "claude-haiku-4-5-20251001": (1.00, 5.00),
            }
            inp_cost, out_cost = token_costs.get(model, (3.00, 15.00))
            cost = round((input_tokens / 1e6) * inp_cost + (output_tokens / 1e6) * out_cost, 6)

            complexity_score = {"low": 0.3, "medium": 0.6, "high": 0.9}.get(complexity, 0.5)

            log = RequestLog(
                org_id=org.id,
                api_key_id=api_key.id,
                prompt=prompt,
                response=f"[Sample response for: {prompt[:50]}...]",
                status="completed",
                task_category=category,
                complexity_score=complexity_score,
                selected_llm=model,
                selected_agents=agents,
                selected_tools=tools,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                latency_ms=latency,
                created_at=created,
            )
            db.add(log)

        await db.commit()
        print("=" * 60)
        print("DEMO SETUP COMPLETE")
        print(f"Demo API Key: {DEMO_KEY_RAW}")
        print("Use this key in the X-API-Key header to test the API.")
        print("Sample analytics data seeded for the last 14 days.")
        print("=" * 60)
