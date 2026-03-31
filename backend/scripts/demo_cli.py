#!/usr/bin/env python3
"""
Namango AI Gateway — Live Demo CLI
====================================
Sends a complex, multi-agent task to the gateway and streams the orchestration
in real time, showing routing decisions, agent selection, tool execution, and
the final response — all in a single CLI run.

Usage:
    python demo_cli.py                             # uses defaults below
    GATEWAY_URL=https://... API_KEY=gw-... python demo_cli.py
    python demo_cli.py --task planning             # pick a different demo task
    python demo_cli.py --url http://localhost:8000 --key gw-...

Tasks: planning (default), architecture, research, code, fullstack
"""
import os
import sys
import json
import time
import argparse
import httpx

# ── Config ──────────────────────────────────────────────────────────────────
DEFAULT_GATEWAY = "https://ai-gateway-backend-production.up.railway.app"
DEFAULT_KEY     = os.getenv("API_KEY", "gw-bn1RrcLqzARb5mPpBMiCzB0ZbxhpCVasQ_5hz9aWIrE")

# ── Demo Tasks ───────────────────────────────────────────────────────────────
TASKS = {
    "planning": {
        "title": "YC Startup: 90-Day Go-To-Market Plan",
        "prompt": (
            "You are a startup advisor. I'm building an AI API gateway (like Kong but for LLMs) "
            "and I just got accepted to Y Combinator W26. I need a comprehensive 90-day go-to-market plan.\n\n"
            "Please create:\n"
            "1. **Week 1-2 (Foundation):** Define ICP, pricing tiers, and launch messaging\n"
            "2. **Week 3-6 (Traction):** Developer outreach strategy, content calendar (10 post ideas), "
            "and how to get first 50 paying customers\n"
            "3. **Week 7-12 (Scale):** PLG motion, enterprise sales motion, and key metrics to hit\n"
            "4. **Technical integration guide:** A sample curl command and Python snippet showing how "
            "a developer integrates our gateway in under 5 minutes\n"
            "5. **Competitive positioning:** How we win against OpenRouter, LiteLLM, and Portkey\n\n"
            "Make this specific, actionable, and YC Demo Day-ready. Include metrics, timelines, and "
            "concrete next steps for each phase."
        ),
    },
    "architecture": {
        "title": "Multi-Tenant SaaS: Technical Architecture Design",
        "prompt": (
            "Design a production-grade multi-tenant SaaS architecture for an AI gateway product "
            "that must handle 100,000 API requests/day at launch, scaling to 10M/day in 18 months.\n\n"
            "Provide:\n"
            "1. **System architecture diagram** (ASCII art) with all components\n"
            "2. **Database schema** for: organizations, api_keys, request_logs, billing, rate_limits\n"
            "3. **LLM routing algorithm** — how to select the right model based on task category, "
            "cost budget, latency requirements, and fallback chain\n"
            "4. **Rate limiting design** — token bucket with Redis, per-org limits, burst handling\n"
            "5. **Observability stack** — what to instrument, which metrics matter (p50/p95/p99 latency, "
            "error rates, cost per org)\n"
            "6. **Cost optimization** — caching strategy, model routing to minimize cost while "
            "maintaining quality\n"
            "7. **Security model** — API key hashing, secret rotation, audit logging\n"
            "8. **Deployment** — Dockerfile, Railway config, environment variables checklist\n\n"
            "Include Python FastAPI code snippets for the 3 most critical components."
        ),
    },
    "research": {
        "title": "AI Model Landscape: 2025 Research Report",
        "prompt": (
            "Research and write a comprehensive technical report on the current AI model landscape "
            "for an enterprise developer audience (2025 edition).\n\n"
            "Cover:\n"
            "1. **Foundation Models Comparison:** GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro, "
            "Llama 3.1 70B, Mistral Large — benchmark scores, pricing, context windows, strengths\n"
            "2. **Routing Strategy:** When to use which model — a decision tree for: "
            "code generation, analysis, summarization, RAG, agentic tasks\n"
            "3. **Cost Analysis:** Real-world cost breakdown for 1M tokens across providers, "
            "with a Python script to calculate monthly AI spend\n"
            "4. **Emerging Trends:** Multi-modal, reasoning models (o1, R1), fine-tuning vs RAG, "
            "agentic frameworks (LangGraph, AutoGen, CrewAI)\n"
            "5. **Production Checklist:** 20 things to get right before going to production with LLMs\n"
            "6. **Python Integration Examples:** SDK snippets for the top 3 providers\n\n"
            "Format as a structured report with headers, tables, and code blocks. "
            "Target: senior engineers evaluating LLM infrastructure."
        ),
    },
    "code": {
        "title": "Full FastAPI App: AI-Powered Code Review Service",
        "prompt": (
            "Build a complete production-ready Python FastAPI application for an AI-powered "
            "code review service. This should be real, working code I can run immediately.\n\n"
            "Implement:\n"
            "1. **FastAPI app structure** with routers, models, and config\n"
            "2. **POST /review endpoint** that accepts code (any language) and returns:\n"
            "   - Security vulnerabilities with severity (Critical/High/Medium/Low)\n"
            "   - Performance issues with suggested fixes\n"
            "   - Code quality score (0-100)\n"
            "   - Specific line-by-line suggestions\n"
            "3. **Streaming endpoint** POST /review/stream for real-time review output\n"
            "4. **Rate limiting** with slowapi (10 reviews/minute per IP)\n"
            "5. **SQLAlchemy models** for review history: Review, ReviewItem, User\n"
            "6. **Pydantic schemas** for all request/response models\n"
            "7. **Docker setup** with docker-compose for dev\n"
            "8. **Test suite** with pytest covering happy path + error cases\n\n"
            "Use: FastAPI, SQLAlchemy async, asyncpg, Pydantic v2, httpx, slowapi. "
            "Include all imports. Make it production-ready, not a toy example."
        ),
    },
    "fullstack": {
        "title": "Full-Stack Feature: Real-Time Dashboard with WebSockets",
        "prompt": (
            "Implement a complete full-stack real-time analytics dashboard feature for an AI gateway. "
            "This is the most complex demo — build ALL layers end-to-end.\n\n"
            "**Backend (FastAPI + PostgreSQL):**\n"
            "- WebSocket endpoint /ws/analytics that streams live request metrics every second\n"
            "- Aggregation queries: requests/sec, avg latency, cost rate, top models by volume\n"
            "- Background task that computes rolling 60-second window stats\n"
            "- SQLAlchemy async queries with proper indexing for time-series data\n\n"
            "**Frontend (React + TypeScript):**\n"
            "- useWebSocket hook that auto-reconnects on disconnect\n"
            "- Live line chart component (using recharts) showing requests/sec over 60s\n"
            "- Model distribution pie chart that updates in real-time\n"
            "- Stat cards: Total Requests, Avg Latency, Cost/Hour, Active Models\n"
            "- Connection status indicator with pulse animation\n\n"
            "**Integration:**\n"
            "- Authentication: Pass API key via WebSocket subprotocol header\n"
            "- Error handling: Graceful degradation when WS disconnects\n"
            "- Performance: Only re-render changed components (React.memo)\n\n"
            "Provide complete, copy-paste-ready code for every file. Include TypeScript types, "
            "proper error boundaries, and loading states. This should work out of the box."
        ),
    },
}

