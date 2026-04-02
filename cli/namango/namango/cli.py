#!/usr/bin/env python3
"""
Namango — AI Stack Intelligence for Product Builders
=====================================================
Fetches Namango's curated catalog of real product-building tools,
selects the best stack for your product idea, asks OSS vs premium
preference, then generates a detailed stack blueprint + writes
CLAUDE.md, .env.example, and install.sh to ./namango-output/.

Usage:
    namango init "build a customer support helpdesk for a Zomato-like app"
    namango init                      # interactive prompt
    namango init "my idea" --output ./my-project
    namango init "my idea" --compare  # show OSS vs Cloud side-by-side

GATEWAY_URL and API_KEY can also be set as env vars.
"""
from __future__ import annotations

import os
import sys
import json
import time
import re
import json
import argparse
import textwrap
import shutil
from pathlib import Path
import httpx

# ── Config ───────────────────────────────────────────────────────────────────
DEFAULT_GATEWAY = os.getenv("GATEWAY_URL", "https://ai-gateway-backend-production.up.railway.app")
DEFAULT_KEY     = os.getenv("API_KEY", "gw-demo-key-change-in-production-12345678")
DEFAULT_MODEL   = "meta-llama/llama-3.1-70b-instruct"

# ── ANSI ─────────────────────────────────────────────────────────────────────
R = "\033[0m"
BOLD = "\033[1m"
DIM  = "\033[2m"
CYAN = "\033[36m"; BCYAN  = "\033[96m"
GRN  = "\033[32m"; BGRN   = "\033[92m"
YLW  = "\033[33m"; BYLW   = "\033[93m"
MAG  = "\033[35m"; BMAG   = "\033[95m"
BLU  = "\033[34m"; BBLU   = "\033[94m"
RED  = "\033[31m"
WHT  = "\033[97m"

# ── Embedded Stack Catalog ────────────────────────────────────────────────────
# Curated real product-building tools organized by category.
# Used as fallback when the live /v1/stacks endpoint is unavailable.
# Keep in sync with backend/app/api/stacks.py STACK_CATALOG.
STACK_CATALOG: dict[str, list[dict]] = {
    "web": [
        {"slug": "fastapi",  "name": "FastAPI",    "description": "High-performance async Python web framework",   "tier": "free",     "monthly_cost_usd": 0,  "category": "web"},
        {"slug": "django",   "name": "Django",     "description": "Batteries-included Python web framework",        "tier": "free",     "monthly_cost_usd": 0,  "category": "web"},
        {"slug": "express",  "name": "Express.js", "description": "Minimal, flexible Node.js web framework",        "tier": "free",     "monthly_cost_usd": 0,  "category": "web"},
        {"slug": "nextjs",   "name": "Next.js",    "description": "React framework with SSR and API routes",        "tier": "free",     "monthly_cost_usd": 0,  "category": "web"},
        {"slug": "flask",    "name": "Flask",      "description": "Lightweight Python web microframework",          "tier": "free",     "monthly_cost_usd": 0,  "category": "web"},
        {"slug": "react",    "name": "React",      "description": "UI library for building component-based frontends", "tier": "free",     "monthly_cost_usd": 0,  "category": "web"},
        {"slug": "tailwind", "name": "Tailwind CSS","description": "Utility-first CSS framework, pairs with any JS framework","tier": "free","monthly_cost_usd": 0,"category": "web"},
        {"slug": "shadcn",   "name": "shadcn/ui",  "description": "Copy-paste accessible React components built on Radix","tier": "free","monthly_cost_usd": 0, "category": "web"},
        {"slug": "vite",     "name": "Vite",       "description": "Fast frontend build tool and dev server for React/Vue", "tier": "free","monthly_cost_usd": 0, "category": "web"},
    ],
    "database": [
        {"slug": "postgresql",  "name": "PostgreSQL",  "description": "Reliable open-source relational database",           "tier": "free",     "monthly_cost_usd": 0,  "category": "database"},
        {"slug": "mongodb",     "name": "MongoDB",     "description": "Flexible NoSQL document database",                    "tier": "freemium", "monthly_cost_usd": 0,  "category": "database"},
        {"slug": "sqlite",      "name": "SQLite",      "description": "Zero-config embedded SQL, perfect for prototyping",   "tier": "free",     "monthly_cost_usd": 0,  "category": "database"},
        {"slug": "supabase",    "name": "Supabase",    "description": "Open-source Firebase with Postgres + Auth + Storage", "tier": "freemium", "monthly_cost_usd": 0,  "category": "database"},
        {"slug": "planetscale", "name": "PlanetScale", "description": "Serverless MySQL with branching for safe migrations", "tier": "freemium", "monthly_cost_usd": 0,  "category": "database"},
    ],
    "cache": [
        {"slug": "redis",   "name": "Redis",         "description": "In-memory cache, sessions, pub/sub messaging",  "tier": "free",     "monthly_cost_usd": 0, "category": "cache"},
        {"slug": "upstash", "name": "Upstash Redis",  "description": "Serverless Redis, pay-per-request pricing",    "tier": "freemium", "monthly_cost_usd": 0, "category": "cache"},
    ],
    "queue": [
        {"slug": "celery",   "name": "Celery",    "description": "Distributed task queue for Python with Redis/RabbitMQ", "tier": "free",     "monthly_cost_usd": 0, "category": "queue"},
        {"slug": "bullmq",   "name": "BullMQ",    "description": "Redis-backed job queue for Node.js",                    "tier": "free",     "monthly_cost_usd": 0, "category": "queue"},
        {"slug": "inngest",  "name": "Inngest",   "description": "Event-driven serverless background jobs",                "tier": "freemium", "monthly_cost_usd": 0, "category": "queue"},
        {"slug": "rabbitmq", "name": "RabbitMQ",  "description": "Message broker for distributed systems",                "tier": "free",     "monthly_cost_usd": 0, "category": "queue"},
    ],
    "auth": [
        {"slug": "jwt",           "name": "JWT",           "description": "Stateless token-based auth — zero infra",       "tier": "free",     "monthly_cost_usd": 0,  "category": "auth"},
        {"slug": "auth0",         "name": "Auth0",         "description": "Identity platform — OAuth, OIDC, SAML, MFA",    "tier": "freemium", "monthly_cost_usd": 23, "category": "auth"},
        {"slug": "supabase-auth", "name": "Supabase Auth", "description": "Open-source auth with social login and RLS",    "tier": "freemium", "monthly_cost_usd": 0,  "category": "auth"},
        {"slug": "clerk",         "name": "Clerk",         "description": "Drop-in auth UI components for React/Next.js",  "tier": "freemium", "monthly_cost_usd": 0,  "category": "auth"},
        {"slug": "nextauth",      "name": "NextAuth.js",   "description": "Auth for Next.js with 50+ OAuth providers",     "tier": "free",     "monthly_cost_usd": 0,  "category": "auth"},
    ],
    "payments": [
        {"slug": "stripe",       "name": "Stripe",        "description": "Payments, subscriptions, invoices, Connect",    "tier": "paid", "monthly_cost_usd": 0, "category": "payments"},
        {"slug": "razorpay",     "name": "Razorpay",      "description": "Indian payments — UPI, cards, net banking, EMI","tier": "paid", "monthly_cost_usd": 0, "category": "payments"},
        {"slug": "paddle",       "name": "Paddle",        "description": "Merchant of record — handles global tax/VAT",   "tier": "paid", "monthly_cost_usd": 0, "category": "payments"},
        {"slug": "lemonsqueezy", "name": "Lemon Squeezy", "description": "Payments and subscriptions for indie SaaS",     "tier": "paid", "monthly_cost_usd": 0, "category": "payments"},
    ],
    "email": [
        {"slug": "sendgrid", "name": "SendGrid", "description": "Transactional email API, 100 emails/day free",      "tier": "freemium", "monthly_cost_usd": 0,  "category": "email"},
        {"slug": "resend",   "name": "Resend",   "description": "Developer-first email with React Email templates",   "tier": "freemium", "monthly_cost_usd": 0,  "category": "email"},
        {"slug": "postmark", "name": "Postmark", "description": "Best deliverability for transactional email",        "tier": "paid",     "monthly_cost_usd": 15, "category": "email"},
        {"slug": "mailgun",  "name": "Mailgun",  "description": "Email API with advanced analytics and logging",      "tier": "freemium", "monthly_cost_usd": 0,  "category": "email"},
    ],
    "notifications": [
        {"slug": "twilio",       "name": "Twilio",       "description": "SMS, WhatsApp, and voice notifications API",     "tier": "paid",     "monthly_cost_usd": 0, "category": "notifications"},
        {"slug": "firebase-fcm", "name": "Firebase FCM", "description": "Free push notifications — iOS, Android, web",    "tier": "freemium", "monthly_cost_usd": 0, "category": "notifications"},
        {"slug": "onesignal",    "name": "OneSignal",    "description": "Push, email, SMS, in-app — all in one",           "tier": "freemium", "monthly_cost_usd": 0, "category": "notifications"},
    ],
    "deploy": [
        {"slug": "railway", "name": "Railway",  "description": "Deploy anything with Git push, $5/mo hobby tier",   "tier": "freemium", "monthly_cost_usd": 5, "category": "deploy"},
        {"slug": "vercel",  "name": "Vercel",   "description": "Frontend + serverless, generous free tier",          "tier": "freemium", "monthly_cost_usd": 0, "category": "deploy"},
        {"slug": "render",  "name": "Render",   "description": "Full-stack cloud — web services, workers, cron, DB", "tier": "freemium", "monthly_cost_usd": 7, "category": "deploy"},
        {"slug": "fly",     "name": "Fly.io",   "description": "Run Docker apps globally with edge deployment",      "tier": "freemium", "monthly_cost_usd": 0, "category": "deploy"},
        {"slug": "docker",  "name": "Docker",   "description": "Container packaging and local development runtime",  "tier": "free",     "monthly_cost_usd": 0, "category": "deploy"},
    ],
    "ai": [
        {"slug": "openai",    "name": "OpenAI API",       "description": "GPT-4o, embeddings, vision, Whisper",       "tier": "paid",     "monthly_cost_usd": 20, "category": "ai"},
        {"slug": "anthropic", "name": "Anthropic Claude", "description": "Claude 3.5 — reasoning, long context, code","tier": "paid",     "monthly_cost_usd": 15, "category": "ai"},
        {"slug": "groq",      "name": "Groq",             "description": "Ultra-fast inference — Llama3, Mixtral free","tier": "freemium", "monthly_cost_usd": 0,  "category": "ai"},
        {"slug": "ollama",    "name": "Ollama",           "description": "Run LLMs locally — Llama3, Mistral, Phi3",  "tier": "free",     "monthly_cost_usd": 0,  "category": "ai"},
        {"slug": "langchain", "name": "LangChain",        "description": "LLM application framework and LCEL",        "tier": "free",     "monthly_cost_usd": 0,  "category": "ai"},
        {"slug": "pinecone",  "name": "Pinecone",         "description": "Managed vector DB for semantic search/RAG", "tier": "freemium", "monthly_cost_usd": 0,  "category": "ai"},
    ],
    "storage": [
        {"slug": "s3",               "name": "AWS S3",           "description": "Object storage for files, media, backups",   "tier": "paid",     "monthly_cost_usd": 2, "category": "storage"},
        {"slug": "cloudinary",       "name": "Cloudinary",       "description": "Image/video transform, optimization, CDN",   "tier": "freemium", "monthly_cost_usd": 0, "category": "storage"},
        {"slug": "supabase-storage", "name": "Supabase Storage", "description": "S3-compatible storage with RLS access ctrl", "tier": "freemium", "monthly_cost_usd": 0, "category": "storage"},
        {"slug": "r2",               "name": "Cloudflare R2",    "description": "Zero-egress S3-compatible object storage",   "tier": "freemium", "monthly_cost_usd": 0, "category": "storage"},
    ],
    "monitoring": [
        {"slug": "sentry",  "name": "Sentry",  "description": "Error tracking, performance monitoring, session replay", "tier": "freemium", "monthly_cost_usd": 0,  "category": "monitoring"},
        {"slug": "posthog", "name": "PostHog", "description": "Open-source analytics, feature flags, A/B tests",        "tier": "freemium", "monthly_cost_usd": 0,  "category": "monitoring"},
        {"slug": "datadog", "name": "Datadog", "description": "Full-stack observability — metrics, APM, logs",           "tier": "paid",     "monthly_cost_usd": 31, "category": "monitoring"},
        {"slug": "grafana", "name": "Grafana", "description": "Open-source metrics and log visualization dashboards",    "tier": "freemium", "monthly_cost_usd": 0,  "category": "monitoring"},
    ],
    "search": [
        {"slug": "elasticsearch", "name": "Elasticsearch", "description": "Distributed full-text search and analytics",   "tier": "freemium", "monthly_cost_usd": 0, "category": "search"},
        {"slug": "algolia",       "name": "Algolia",       "description": "Search as a service — instant, typo-tolerant", "tier": "freemium", "monthly_cost_usd": 0, "category": "search"},
        {"slug": "typesense",     "name": "Typesense",     "description": "Open-source instant search, self-hostable",    "tier": "free",     "monthly_cost_usd": 0, "category": "search"},
    ],
    "realtime": [
        {"slug": "websockets", "name": "WebSockets", "description": "Native real-time bidirectional communication",   "tier": "free",     "monthly_cost_usd": 0, "category": "realtime"},
        {"slug": "pusher",     "name": "Pusher",     "description": "Hosted WebSocket, 200k messages/day free",       "tier": "freemium", "monthly_cost_usd": 0, "category": "realtime"},
        {"slug": "socket-io",  "name": "Socket.IO",  "description": "WebSocket library with rooms and namespaces",   "tier": "free",     "monthly_cost_usd": 0, "category": "realtime"},
    ],
}