# ── ANSI Colors ──────────────────────────────────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
CYAN    = "\033[36m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
MAGENTA = "\033[35m"
BLUE    = "\033[34m"
RED     = "\033[31m"
WHITE   = "\033[97m"

STEP_ICONS = {
    "context":     "🌐",
    "intent":      "🧠",
    "llm_routing": "⚡",
    "agents":      "🤖",
    "tools":       "🔧",
    "generation":  "✍️ ",
}

MODEL_COLORS = {
    "openai":    CYAN,
    "anthropic": MAGENTA,
    "meta":      GREEN,
    "google":    YELLOW,
    "mistral":   BLUE,
    "qwen":      CYAN,
    "nous":      MAGENTA,
}


def colored_model(model_id: str) -> str:
    for provider, color in MODEL_COLORS.items():
        if provider in model_id.lower():
            return f"{color}{model_id}{RESET}"
    return f"{CYAN}{model_id}{RESET}"


def print_header(task: dict) -> None:
    width = 70
    print()
    print(f"{BOLD}{CYAN}{'═' * width}{RESET}")
    print(f"{BOLD}{CYAN}  🚀 NAMANGO AI GATEWAY — LIVE ORCHESTRATION DEMO{RESET}")
    print(f"{BOLD}{CYAN}{'═' * width}{RESET}")
    print(f"  {BOLD}Task:{RESET} {task['title']}")
    print(f"  {DIM}Gateway:{RESET} {DIM}{DEFAULT_GATEWAY}{RESET}")
    print(f"{CYAN}{'─' * width}{RESET}")
    print()


def print_step_start(step: str, label: str) -> None:
    icon = STEP_ICONS.get(step, "•")
    print(f"  {icon}  {YELLOW}{label}...{RESET}", end="", flush=True)


def print_step_done(step: str, label: str, details: dict) -> None:
    icon = STEP_ICONS.get(step, "•")

    if step == "llm_routing":
        model = details.get("model_id", details.get("llm", "unknown"))
        reason = details.get("reason", "")
        print(f"\r  {icon}  {GREEN}{label}{RESET}  →  {colored_model(model)}")
        if reason:
            short_reason = reason[:80] + "..." if len(reason) > 80 else reason
            print(f"       {DIM}{short_reason}{RESET}")

    elif step == "agents":
        agents = details.get("agents", [])
        count = details.get("count", len(agents))
        names = ", ".join(f"{a.get('icon','')} {a['name']}" for a in agents[:3])
        print(f"\r  {icon}  {GREEN}{label}{RESET}  →  {MAGENTA}{count} agents{RESET}: {names}")

    elif step == "tools":
        tools = details.get("tools_executed", [])
        if tools:
            names = ", ".join(t.get("tool", "") for t in tools[:3])
            print(f"\r  {icon}  {GREEN}{label}{RESET}  →  {CYAN}{len(tools)} tools{RESET}: {names}")
        else:
            print(f"\r  {icon}  {GREEN}{label}{RESET}")

    elif step == "generation":
        in_tok = details.get("input_tokens", 0)
        out_tok = details.get("output_tokens", 0)
        latency = details.get("latency_ms", 0)
        cost = details.get("cost_usd", 0)
        print(
            f"\r  {icon}  {GREEN}{label}{RESET}  "
            f"{DIM}{in_tok:,}→{out_tok:,} tokens  "
            f"{latency:,}ms  ${cost:.4f}{RESET}"
        )
    else:
        cat = details.get("category", "")
        complexity = details.get("complexity", "")
        suffix = f"  {DIM}{cat}/{complexity}{RESET}" if cat else ""
        print(f"\r  {icon}  {GREEN}{label}{RESET}{suffix}")