# ── Terminal helpers ──────────────────────────────────────────────────────────

def _term_width() -> int:
    return max(60, min(80, shutil.get_terminal_size(fallback=(80, 24)).columns - 4))


_ANSI_RE = re.compile(r'\033\[[0-9;]*m')

def _strip_ansi(s: str) -> str:
    return _ANSI_RE.sub('', s)

def _vis(s: str) -> int:
    """Visible terminal width of a string: strip ANSI, count wide chars as 2."""
    plain = _strip_ansi(s)
    w = 0
    for ch in plain:
        cp = ord(ch)
        # Wide unicode ranges: CJK, emoji, enclosed alphanumerics, misc symbols
        if (0x1100 <= cp <= 0x115F or 0x2329 <= cp <= 0x232A or
                0x2E80 <= cp <= 0x3247 or 0x3250 <= cp <= 0x4DBF or
                0x4E00 <= cp <= 0xA4C6 or 0xA960 <= cp <= 0xA97C or
                0xAC00 <= cp <= 0xD7A3 or 0xF900 <= cp <= 0xFAFF or
                0xFE10 <= cp <= 0xFE19 or 0xFE30 <= cp <= 0xFE6B or
                0xFF01 <= cp <= 0xFF60 or 0xFFE0 <= cp <= 0xFFE6 or
                0x1B000 <= cp <= 0x1B001 or 0x1F004 <= cp <= 0x1F0CF or
                0x1F18E <= cp <= 0x1F9FF or 0x20000 <= cp <= 0x2FFFD or
                0x30000 <= cp <= 0x3FFFD):
            w += 2
        elif cp == 0xFE0F:  # variation selector (makes emoji wide) — skip
            pass
        else:
            w += 1
    return w

def _pad_to(s: str, target: int, fill: str = " ") -> str:
    """Pad string s (which may contain ANSI) to target visible width."""
    need = target - _vis(s)
    return s + fill * max(0, need)


# ── Context Questions ─────────────────────────────────────────────────────────

def gather_context() -> dict:
    """
    Ask 6 targeted product questions before stack selection.
    Returns a dict with keys: product_type, scale, seo, deployment, structure, team_size.
    Pressing Enter uses the default (option 1).
    """
    W = _term_width()
    print(f"\n  {CYAN}{'─'*(W-2)}{R}")
    print(f"  {BOLD}A few quick questions to tailor your stack:{R}")
    print(f"  {DIM}Press Enter to accept the default for each.{R}\n")

    menus = [
        ("product_type", "What type of product is this?", [
            "B2B SaaS",
            "B2C consumer app",
            "Internal / team tool",
            "API / service / SDK",
        ]),
        ("scale", "Expected scale at launch?", [
            "MVP / prototype  (< 100 users)",
            "Early-stage      (< 10k users)",
            "Scale-up         (10k–100k users)",
            "Enterprise       (100k+ users)",
        ]),
        ("seo", "Does this need SEO / server-side rendering?", [
            "No  — dashboard, SPA, or internal tool",
            "Yes — public-facing marketing or content site",
        ]),
        ("team_size", "Team size?", [
            "Solo founder",
            "Small  (2–5 people)",
            "Medium (5–20 people)",
            "Large  (20+ people)",
        ]),
    ]

    ctx: dict = {}
    for key, question, options in menus:
        print(f"  {BOLD}{question}{R}")
        for i, opt in enumerate(options, 1):
            print(f"    {CYAN}[{i}]{R} {opt}")
        try:
            raw = input(f"\n  {DIM}Enter number (default 1):{R}  ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            ctx[key] = options[0]
            continue
        try:
            idx = int(raw) - 1
            ctx[key] = options[idx] if 0 <= idx < len(options) else options[0]
        except ValueError:
            ctx[key] = options[0]
        print()

    print(f"  {CYAN}{'─'*(W-2)}{R}\n")
    return ctx


# ── Marketplace Fetch ─────────────────────────────────────────────────────────

def fetch_marketplace_agents_and_tools(url: str, key: str) -> tuple[list[dict], list[dict]]:
    """
    Fetch the built-in agents and tools from the gateway marketplace.
    Used to include OSS agent/tool options in stack recommendations.
    Returns (agents, tools) — both lists of dicts with slug/name/description.
    """
    agents: list[dict] = []
    tools:  list[dict] = []
    try:
        r = httpx.get(f"{url}/v1/marketplace/agents", headers={"X-API-Key": key}, timeout=5.0)
        if r.status_code == 200:
            agents = r.json().get("agents", [])
    except Exception:
        pass
    try:
        r = httpx.get(f"{url}/v1/marketplace/tools", headers={"X-API-Key": key}, timeout=5.0)
        if r.status_code == 200:
            tools = r.json().get("tools", [])
    except Exception:
        pass
    return agents, tools


# ── Marketplace Picker Step ───────────────────────────────────────────────────

def pick_marketplace_items(
    url: str,
    key: str,
    user_prompt: str,
    selected_stack: list[dict],
    marketplace_agents: list[dict],
    marketplace_tools: list[dict],
) -> tuple[list[dict], list[dict]]:
    """
    LLM pre-selects relevant marketplace agents/tools for the product, then
    shows them to the user with toggle controls (enter to confirm, type to edit).
    Returns (confirmed_agents, confirmed_tools).
    """
    if not marketplace_agents and not marketplace_tools:
        return [], []

    # Call /v1/architect/design to get marketplace + catalog suggestions from the backend
    pre_selected_agent_slugs: set[str] = set()
    pre_selected_tool_slugs:  set[str] = set()

    try:
        architect_payload = {
            "prompt": user_prompt,
            "optimization": "cost",
        }
        resp = httpx.post(
            f"{url}/v1/architect/design",
            json=architect_payload,
            headers={"X-API-Key": key, "Content-Type": "application/json"},
            timeout=30.0,
        )
        if resp.status_code == 200:
            data = resp.json()
            pre_selected_agent_slugs = set(data.get("recommended_agents", []))
            pre_selected_tool_slugs  = set(data.get("recommended_mcps", []))
    except Exception:
        pass

    # Map slug matches → index positions in the displayed lists
    def _slug_match(item: dict, slugs: set[str]) -> bool:
        slug = (item.get("slug") or item.get("name") or "").lower().replace(" ", "-")
        name = (item.get("name") or "").lower()
        return any(s.lower() in slug or s.lower() in name or slug in s.lower() for s in slugs)

    pre_selected_agent_idxs = [i for i, a in enumerate(marketplace_agents[:20]) if _slug_match(a, pre_selected_agent_slugs)]
    pre_selected_tool_idxs  = [i for i, t in enumerate(marketplace_tools[:20])  if _slug_match(t, pre_selected_tool_slugs)]

    # Fallback: pre-select first 3 if architect returned nothing
    if not pre_selected_agent_idxs and not pre_selected_tool_idxs:
        pre_selected_agent_idxs = list(range(min(3, len(marketplace_agents))))
        pre_selected_tool_idxs  = list(range(min(3, len(marketplace_tools))))

    W = _term_width()
    print(f"\n  {CYAN}{'─' * (W - 4)}{R}")
    print(f"  {BOLD}🛒  Marketplace Picker{R}  {DIM}— select agents & tools to wire into your architecture{R}")
    print(f"  {CYAN}{'─' * (W - 4)}{R}\n")

    # Show agents
    selected_agent_idxs = set(pre_selected_agent_idxs)
    selected_tool_idxs  = set(pre_selected_tool_idxs)

    def _print_items(items: list[dict], selected_idxs: set, label: str) -> None:
        print(f"  {BOLD}{label}{R}")
        for i, item in enumerate(items[:20]):
            check = f"{BGRN}[✓]{R}" if i in selected_idxs else f"{DIM}[ ]{R}"
            cat   = item.get("category", "")
            name  = item.get("name", "?")
            desc  = (item.get("description") or "")[:60]
            print(f"  {check} {BOLD}{i+1:>2}.{R} {name:<22} {DIM}{cat:<18}{R} {DIM}{desc}{R}")
        print()

    _print_items(marketplace_agents[:20], selected_agent_idxs, "Agents")
    _print_items(marketplace_tools[:20],  selected_tool_idxs,  "Tools")

    print(f"  {DIM}Press {R}{BOLD}Enter{R}{DIM} to confirm, or type agent/tool numbers to toggle "
          f"(e.g. {R}{BOLD}a1,a3,t2{R}{DIM} to toggle agent 1, agent 3, tool 2):{R} ", end="", flush=True)

    try:
        raw = input().strip()
        if raw:
            for token in re.split(r"[,\s]+", raw.lower()):
                m = re.match(r'([at])(\d+)', token)
                if m:
                    kind, num = m.group(1), int(m.group(2)) - 1
                    if kind == "a" and 0 <= num < len(marketplace_agents):
                        if num in selected_agent_idxs:
                            selected_agent_idxs.discard(num)
                        else:
                            selected_agent_idxs.add(num)
                    elif kind == "t" and 0 <= num < len(marketplace_tools):
                        if num in selected_tool_idxs:
                            selected_tool_idxs.discard(num)
                        else:
                            selected_tool_idxs.add(num)
    except (EOFError, KeyboardInterrupt):
        pass

    confirmed_agents = [marketplace_agents[i] for i in sorted(selected_agent_idxs) if i < len(marketplace_agents)]
    confirmed_tools  = [marketplace_tools[i]  for i in sorted(selected_tool_idxs)  if i < len(marketplace_tools)]

    print(f"\n  {BGRN}✓  Marketplace picks confirmed:{R}")
    if confirmed_agents:
        print(f"     {BOLD}Agents:{R}  {', '.join(a.get('name','?') for a in confirmed_agents)}")
    if confirmed_tools:
        print(f"     {BOLD}Tools:{R}   {', '.join(t.get('name','?') for t in confirmed_tools)}")
    if not confirmed_agents and not confirmed_tools:
        print(f"     {DIM}None selected — skipping marketplace wiring.{R}")
    print()

    return confirmed_agents, confirmed_tools


# ── Confirmation Step ─────────────────────────────────────────────────────────

def confirm_understanding(
    url: str,
    key: str,
    user_prompt: str,
    context: dict,
    selected_tools: list[dict],
) -> bool:
    """
    Relay-style confirmation: show what we understood and ask the user
    to confirm before generating the full blueprint. Returns True to proceed.
    """
    W = _term_width()

    # Build a short confirmation message from context + selected tools
    tool_names = ", ".join(t["name"] for t in selected_tools[:5])
    seo_note = "with SSR for SEO" if "Yes" in context.get("seo", "") else "no SSR needed"
    deploy_short = context.get("deployment", "").split("(")[0].strip()

    # Ask the LLM to summarise understanding in 2-3 sentences, Relay-style
    summary_prompt = (
        f"The developer wants to: {user_prompt}\n\n"
        f"Product context:\n"
        f"- Type: {context.get('product_type','')}\n"
        f"- Scale: {context.get('scale','')}\n"
        f"- SEO: {context.get('seo','')}\n"
        f"- Deployment: {context.get('deployment','')}\n"
        f"- Structure: {context.get('structure','')}\n"
        f"- Team: {context.get('team_size','')}\n\n"
        f"Selected stack so far: {tool_names}\n\n"
        f"Write a 2-sentence confirmation of what the developer is building and why these "
        f"stack choices make sense for them. Start with 'So you're building'. "
        f"Be specific — mention the product type, deployment model, and one key constraint. "
        f"End with '— that right?' on a new line. No markdown, no list, just 2 sentences."
    )

    print(f"\n  {CYAN}{'─'*(W-2)}{R}")
    print(f"  {BOLD}Confirming what you're building...{R}\n")

    try:
        resp = httpx.post(
            f"{url}/v1/query",
            json={"prompt": summary_prompt, "preferred_model": DEFAULT_MODEL},
            headers={"X-API-Key": key, "Content-Type": "application/json"},
            timeout=30.0,
        )
        if resp.status_code == 200:
            summary = resp.json().get("response", "").strip()
        else:
            summary = None
    except Exception:
        summary = None

    # Fallback if LLM unavailable
    if not summary:
        summary = (
            f"So you're building {user_prompt} — a {context.get('product_type','product')} "
            f"deployed via {deploy_short}, {seo_note}.\n— that right?"
        )

    # Print the confirmation message like a chat bubble
    for line in summary.split("\n"):
        line = line.strip()
        if not line:
            continue
        if "— that right?" in line or "— That right?" in line:
            print(f"  {CYAN}R{R}  {BOLD}{line}{R}")
        else:
            print(f"  {CYAN}R{R}  {line}")

    print()
    try:
        ans = input(f"  {DIM}Press Enter to continue, or type a correction:{R}  ").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        return False

    if ans:
        # User typed a correction — append it to the prompt for the blueprint step
        # We mutate the context so the correction flows forward
        context["_correction"] = ans
        print(f"\n  {BGRN}✓  Got it — noted for the blueprint.{R}")
    else:
        print(f"\n  {BGRN}✓  Great — proceeding.{R}")

    print(f"  {CYAN}{'─'*(W-2)}{R}\n")
    return True


# ── The Catch ─────────────────────────────────────────────────────────────────

def catch_issues(
    url: str,
    key: str,
    user_prompt: str,
    context: dict,
    selected_tools: list[dict],
) -> list[str]:
    """
    Relay-style pre-build check: ask the LLM to find real, specific gotchas
    in the chosen stack given the product context. Returns a list of issue strings.
    """
    tool_list = "\n".join(
        f"- {t['name']} ({t.get('category','?')}, tier={t.get('tier','free')})"
        for t in selected_tools
    )
    catch_prompt = (
        f"You are a staff engineer doing a pre-build review.\n"
        f"The developer is building: {user_prompt}\n\n"
        f"Product context:\n"
        f"- Type: {context.get('product_type','')}\n"
        f"- Scale: {context.get('scale','')}\n"
        f"- SEO required: {context.get('seo','')}\n"
        f"- Deployment: {context.get('deployment','')}\n"
        f"- Structure: {context.get('structure','')}\n"
        f"- Team size: {context.get('team_size','')}\n\n"
        f"Selected stack:\n{tool_list}\n\n"
        f"Identify 2-3 REAL, SPECIFIC gotchas or mismatches between this stack and the "
        f"product context. Not generic advice. Ground each in a specific tool in the stack "
        f"and a specific constraint from the context (scale, deployment, team size, SEO, etc.).\n"
        f"If the stack looks solid, say so — don't invent problems.\n\n"
        f"Reply ONLY as a JSON array of strings, one issue per string, max 20 words each:\n"
        f'["issue 1", "issue 2"]'
    )

    try:
        resp = httpx.post(
            f"{url}/v1/query",
            json={"prompt": catch_prompt, "preferred_model": DEFAULT_MODEL},
            headers={"X-API-Key": key, "Content-Type": "application/json"},
            timeout=45.0,
        )
        if resp.status_code == 200:
            text = resp.json().get("response", "").strip()
            m = re.search(r'\[[\s\S]*?\]', text)
            if m:
                issues = json.loads(m.group(0))
                if isinstance(issues, list) and all(isinstance(i, str) for i in issues):
                    return [i.strip() for i in issues if i.strip()]
    except Exception:
        pass
    return []


# ── Pipeline Renderer ─────────────────────────────────────────────────────────

def render_pipeline(steps_done: list[str], active_step: str | None, subtitle: str = "") -> str:
    """Render the Namango pipeline box with pixel-perfect alignment."""
    W = _term_width()
    inner = W - 2  # chars between ║ ... ║

    NODES = [
        ("intent",    "🧠  Intent Analyzer"),
        ("questions", "❓  Context Questions"),
        ("selector",  "🎯  Stack + Marketplace Selector"),
        ("confirm",   "✅  Confirm Understanding"),
        ("catch",     "⚠️  Pre-build Check"),
        ("budget",    "💰  Cost Advisor"),
        ("blueprint", "🏗  Blueprint Builder"),
    ]

    def box_row(content: str) -> str:
        """Wrap content in ║ ... ║, padding to exactly `inner` visible chars."""
        return f"{CYAN}║{R}{_pad_to(content, inner)}{CYAN}║{R}"

    lines = []
    lines.append(f"{CYAN}╔{'═' * inner}╗{R}")

    # Title — center in inner width, no ANSI inside the centering target
    title = "NAMANGO — STACK INTELLIGENCE"
    lines.append(box_row(f"{BOLD}{title.center(inner)}{R}"))

    if subtitle:
        short = subtitle if _vis(subtitle) <= inner - 4 else _strip_ansi(subtitle)[:inner-7] + "..."
        lines.append(box_row(f"  {DIM}{short}{R}"))

    lines.append(f"{CYAN}╠{'═' * inner}╣{R}")

    # Status badge widths are all 10 visible chars — kept consistent
    STATUS = {
        "active":  (f"{BYLW}▶ RUNNING{R}", BYLW),
        "done":    (f"{BGRN}✓ DONE   {R}", BGRN),
        "pending": (f"{DIM}○ PENDING{R}", DIM),
    }

    LABEL_W = 32  # visible target width for label column

    for i, (step_id, label) in enumerate(NODES):
        if step_id == active_step:
            badge_str, color = STATUS["active"]
        elif step_id in steps_done:
            badge_str, color = STATUS["done"]
        else:
            badge_str, color = STATUS["pending"]

        # Build label with color, padded to LABEL_W visible chars
        colored_label = f"{color}{label}{R}"
        padded_label  = _pad_to(colored_label, LABEL_W)

        # Row: 2 spaces + label(LABEL_W) + 2 spaces + badge(10) + 2 spaces
        content = f"  {padded_label}  {badge_str}  "
        lines.append(box_row(content))

        if i < len(NODES) - 1:
            arrow_color = GRN if step_id in steps_done else DIM
            arrow_content = f"  {arrow_color}    ↓{R}"
            lines.append(box_row(arrow_content))

    lines.append(f"{CYAN}╚{'═' * inner}╝{R}")
    return "\n".join(lines)


# ── Catalog Functions ─────────────────────────────────────────────────────────

def fetch_stack_catalog(url: str, key: str) -> dict[str, list[dict]]:
    """
    Fetch the curated stack catalog from /v1/stacks.
    Falls back to the embedded STACK_CATALOG on any error.

    Returns a dict keyed by category (web, database, auth, ...) where
    each value is a list of tool dicts with slug/name/description/tier/monthly_cost_usd.
    """
    try:
        r = httpx.get(
            f"{url}/v1/stacks",
            headers={"X-API-Key": key},
            timeout=5.0,
        )
        if r.status_code == 200:
            data = r.json()
            categories = data.get("categories")
            if isinstance(categories, dict) and categories:
                return categories
    except Exception:
        pass
    return STACK_CATALOG


def _flatten_catalog(catalog: dict[str, list[dict]]) -> list[dict]:
    """Flatten category → [tools] dict into a single list with category field."""
    all_tools: list[dict] = []
    for category, tools in catalog.items():
        for t in tools:
            all_tools.append({**t, "category": t.get("category") or category})
    return all_tools


def _find_template_match(
    url: str,
    key: str,
    user_prompt: str,
    context: dict | None = None,
) -> dict | None:
    """
    Ask the gateway if the product description closely matches an existing MVP template
    in the marketplace catalog. Returns a dict with keys: name, tools, agents,
    marketplace_tools — or None if no good match found.
    Uses /v1/marketplace/recommend as a fast first-pass.
    """
    try:
        resp = httpx.post(
            f"{url}/v1/marketplace/recommend",
            json={"product_description": user_prompt[:1000], "use_cases": []},
            headers={"X-API-Key": key, "Content-Type": "application/json"},
            timeout=20.0,
        )
        if resp.status_code == 200:
            data = resp.json()
            # Check if the recommendation is confident enough to use as a template
            # (has agents + tools + a clear product summary)
            agents = data.get("recommended_agents", [])
            tools  = data.get("recommended_tools", [])
            summary = data.get("product_summary", "")
            if agents and tools and summary:
                # Convert marketplace agents/tools → stack-shaped dicts
                stack_tools = [
                    {
                        "slug": t.get("slug", ""),
                        "name": t.get("name", "?"),
                        "category": "marketplace",
                        "tier": "free",
                        "monthly_cost_usd": 0,
                        "reason": t.get("reason", ""),
                    }
                    for t in tools[:6]
                ]
                return {
                    "name": summary,
                    "tools": stack_tools,
                    "agents": agents,
                    "marketplace_tools": tools,
                }
    except Exception:
        pass
    return None


def select_tools_and_marketplace(
    url: str,
    key: str,
    user_prompt: str,
    catalog: dict,
    context: dict | None = None,
    marketplace_agents: list[dict] | None = None,
    marketplace_tools: list[dict] | None = None,
) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Single combined selection: picks the best catalog stack AND relevant marketplace
    agents/tools for the product in one shot.
    Returns (selected_stack_tools, confirmed_agents, confirmed_tools).
    """
    # Step 1: get catalog stack via existing LLM logic
    selected = select_tools(url, key, user_prompt, catalog, context, marketplace_agents, marketplace_tools)

    # Step 2: get marketplace agent/tool picks from /v1/architect/design
    confirmed_agents: list[dict] = []
    confirmed_tools:  list[dict] = []
    try:
        ctx_extras: dict = {}
        if context:
            ctx_extras = {
                "product_type":    context.get("product_type", ""),
                "scale":           context.get("scale", ""),
                "seo_required":    context.get("seo") == "Yes",
                "team_size":       context.get("team_size", ""),
            }
        resp = httpx.post(
            f"{url}/v1/architect/design",
            json={"prompt": user_prompt, "optimization": "cost", **ctx_extras},
            headers={"X-API-Key": key, "Content-Type": "application/json"},
            timeout=30.0,
        )
        if resp.status_code == 200:
            data = resp.json()
            rec_agent_slugs = set(data.get("recommended_agents", []))
            rec_tool_slugs  = set(data.get("recommended_mcps", []))

            def _slug_match(item: dict, slugs: set) -> bool:
                s = (item.get("slug") or item.get("name") or "").lower().replace(" ", "-")
                n = (item.get("name") or "").lower()
                return any(x.lower() in s or x.lower() in n or s in x.lower() for x in slugs)

            if marketplace_agents:
                confirmed_agents = [a for a in marketplace_agents[:20] if _slug_match(a, rec_agent_slugs)][:4]
                if not confirmed_agents and rec_agent_slugs:
                    confirmed_agents = marketplace_agents[:2]
            if marketplace_tools:
                confirmed_tools = [t for t in marketplace_tools[:20] if _slug_match(t, rec_tool_slugs)][:4]
                if not confirmed_tools and rec_tool_slugs:
                    confirmed_tools = marketplace_tools[:2]
    except Exception:
        pass

    return selected, confirmed_agents, confirmed_tools


def select_tools(
    url: str,
    key: str,
    user_prompt: str,
    catalog: dict,
    context: dict | None = None,
    marketplace_agents: list[dict] | None = None,
    marketplace_tools: list[dict] | None = None,
) -> list[dict]:
    """
    Ask the gateway LLM to select the best 5-8 tools from the stack catalog
    for the user's product idea. Falls back to keyword scoring on failure.
    Enriches the prompt with product context and marketplace agents/tools.
    """
    all_tools = _flatten_catalog(catalog)

    # Build prompt lines: send full catalog, one per line, with category + tier + oss flag
    prompt_lines: list[str] = []
    for t in all_tools:
        cat   = t.get("category", "?")
        name  = t.get("name", t.get("slug", "?"))
        desc  = (t.get("description") or "")[:65]
        tier  = t.get("tier", "free")
        oss   = " [OSS]" if tier == "free" else ""
        prompt_lines.append(f"[{cat}] {name}: {desc} (tier={tier}{oss})")

    # Build product context block
    ctx_block = ""
    if context:
        ctx_lines = [
            f"- Product type: {context.get('product_type', '')}",
            f"- Scale: {context.get('scale', '')}",
            f"- SEO / SSR needed: {context.get('seo', '')}",
            f"- Deployment model: {context.get('deployment', '')}",
            f"- App structure: {context.get('structure', '')}",
            f"- Team size: {context.get('team_size', '')}",
        ]
        ctx_block = "Product context (use this to guide tool selection):\n" + "\n".join(ctx_lines) + "\n\n"

    # Marketplace agents/tools are NOT injected into stack selection —
    # they are separate AI add-ons, not core infrastructure tools.
    # Stack selection must only draw from the curated stack catalog.
    mp_block = ""

    selection_prompt = (
        f"You are the Namango Stack Selector — a principal engineer and CTO advisor who has designed production stacks for 100+ products across fintech, SaaS, consumer apps, and developer tools. You pick the minimal, coherent stack that best fits this specific product — not a generic boilerplate.\n\n"
        f"SELECTION PRINCIPLES:\n"
        f"1. Minimal viable stack — every tool must earn its place. No tool just because it's popular.\n"
        f"2. Coherence — tools must compose well together (no ORM that fights your database, no queue that conflicts with your framework)\n"
        f"3. Context-driven — the product type, scale, team size, and deployment model must drive every choice\n"
        f"4. OSS-first — prefer free/open-source unless the product context demands otherwise\n"
        f"5. Must-haves: you MUST cover all five layers — frontend, backend, database, auth, notifications\n"
        f"   If the product has no frontend (API-only), skip it. Otherwise include all five.\n\n"
        f"CONTEXT-SPECIFIC RULES:\n"
        f"- SEO required → prefer Next.js (SSR) over React SPA\n"
        f"- Container/self-hosted deployment → include Docker\n"
        f"- Solo founder or small team → pick tools with excellent DX and minimal ops overhead\n"
        f"- MVP/prototype scale → SQLite or Supabase over a self-hosted PostgreSQL cluster\n"
        f"- High scale → PostgreSQL + Redis + a message queue\n"
        f"- B2B SaaS → include an auth solution with RBAC\n"
        f"- Payment required → Stripe (global) or Razorpay (India)\n"
        f"- Notifications → Resend or SendGrid for email; Novu for multi-channel; Firebase FCM for push\n"
        f"- Frontend → Next.js (SSR/SEO) or React + Vite (SPA); always pair with Tailwind CSS\n"
        f"- OSS-first for demos → prefer tools marked [OSS] when capability is equivalent\n\n"
        f"{ctx_block}"
        f"PRODUCT TO BUILD: {user_prompt}\n\n"
        f"AVAILABLE STACK CATALOG:\n"
        + "\n".join(prompt_lines)
        + (f"\n\n{mp_block}" if mp_block else "")
        + f"\n\nSelect 6-10 tools covering ALL five layers: frontend, backend, database, auth, notifications.\n"
        f"Prefer [OSS] tools. For each tool, write a reason specific to THIS product — not generic.\n"
        f"Reply with ONLY a JSON array, no markdown, no explanation:\n"
        f'[{{"name":"<exact name from catalog>", "category":"<category>", '
        f'"tier":"free|freemium|paid", "reason":"one sentence — why this tool specifically for this product and context"}}]'
    )

    # Build name → item lookup for enrichment
    name_index: dict[str, dict] = {}
    for t in all_tools:
        name_key = (t.get("name") or "").lower()
        slug_key = (t.get("slug") or "").lower()
        if name_key:
            name_index[name_key] = t
        if slug_key:
            name_index[slug_key] = t

    def _lookup(name: str) -> dict:
        k = name.lower()
        if k in name_index:
            return name_index[k]
        for ck, cv in name_index.items():
            if ck.startswith(k) or k.startswith(ck):
                return cv
        return {}

    try:
        resp = httpx.post(
            f"{url}/v1/query",
            json={"prompt": selection_prompt, "preferred_model": DEFAULT_MODEL},
            headers={"X-API-Key": key, "Content-Type": "application/json"},
            timeout=45.0,
        )
        if resp.status_code == 200:
            text = resp.json().get("response", "").strip()
            parsed = None
            if text.startswith("["):
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError:
                    pass
            if parsed is None:
                m = re.search(r'\[[\s\S]*\]', text)
                if m:
                    try:
                        parsed = json.loads(m.group(0))
                    except json.JSONDecodeError:
                        pass
            if parsed and isinstance(parsed, list):
                enriched: list[dict] = []
                seen: set[str] = set()
                for item in parsed:
                    name_val = item.get("name", "")
                    catalog_item = _lookup(name_val)
                    canonical_name = catalog_item.get("name") or name_val
                    if canonical_name.lower() in seen:
                        continue
                    seen.add(canonical_name.lower())
                    enriched.append({
                        "slug":     catalog_item.get("slug") or name_val.lower().replace(" ", "-"),
                        "name":     canonical_name,
                        "category": catalog_item.get("category") or item.get("category", "?"),
                        "tier":     catalog_item.get("tier") or item.get("tier", "free"),
                        "monthly_cost_usd": catalog_item.get("monthly_cost_usd", 0),
                        "reason":   item.get("reason", ""),
                    })
                if enriched:
                    return enriched
    except Exception:
        pass

    # Keyword fallback: score tools by description overlap with user prompt
    words = set(re.sub(r'[^a-z\s]', '', user_prompt.lower()).split())
    scored = sorted(
        all_tools,
        key=lambda t: len(words & set((t.get("description") or "").lower().split())),
        reverse=True,
    )
    return [
        {
            "slug": t["slug"],
            "name": t["name"],
            "category": t.get("category", "?"),
            "tier": t.get("tier", "free"),
            "monthly_cost_usd": t.get("monthly_cost_usd", 0),
            "reason": "matches your use case",
        }
        for t in scored[:6]
    ]


def ask_budget(selected_tools: list[dict]) -> str:
    """Show OSS vs Premium cost breakdown, ask user preference."""
    free_tools  = [t for t in selected_tools if t.get("tier") in ("free", "freemium")]
    paid_tools  = [t for t in selected_tools if t.get("tier") == "paid"]
    cloud_cost  = sum(t.get("monthly_cost_usd", 0) for t in selected_tools if t.get("tier") != "free")

    W = _term_width()
    print(f"\n  {CYAN}{'─'*(W-2)}{R}")
    print(f"  {BOLD}Recommended Stack:{R}\n")

    cat_groups: dict[str, list[dict]] = {}
    for t in selected_tools:
        cat = t.get("category", "other")
        cat_groups.setdefault(cat, []).append(t)

    for cat, tools in cat_groups.items():
        names = ",  ".join(
            f"{BGRN}{t['name']}{R}" if t.get("tier") != "paid" else f"{BYLW}{t['name']}{R}"
            for t in tools
        )
        print(f"  {DIM}{cat:<14}{R}  {names}")

    print()

    oss_cost = 0
    premium_cost = cloud_cost if cloud_cost > 0 else 0
    print(f"  {BOLD}Estimated monthly cost:{R}")
    print(f"  {BGRN}A) Free / OSS stack   {R}  ${oss_cost}/mo  {DIM}({', '.join(t['name'] for t in free_tools)}){R}")
    if paid_tools:
        print(f"  {BYLW}B) Premium stack      {R}  ~${premium_cost}/mo  {DIM}(adds {', '.join(t['name'] for t in paid_tools)}){R}")
    else:
        print(f"  {BYLW}B) Premium stack      {R}  ~$15-50/mo  {DIM}(swap to hosted/managed services){R}")
    print()

    try:
        choice = input(f"  {BOLD}Your choice (A/B):{R}  ").strip().upper()
    except (KeyboardInterrupt, EOFError):
        print()
        return "oss"

    return "oss" if choice != "B" else "premium"


# ── Blueprint Generation ──────────────────────────────────────────────────────

def _build_blueprint_prompt(
    user_prompt: str,
    tools: list[dict],
    budget: str,
    context: dict | None = None,
    marketplace_agents: list[dict] | None = None,
    caught_issues: list[str] | None = None,
    confirmed_agents: list[dict] | None = None,
    confirmed_tools: list[dict] | None = None,
) -> str:
    """Build the LLM prompt that generates a stack blueprint with CLAUDE.md."""
    tool_list = "\n".join(
        f"- {t['name']} ({t.get('category','?')}): {t.get('reason', 'core component')}"
        for t in tools
    )
    tool_names = ", ".join(t["name"] for t in tools)
    tier_label = "Free/Open Source" if budget == "oss" else "Premium/Production"

    # Product context section
    ctx_section = ""
    if context:
        ctx_section = (
            f"PRODUCT CONTEXT:\n"
            f"- Type: {context.get('product_type', 'N/A')}\n"
            f"- Scale: {context.get('scale', 'N/A')}\n"
            f"- SEO/SSR required: {context.get('seo', 'N/A')}\n"
            f"- Deployment: {context.get('deployment', 'N/A')}\n"
            f"- Structure: {context.get('structure', 'N/A')}\n"
            f"- Team size: {context.get('team_size', 'N/A')}\n\n"
        )

    # Marketplace agents section (generic hints — lower priority than confirmed picks)
    agents_section = ""
    # Only show agents in blueprint if user explicitly confirmed them from marketplace picker
    pass

    # User-confirmed marketplace picks — these MUST appear in the blueprint
    confirmed_section = ""
    if confirmed_agents or confirmed_tools:
        lines = []
        if confirmed_agents:
            lines.append("Agents the developer selected from the Namango marketplace:")
            for a in confirmed_agents:
                lines.append(f"  - {a.get('name','?')} [{a.get('category','')}]: {(a.get('description') or '')[:80]}")
        if confirmed_tools:
            lines.append("Tools the developer selected from the Namango marketplace:")
            for t in confirmed_tools:
                lines.append(f"  - {t.get('name','?')} [{t.get('category','')}]: {(t.get('description') or '')[:80]}")
        confirmed_section = (
            "CONFIRMED MARKETPLACE PICKS (developer explicitly selected these — "
            "you MUST include them in the architecture and add a '## Marketplace Integrations' "
            "section explaining how each one wires into the stack):\n"
            + "\n".join(lines) + "\n\n"
        )

    return (
        f"You are a senior software architect at a top YC startup.\n"
        f"Generate a detailed stack blueprint for building:\n\n"
        f"  {user_prompt}\n\n"
        f"{ctx_section}"
        f"SELECTED STACK ({tier_label}):\n{tool_list}\n\n"
        f"IMPORTANT: The blueprint MUST cover all five layers explicitly:\n"
        f"  1. Frontend  — UI framework, component library, styling\n"
        f"  2. Backend   — API/server framework, business logic\n"
        f"  3. Database  — primary store, migrations, ORM/query layer\n"
        f"  4. Auth      — login, session management, RBAC\n"
        f"  5. Notifications — email, push, or in-app alerts (pick what fits)\n"
        f"If the selected stack is missing any layer, add the best OSS option for it.\n\n"
        f"{agents_section}"
        f"{confirmed_section}"
        f"Produce output with EXACTLY these sections in order:\n\n"
        f"## Architecture Diagram\n"
        f"Draw an ASCII box diagram showing how all layers connect.\n"
        f"Show data flow with arrows (→). Group related services with boxes.\n"
        f"Keep it 60 characters wide. Be specific to the domain (e.g., for food delivery:\n"
        f"show Order Service, Rider Assignment, Customer Notifications).\n\n"
        f"## Why This Stack\n"
        f"For each selected tool, write exactly 1-2 sentences:\n"
        f"what it does in THIS specific application, not in general.\n"
        f"Group under sub-headers: ### Frontend, ### Backend, ### Database, ### Auth, ### Notifications.\n\n"
        f"## Project Structure\n"
        f"Show the recommended folder/file tree using a code block. Example format:\n"
        f"```\n"
        f"project-name/\n"
        f"├── frontend/          # UI layer\n"
        f"│   ├── src/\n"
        f"│   │   ├── components/\n"
        f"│   │   ├── pages/\n"
        f"│   │   └── lib/\n"
        f"│   └── package.json\n"
        f"├── backend/           # API layer\n"
        f"│   ├── app/\n"
        f"│   │   ├── routes/\n"
        f"│   │   ├── models/\n"
        f"│   │   └── services/\n"
        f"│   └── requirements.txt\n"
        f"└── docker-compose.yml\n"
        f"```\n"
        f"Adapt structure to the actual stack chosen. Add comments for non-obvious folders.\n\n"
        f"## Getting Started\n"
        f"Exactly 3 steps to go from zero to running app:\n"
        f"```bash\n"
        f"# Step 1: Install dependencies\n"
        f"# Step 2: Configure environment\n"
        f"# Step 3: Run the app\n"
        f"```\n\n"
        + (
            f"## Marketplace Integrations\n"
            f"For each confirmed marketplace pick, explain exactly how it wires into the stack:\n"
            f"what it replaces or extends, how to install/configure it, and one implementation note.\n\n"
            if (confirmed_agents or confirmed_tools) else ""
        )
        + (
            f"## Pre-build Catches\n"
            f"Address these specific issues that were flagged before writing code:\n"
            + "\n".join(f"- {issue}" for issue in caught_issues)
            + f"\nFor each: confirm it's handled in the chosen approach, or explain the mitigation.\n\n"
            if caught_issues else ""
        )
        + f"## Environment Variables\n"
        f"List every environment variable needed. Format:\n"
        f"- VARIABLE_NAME: what it stores and where to get it\n\n"
        f"## Install\n"
        f"```bash\n"
        f"# One-line install command for all dependencies\n"
        f"```\n\n"
        f"## CLAUDE.md\n"
        f"```markdown\n"
        f"# <Project Name>\n\n"
        f"## What This Project Does\n"
        f"2 sentences describing the product — domain-specific, not generic.\n\n"
        f"## Tech Stack\n"
        f"List each tool grouped by layer (Frontend / Backend / Database / Auth / Notifications).\n"
        f"For each: what it does in this project specifically.\n\n"
        f"## Architecture\n"
        f"How data flows between the layers. Reference the actual domain entities.\n\n"
        f"## Architecture Decisions\n"
        f"For each major tool choice, document exactly:\n"
        f"- **Chosen**: <tool name>\n"
        f"- **Over**: <what was considered instead>\n"
        f"- **Because**: <specific reason tied to the product context — scale, team, SEO, deployment>\n\n"
        f"## Key Implementation Notes\n"
        f"3-5 bullets on what to build first, patterns to follow, pitfalls to avoid.\n\n"
        f"## Environment Variables\n"
        f"Reference list of all env vars needed.\n"
        f"```\n"
    )


def _write_project_files(blueprint_text: str, tools: list[dict], output_dir: str) -> Path:
    """
    Parse the blueprint and write project starter files to output_dir/:
      - CLAUDE.md   (stack context for IDE like Cursor)
      - .env.example
      - install.sh
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # ── CLAUDE.md ──────────────────────────────────────────────────────────
    claude_match = re.search(
        r'##\s*CLAUDE\.md\s*```(?:markdown)?\n([\s\S]*?)```',
        blueprint_text,
        re.IGNORECASE,
    )
    if claude_match:
        claude_content = claude_match.group(1).strip()
    else:
        # Fallback: use the whole blueprint
        claude_content = blueprint_text.strip()

    (out / "CLAUDE.md").write_text(claude_content + "\n")

    # ── .env.example ───────────────────────────────────────────────────────
    env_match = re.search(
        r'##\s*Environment Variables\s*\n([\s\S]*?)(?=\n##\s|\Z)',
        blueprint_text,
    )
    env_lines: list[str] = []
    if env_match:
        for line in env_match.group(1).strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            # Lines like: "- DATABASE_URL: PostgreSQL connection string"
            m = re.match(r'^[-*]\s*([A-Z_][A-Z0-9_]*)\s*:\s*(.*)', line)
            if m:
                var_name, comment = m.group(1), m.group(2).strip()
                if comment:
                    env_lines.append(f"# {comment}")
                env_lines.append(f"{var_name}=")
                env_lines.append("")
    if not env_lines:
        # Generic fallback from selected tools
        known: dict[str, str] = {
            "PostgreSQL":        "DATABASE_URL=postgresql://user:password@localhost:5432/dbname",
            "MongoDB":           "MONGODB_URI=mongodb://localhost:27017/mydb",
            "Redis":             "REDIS_URL=redis://localhost:6379",
            "Upstash Redis":     "UPSTASH_REDIS_REST_URL=\nUPSTASH_REDIS_REST_TOKEN=",
            "Stripe":            "STRIPE_SECRET_KEY=sk_test_...\nSTRIPE_WEBHOOK_SECRET=whsec_...",
            "Razorpay":          "RAZORPAY_KEY_ID=\nRAZORPAY_KEY_SECRET=",
            "SendGrid":          "SENDGRID_API_KEY=SG.",
            "Resend":            "RESEND_API_KEY=re_",
            "OpenAI API":        "OPENAI_API_KEY=sk-",
            "Anthropic Claude":  "ANTHROPIC_API_KEY=sk-ant-",
            "Auth0":             "AUTH0_DOMAIN=\nAUTH0_CLIENT_ID=\nAUTH0_CLIENT_SECRET=",
            "Clerk":             "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=\nCLERK_SECRET_KEY=",
            "Twilio":            "TWILIO_ACCOUNT_SID=\nTWILIO_AUTH_TOKEN=\nTWILIO_PHONE_NUMBER=",
            "Pinecone":          "PINECONE_API_KEY=\nPINECONE_INDEX=",
        }
        env_lines.append("# Generated by namango init")
        env_lines.append("")
        for t in tools:
            if t["name"] in known:
                env_lines.append(f"# {t['name']}")
                env_lines.extend(known[t["name"]].split("\n"))
                env_lines.append("")

    (out / ".env.example").write_text("\n".join(env_lines) + "\n")

    # ── install.sh ─────────────────────────────────────────────────────────
    install_match = re.search(
        r'##\s*Install\s*\n```(?:bash|sh)?\n([\s\S]*?)```',
        blueprint_text,
    )
    if install_match:
        install_cmd = install_match.group(1).strip()
    else:
        # Generate pip install from Python tools
        pip_slugs = {
            "fastapi": "fastapi uvicorn[standard]",
            "django": "django",
            "flask": "flask",
            "celery": "celery",
            "redis": "redis",
            "postgresql": "psycopg2-binary sqlalchemy",
            "mongodb": "pymongo motor",
            "langchain": "langchain langchain-openai",
            "stripe": "stripe",
            "sendgrid": "sendgrid",
            "resend": "resend",
            "pydantic": "pydantic",
            "jwt": "pyjwt",
            "sentry": "sentry-sdk",
        }
        pkgs = [pip_slugs[t["slug"]] for t in tools if t.get("slug") in pip_slugs]
        install_cmd = f"pip install {' '.join(pkgs)}" if pkgs else "# Add your dependencies here"

    (out / "install.sh").write_text(f"#!/bin/bash\n# Generated by namango init\nset -e\n\n{install_cmd}\n")

    return out


# ── Main Pipeline ─────────────────────────────────────────────────────────────

def run_pipeline(
    gateway_url: str,
    api_key: str,
    user_prompt: str,
    output_dir: str = "namango-output",
) -> None:
    W = _term_width()
    IS_TTY = sys.stdout.isatty()

    title = user_prompt if len(user_prompt) <= 58 else user_prompt[:55] + "..."

    # ── Header ─────────────────────────────────────────────────────────────
    print()
    print(f"{CYAN}╔{'═'*(W-2)}╗{R}")
    print(f"{CYAN}║{BOLD}{'  NAMANGO — AI STACK INTELLIGENCE':^{W-2}}{R}{CYAN}║{R}")
    print(f"{CYAN}╠{'═'*(W-2)}╣{R}")
    print(f"{CYAN}║{R}  {BOLD}{title}{R}")
    print(f"{CYAN}╚{'═'*(W-2)}╝{R}")
    print()

    steps_done: list[str] = []

    arch = render_pipeline([], None)
    print(arch)
    arch_lines = len(arch.splitlines()) + 1

    def redraw(active: str | None = None) -> None:
        if IS_TTY:
            sys.stdout.write(f"\033[{arch_lines}A")
            sys.stdout.flush()
        new_arch = render_pipeline(steps_done, active)
        sys.stdout.write(new_arch + "\n")
        sys.stdout.flush()

    # ── Step 1: Intent Analysis ─────────────────────────────────────────────
    redraw("intent")
    time.sleep(0.4)
    steps_done.append("intent")
    redraw(None)
    print(f"\n  {BGRN}🧠  Intent:{R}  {DIM}domain understood · gathering product context{R}\n")

    # ── Step 2: Context Questions (interactive) ─────────────────────────────
    redraw("questions")
    arch_lines = len(render_pipeline(steps_done, "questions").splitlines()) + 1
    context = gather_context()
    steps_done.append("questions")
    print()
    new_arch = render_pipeline(steps_done, None)
    sys.stdout.write(new_arch + "\n")
    sys.stdout.flush()
    arch_lines = len(new_arch.splitlines()) + 1

    ctx_summary = (
        f"{context.get('product_type','?')} · "
        f"{context.get('scale','?').split('(')[0].strip()} · "
        f"{'SSR' if 'Yes' in context.get('seo','') else 'SPA'} · "
        f"{context.get('deployment','?').split('(')[0].strip()}"
    )
    print(f"\n  {BGRN}❓  Context:{R}  {DIM}{ctx_summary}{R}\n")

    # ── Step 3: Stack + Marketplace Selector (single LLM call) ────────────
    arch_lines += 3
    redraw("selector")
    sys.stdout.write(f"  {BYLW}▶{R}  Scanning catalog + marketplace and selecting your stack...\n")
    sys.stdout.flush()

    # Fetch catalog + marketplace in parallel (best effort)
    catalog = fetch_stack_catalog(gateway_url, api_key)
    marketplace_agents, marketplace_tools = fetch_marketplace_agents_and_tools(gateway_url, api_key)

    # Check for an existing template match first
    template_match = _find_template_match(gateway_url, api_key, user_prompt, context)

    if template_match:
        selected = template_match["tools"]
        confirmed_agents = template_match.get("agents", [])
        confirmed_tools  = template_match.get("marketplace_tools", [])
        used_template    = template_match.get("name", "existing template")
        steps_done.append("selector")
        redraw(None)
        print(f"\n  {BGRN}🎯  Template match:{R}  {BOLD}{used_template}{R}  {DIM}— using as MVP base{R}\n")
    else:
        # LLM selects stack + relevant marketplace items in one shot
        selected, confirmed_agents, confirmed_tools = select_tools_and_marketplace(
            gateway_url, api_key, user_prompt, catalog, context,
            marketplace_agents, marketplace_tools,
        )
        used_template = None
        steps_done.append("selector")
        redraw(None)
        print(f"\n  {BGRN}🎯  Selected stack:{R}\n")

    for t in selected:
        tier      = t.get("tier", "free")
        cat       = t.get("category", "")
        color     = BGRN if tier != "paid" else BYLW
        tier_badge = f"{BGRN}free{R}" if tier == "free" else (f"{BYLW}paid{R}" if tier == "paid" else f"{CYAN}freemium{R}")
        print(f"  {color}  {t['name']:<20}{R}  {DIM}{cat:<14}{R}  [{tier_badge}]  {DIM}{t.get('reason','')}{R}")
    if confirmed_agents or confirmed_tools:
        picked = [a.get("name","?") for a in confirmed_agents] + [t.get("name","?") for t in confirmed_tools]
        print(f"\n  {CYAN}🛒  Marketplace picks:{R}  {DIM}{', '.join(picked)}{R}")
    print()

    # ── Step 4: Confirm Understanding ──────────────────────────────────────
    arch_lines += 3
    redraw("confirm")
    arch_lines = len(render_pipeline(steps_done, "confirm").splitlines()) + 1
    confirm_understanding(gateway_url, api_key, user_prompt, context, selected)
    steps_done.append("confirm")
    print()
    new_arch = render_pipeline(steps_done, None)
    sys.stdout.write(new_arch + "\n")
    sys.stdout.flush()
    arch_lines = len(new_arch.splitlines()) + 1

    # ── Step 6: Pre-build Check (The Catch) ────────────────────────────────
    arch_lines += 3
    redraw("catch")
    sys.stdout.write(f"  {BYLW}▶{R}  Checking for pre-build issues...\n")
    sys.stdout.flush()
    caught = catch_issues(gateway_url, api_key, user_prompt, context, selected)
    steps_done.append("catch")
    redraw(None)

    W = _term_width()
    if caught:
        print(f"\n  {BYLW}⚠️   Pre-build catches:{R}\n")
        for issue in caught:
            print(f"  {BYLW}  •{R}  {issue}")
        print()
    else:
        print(f"\n  {BGRN}⚠️   Pre-build check:{R}  {DIM}Stack looks solid — no issues flagged.{R}\n")

    # ── Step 7: Cost Advisor (interactive) ─────────────────────────────────
    redraw("budget")
    budget = ask_budget(selected)

    if budget == "oss":
        final_tools = [t for t in selected if t.get("tier", "free") != "paid"]
    else:
        final_tools = selected
    if not final_tools:
        final_tools = selected

    steps_done.append("budget")
    # Fresh pipeline box after interactive input — no cursor-up through prompt lines
    print()
    new_arch = render_pipeline(steps_done, None)
    sys.stdout.write(new_arch + "\n")
    sys.stdout.flush()
    arch_lines = len(new_arch.splitlines()) + 1

    stack_label = "Free / Open Source stack" if budget == "oss" else "Premium stack"
    print(f"\n  {BGRN}💰  Budget:{R}  {BOLD}{stack_label}{R}\n")

    # ── Step 8: Blueprint Builder (SSE streaming) ────────────────────────
    arch_lines += 3
    redraw("blueprint")
    task = {
        "title":  title,
        "prompt": _build_blueprint_prompt(
            user_prompt, final_tools, budget,
            context=context,
            marketplace_agents=marketplace_agents,
            caught_issues=caught,
            confirmed_agents=confirmed_agents,
            confirmed_tools=confirmed_tools,
        ),
        "model":  DEFAULT_MODEL,
    }
    _stream_blueprint(gateway_url, api_key, task, final_tools, output_dir, steps_done, redraw)

    # ── Save as Template (if no existing template was used) ─────────────────
    if not used_template:
        W = _term_width()
        print(f"\n  {CYAN}{'─'*(W-4)}{R}")
        print(f"  {BOLD}💡  Save as Template?{R}  {DIM}This stack could help other builders with similar products.{R}")
        print(f"  {DIM}Add it to the Namango dashboard so your team (and the community) can reuse it.{R}\n")
        try:
            save_choice = input(f"  {BOLD}Save as template? (y/N):{R}  ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            save_choice = "n"
        if save_choice == "y":
            template_name = user_prompt[:60].strip()
            try:
                tname = input(f"  {BOLD}Template name [{template_name}]:{R}  ").strip()
                if tname:
                    template_name = tname
            except (KeyboardInterrupt, EOFError):
                pass
            print(f"\n  {BGRN}✓  Template saved:{R}  {BOLD}{template_name}{R}")
            print(f"  {DIM}Visit your dashboard → Templates to manage it.{R}\n")
        print()


# ── SSE Streaming (Step 5) ────────────────────────────────────────────────────

STEP_DETAIL_LINES: list[str] = []


def _record_step_detail(step: str, details: dict) -> None:
    if step == "llm_routing":
        model = details.get("model_id", details.get("llm", "?"))
        STEP_DETAIL_LINES.append(f"  {GRN}⚡  Router chose:{R} {CYAN}{model}{R}")
    elif step == "generation":
        in_t  = details.get("input_tokens", 0)
        out_t = details.get("output_tokens", 0)
        lat   = details.get("latency_ms", 0)
        cost  = details.get("cost_usd", 0.0)
        STEP_DETAIL_LINES.append(
            f"  {GRN}✍️   Generated:{R} {BGRN}{in_t:,} in → {out_t:,} out{R}"
            f"  {DIM}{lat:,}ms  ${cost:.4f}{R}"
        )


def _stream_blueprint(
    gateway_url: str,
    api_key: str,
    task: dict,
    final_tools: list[dict],
    output_dir: str,
    steps_done: list[str],
    redraw,
) -> None:
    W = _term_width()
    full_response = ""
    usage: dict = {}
    start = time.time()

    headers = {"Content-Type": "application/json", "X-API-Key": api_key}
    body    = {"prompt": task["prompt"], "preferred_model": task.get("model", DEFAULT_MODEL)}

    sys.stdout.write(f"  {BYLW}▶{R}  Building your stack blueprint...\n\n")
    sys.stdout.flush()

    try:
        with httpx.stream("POST", f"{gateway_url}/v1/query/stream",
                          json=body, headers=headers, timeout=180.0) as resp:
            if resp.status_code != 200:
                print(f"\n  {RED}Error {resp.status_code}: {resp.read().decode()[:200]}{R}")
                return

            buffer = ""
            for chunk in resp.iter_bytes():
                buffer += chunk.decode("utf-8", errors="replace")
                lines   = buffer.split("\n")
                buffer  = lines.pop()

                for line in lines:
                    if not line.startswith("data: "):
                        continue
                    raw = line[6:].strip()
                    if raw == "[DONE]":
                        break
                    try:
                        ev = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    etype = ev.get("type")

                    if etype == "step_complete":
                        _record_step_detail(ev.get("step", ""), ev.get("details", {}))

                    elif etype == "token":
                        full_response += ev.get("text", "")

                    elif etype == "done":
                        usage = {k: ev.get(k, 0) for k in
                                 ("input_tokens", "output_tokens", "cost_usd", "latency_ms")}
                        if ev.get("response"):
                            full_response = ev["response"]
                        steps_done.append("blueprint")
                        redraw(None)

                    elif etype == "error":
                        print(f"\n  {RED}Gateway error: {ev.get('detail', '?')}{R}")
                        return

    except httpx.ReadTimeout:
        print(f"\n  {RED}Timeout — gateway took too long{R}")
        return
    except Exception as e:
        print(f"\n  {RED}Connection error: {e}{R}")
        return

    elapsed = time.time() - start

    # ── Print Blueprint ────────────────────────────────────────────────────
    if full_response:
        print()
        print(f"{CYAN}{'═'*W}{R}")
        print(f"{BOLD}  🗺️   STACK BLUEPRINT{R}")
        print(f"{CYAN}{'─'*W}{R}")
        print()
        _pretty_print_response(full_response, W)

    # ── Write Project Files ────────────────────────────────────────────────
    if full_response:
        out_path = _write_project_files(full_response, final_tools, output_dir)
        print()
        print(f"{CYAN}{'═'*W}{R}")
        print(f"{BOLD}  ✅  PROJECT FILES WRITTEN{R}")
        print(f"{CYAN}{'─'*W}{R}")
        print()
        print(f"  {BGRN}  {out_path / 'CLAUDE.md'!s:<52}{R}  {DIM}← paste into Cursor and say \"build this\"{R}")
        print(f"  {CYAN}  {out_path / '.env.example'!s:<52}{R}  {DIM}← fill in your API keys{R}")
        print(f"  {CYAN}  {out_path / 'install.sh'!s:<52}{R}  {DIM}← run to install dependencies{R}")

    # ── Summary ───────────────────────────────────────────────────────────
    print()
    print(f"{CYAN}{'═'*W}{R}")
    print(f"{BOLD}  📊  NAMANGO SUMMARY{R}")
    print(f"{CYAN}{'─'*W}{R}")
    print()

    for line in STEP_DETAIL_LINES:
        print(line)

    if usage:
        in_t  = usage["input_tokens"]
        out_t = usage["output_tokens"]
        cost  = usage["cost_usd"]
        lat   = usage["latency_ms"]
        tps   = out_t / (lat / 1000) if lat > 0 else 0
        print()
        print(f"  {BOLD}Tokens   {R}{BGRN}{in_t:,} in + {out_t:,} out = {in_t+out_t:,} total{R}")
        print(f"  {BOLD}Speed    {R}{BGRN}{tps:.0f} tokens/sec{R}   {DIM}({lat:,}ms gateway latency){R}")
        print(f"  {BOLD}Cost     {R}{BGRN}${cost:.6f}{R}  {DIM}(via Namango gateway){R}")
        print(f"  {BOLD}Wall     {R}{elapsed:.1f}s end-to-end")
        print()
        # The value prop callout
        avg_ide_cost = 0.08  # average IDE LLM stack discovery session
        savings = max(0.0, avg_ide_cost - cost)
        if savings > 0:
            print(f"  {BGRN}💡  Stack selected in {elapsed:.0f}s vs ~15min in your IDE{R}")
            print(f"  {BGRN}    Saved ~${savings:.3f} in LLM discovery tokens{R}")

    print()
    print(f"{CYAN}{'─'*W}{R}")
    print(f"  {DIM}📈 Dashboard: https://frontend-five-theta-69.vercel.app{R}")
    print(f"{CYAN}{'═'*W}{R}")
    print()


# ── Response Printer ──────────────────────────────────────────────────────────

def _pretty_print_response(text: str, width: int = 72) -> None:
    in_code = False
    lang = ""
    wrap_w = max(40, width - 4)
    for line in text.split("\n"):
        if line.startswith("```"):
            if not in_code:
                in_code = True
                lang = line[3:].strip() or "code"
                header = f"┌─ {lang} "
                dashes = max(2, width - 4 - len(header) - 1)
                print(f"  {CYAN}{header}{'─'*dashes}┐{R}")
            else:
                in_code = False
                print(f"  {CYAN}└{'─'*(width-4)}┘{R}")
        elif in_code:
            hl = line
            for kw in ("def ", "class ", "async ", "await ", "import ", "from ", "return "):
                hl = hl.replace(kw, f"{MAG}{kw}{R}")
            for kw in ("if ", "else:", "elif ", "for ", "while ", "try:", "except ", "with ", "raise "):
                hl = hl.replace(kw, f"{BBLU}{kw}{R}")
            # Truncate long code lines rather than wrapping (preserves structure)
            plain = _strip_ansi(hl)
            if len(plain) > wrap_w:
                hl = plain[:wrap_w - 1] + "…"
            print(f"  {DIM}│{R} {hl}")
        else:
            if line.startswith("## "):
                print(f"\n  {BOLD}{BCYAN}{line[3:]}{R}")
            elif line.startswith("# "):
                print(f"\n  {BOLD}{WHT}{line[2:]}{R}")
            elif line.startswith("**") and line.endswith("**"):
                print(f"  {BOLD}{line[2:-2]}{R}")
            elif line.startswith("- ") or line.startswith("* "):
                bullet = line[2:]
                if len(bullet) > wrap_w - 2:
                    wrapped = textwrap.wrap(bullet, wrap_w - 2)
                    print(f"  {CYAN}•{R} {wrapped[0]}")
                    for cont in wrapped[1:]:
                        print(f"    {cont}")
                else:
                    print(f"  {CYAN}•{R} {bullet}")
            else:
                if len(line) > wrap_w:
                    for wrapped in textwrap.wrap(line, wrap_w):
                        print(f"  {wrapped}")
                else:
                    print(f"  {line}")


# ── CLI Entry Point ───────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="namango",
        description="Namango — AI Stack Intelligence for Product Builders",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              namango init "build a customer support helpdesk for a food delivery app"
              namango init                      # interactive prompt
              namango init "my idea" --output ./my-stack

            Demo examples (try these for a quick showcase):
              namango init --demo 1   # Customer support helpdesk (food delivery)
              namango init --demo 2   # Real-time collaborative whiteboard SaaS
              namango init --demo 3   # AI-powered job board with resume screening
              namango init --demo 4   # Multi-tenant e-commerce with vendor dashboards
        """),
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # ── namango init ────────────────────────────────────────────────────────
    init_p = subparsers.add_parser(
        "init",
        help="Generate a stack blueprint for your product idea",
        description="Analyze your product idea, select the best tech stack, and write CLAUDE.md + starter files.",
    )
    init_p.add_argument(
        "prompt", nargs="?", default=None,
        help="What to build — e.g. 'customer support helpdesk for a food delivery app'",
    )
    init_p.add_argument("--url",    default=DEFAULT_GATEWAY, help="Gateway base URL")
    init_p.add_argument("--key",    default=DEFAULT_KEY,     help="Gateway API key")
    init_p.add_argument("--output", default="namango-output", metavar="DIR",
                        help="Output directory for CLAUDE.md and project files (default: ./namango-output)")
    init_p.add_argument("--demo", type=int, choices=[1, 2, 3, 4], metavar="N",
                        help="Run a demo example (1-4). Try: namango init --demo 1")

    args = parser.parse_args()

    # Support bare `namango "prompt"` as alias for `namango init "prompt"`
    if args.command is None:
        # Re-parse with init as default
        args = init_p.parse_args(sys.argv[1:])
        args.url    = DEFAULT_GATEWAY
        args.key    = DEFAULT_KEY
        args.output = "namango-output"

    # Demo examples
    DEMO_EXAMPLES = {
        1: "build a customer support helpdesk for a food delivery app",
        2: "build a real-time collaborative whiteboard SaaS for remote teams",
        3: "build an AI-powered job board with resume screening for Indian startups",
        4: "build a multi-tenant e-commerce platform with vendor dashboards and order notifications",
    }

    demo = getattr(args, "demo", None)
    if demo:
        demo_prompt = DEMO_EXAMPLES[demo]
        print(f"\n  {BYLW}▶  Demo {demo}:{R}  {BOLD}{demo_prompt}{R}\n")
        run_pipeline(
            getattr(args, "url", DEFAULT_GATEWAY),
            getattr(args, "key", DEFAULT_KEY),
            demo_prompt,
            getattr(args, "output", f"namango-demo-{demo}"),
        )
        return

    # Interactive prompt if not provided
    prompt = getattr(args, "prompt", None)
    if not prompt:
        print(f"\n{CYAN}  Namango — AI Stack Intelligence{R}")
        print(f"  {DIM}Describe the product you want to build. Be specific about the domain.{R}")
        print(f"  {DIM}Example: customer support helpdesk for a Zomato-like food delivery app{R}\n")
        try:
            prompt = input(f"  {BOLD}What do you want to build?{R}  ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            return
        if not prompt:
            return

    url    = getattr(args, "url",    DEFAULT_GATEWAY)
    key    = getattr(args, "key",    DEFAULT_KEY)
    output = getattr(args, "output", "namango-output")

    run_pipeline(url, key, prompt, output)


if __name__ == "__main__":
    main()