def stream_query(gateway_url: str, api_key: str, prompt: str, context_url: str = "",
                 preferred_model: str = "meta-llama/llama-3.1-70b-instruct") -> None:
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
    }
    body: dict = {"prompt": prompt, "preferred_model": preferred_model}
    if context_url:
        body["context_url"] = context_url

    print(f"  {DIM}{'─' * 60}{RESET}")
    print(f"  {BOLD}📡 Connecting to gateway stream...{RESET}")
    print()

    active_steps: dict = {}
    streamed_chars = 0
    response_lines = []
    usage: dict = {}
    metadata: dict = {}
    start = time.time()

    try:
        with httpx.stream(
            "POST",
            f"{gateway_url}/v1/query/stream",
            json=body,
            headers=headers,
            timeout=120.0,
        ) as resp:
            if resp.status_code != 200:
                raw = resp.read().decode()
                print(f"  {RED}Error {resp.status_code}: {raw[:200]}{RESET}")
                return

            buffer = ""
            for chunk in resp.iter_bytes():
                buffer += chunk.decode("utf-8", errors="replace")
                lines = buffer.split("\n")
                buffer = lines.pop()

                for line in lines:
                    if not line.startswith("data: "):
                        continue
                    raw = line[6:].strip()
                    if raw == "[DONE]":
                        break

                    try:
                        event = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    etype = event.get("type")

                    if etype == "step_start":
                        step = event.get("step", "")
                        label = event.get("label", step)
                        active_steps[step] = label
                        print_step_start(step, label)

                    elif etype == "step_complete":
                        step = event.get("step", "")
                        label = event.get("label", step)
                        details = event.get("details", {})
                        active_steps.pop(step, None)
                        print_step_done(step, label, details)

                    elif etype == "token":
                        text = event.get("text", "")
                        if streamed_chars == 0:
                            print()
                            print(f"  {CYAN}{'─' * 60}{RESET}")
                            print(f"  {BOLD}Response:{RESET}")
                            print()
                        sys.stdout.write(text)
                        sys.stdout.flush()
                        streamed_chars += len(text)
                        response_lines.append(text)

                    elif etype == "metadata":
                        metadata = event

                    elif etype == "done":
                        usage = {
                            "input_tokens": event.get("input_tokens", 0),
                            "output_tokens": event.get("output_tokens", 0),
                            "cost_usd": event.get("cost_usd", 0),
                            "latency_ms": event.get("latency_ms", 0),
                        }
                        # Gateway sends full response in done event (not per-token)
                        full_response = event.get("response", "")
                        if full_response and streamed_chars == 0:
                            print()
                            print(f"  {CYAN}{'─' * 60}{RESET}")
                            print(f"  {BOLD}Response:{RESET}")
                            print()
                            # Print with slight indentation, preserving newlines
                            for line in full_response.split("\n"):
                                print(f"  {line}")
                                sys.stdout.flush()
                            streamed_chars = len(full_response)

                    elif etype == "error":
                        print(f"\n  {RED}Error: {event.get('detail', 'unknown')}{RESET}")

    except httpx.ReadTimeout:
        print(f"\n  {RED}Timeout — gateway took too long to respond{RESET}")
    except Exception as e:
        print(f"\n  {RED}Connection error: {e}{RESET}")

    elapsed = time.time() - start

    # ── Summary ──
    print()
    print()
    print(f"  {CYAN}{'═' * 60}{RESET}")
    print(f"  {BOLD}📊 Orchestration Summary{RESET}")
    print(f"  {CYAN}{'─' * 60}{RESET}")

    if metadata:
        llm = metadata.get("selected_llm", "—")
        agents = metadata.get("selected_agents", [])
        tools = metadata.get("selected_tools", [])
        cat = metadata.get("task_category", "—")
        complexity = metadata.get("complexity", "—")
        reason = metadata.get("routing_reason", "")

        print(f"  {BOLD}LLM Selected:{RESET}   {colored_model(llm)}")
        print(f"  {BOLD}Task Category:{RESET}  {YELLOW}{cat}{RESET}  ({complexity} complexity)")
        if agents:
            print(f"  {BOLD}Agents Used:{RESET}    {MAGENTA}{', '.join(agents)}{RESET}")
        if tools:
            print(f"  {BOLD}Tools Run:{RESET}      {CYAN}{', '.join(tools)}{RESET}")
        if reason:
            short = reason[:100] + "..." if len(reason) > 100 else reason
            print(f"  {BOLD}Routing:{RESET}        {DIM}{short}{RESET}")

    if usage:
        in_tok = usage["input_tokens"]
        out_tok = usage["output_tokens"]
        cost = usage["cost_usd"]
        latency = usage["latency_ms"]
        total_tok = in_tok + out_tok
        tps = out_tok / (latency / 1000) if latency > 0 else 0

        print(f"  {CYAN}{'─' * 60}{RESET}")
        print(f"  {BOLD}Tokens:{RESET}         {GREEN}{in_tok:,} in + {out_tok:,} out = {total_tok:,} total{RESET}")
        print(f"  {BOLD}Speed:{RESET}          {GREEN}{tps:.0f} tokens/sec{RESET}")
        print(f"  {BOLD}Latency:{RESET}        {YELLOW}{latency:,}ms{RESET}")
        print(f"  {BOLD}Cost:{RESET}           {GREEN}${cost:.6f}{RESET}")
        print(f"  {BOLD}Wall time:{RESET}      {elapsed:.1f}s")

    print(f"  {CYAN}{'═' * 60}{RESET}")
    print()
    print(f"  {DIM}📈 View live metrics: https://frontend-five-theta-69.vercel.app{RESET}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Namango Gateway Demo CLI")
    parser.add_argument(
        "--task", "-t",
        choices=list(TASKS.keys()),
        default="planning",
        help=f"Demo task to run (default: planning). Options: {', '.join(TASKS)}"
    )
    parser.add_argument("--url", default=DEFAULT_GATEWAY, help="Gateway base URL")
    parser.add_argument("--key", default=DEFAULT_KEY, help="Gateway API key")
    parser.add_argument("--context-url", default="", help="Optional URL to scrape for context")
    parser.add_argument(
        "--model", "-m",
        default="meta-llama/llama-3.1-70b-instruct",
        help="Preferred LLM model (default: meta-llama/llama-3.1-70b-instruct)"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available demo tasks"
    )
    args = parser.parse_args()

    if args.list:
        print(f"\n{BOLD}Available demo tasks:{RESET}\n")
        for key, task in TASKS.items():
            print(f"  {CYAN}{key:12}{RESET}  {task['title']}")
        print()
        print(f"Usage: python demo_cli.py --task <name>\n")
        return

    task = TASKS[args.task]
    print_header(task)

    # Print the prompt (truncated)
    prompt_preview = task["prompt"][:200].replace("\n", " ")
    print(f"  {BOLD}Prompt preview:{RESET}")
    print(f"  {DIM}{prompt_preview}...{RESET}")
    print()

    stream_query(args.url, args.key, task["prompt"], args.context_url, args.model)


if __name__ == "__main__":
    main()
