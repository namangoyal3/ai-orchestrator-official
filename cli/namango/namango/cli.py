#!/usr/bin/env python3
"""
Namango AI Gateway — Product Builder Demo CLI
=============================================
Sends a real software product-building task to the gateway.
The gateway orchestrates: intent analysis → LLM routing → agent selection → code generation.
The CLI renders the orchestration architecture live in the terminal as it runs.

Usage:
    python demo_cli.py                          # default: build a task queue system
    python demo_cli.py --task router            # build a mini LLM router
    python demo_cli.py --task monitor           # build an API cost monitor
    python demo_cli.py --task pipeline          # build a data pipeline
    python demo_cli.py --save ./output          # save generated code to disk
    python demo_cli.py --list                   # show all tasks

GATEWAY_URL and API_KEY can also be set as env vars.
"""
from __future__ import annotations

import os
import sys
import json
import time
import re
import argparse
import textwrap
import shutil
from pathlib import Path
import httpx

# ── Config ───────────────────────────────────────────────────────────────────
DEFAULT_GATEWAY = os.getenv("GATEWAY_URL", "https://ai-gateway-backend-production.up.railway.app")
DEFAULT_KEY     = os.getenv("API_KEY", "gw-bn1RrcLqzARb5mPpBMiCzB0ZbxhpCVasQ_5hz9aWIrE")
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

# ── Product-Building Tasks ────────────────────────────────────────────────────
TASKS = {

    "taskqueue": {
        "title":    "Build: Distributed Task Queue System in Python",
        "tagline":  "Workers · Queue · Retry Logic · Dashboard · CLI",
        "model":    DEFAULT_MODEL,
        "prompt": textwrap.dedent("""\
            Write a single Python file called taskqueue.py — a complete, fully-implemented
            in-process task queue with background workers. Every function must be fully
            implemented with real code. No stubs, no `pass`, no `# TODO`.

            First, print this ASCII architecture diagram as a comment block at the top:
            # Producer → [Queue] → Worker-1
            #                    → Worker-2   → ResultStore
            #                    → Worker-3
            # RetryWorker ← FailedQueue (up to 3 retries, exponential backoff)

            IMPLEMENT ALL OF THE FOLLOWING in taskqueue.py (~120 lines):

            class Task:
                id: str          # uuid4
                type: str        # "shell" | "http" | "python"
                payload: dict    # {"cmd": "..."} or {"url": "..."} or {"code": "..."}
                priority: int    # 1=low, 5=high (default 3)
                status: str      # "pending" | "running" | "done" | "failed"
                retries: int     # attempts so far
                result: str      # output or error message
                created_at: float

            class TaskQueue:
                def enqueue(self, task_type, payload, priority=3) -> Task
                def dequeue(self) -> Task | None   # returns highest-priority pending task
                def ack(self, task_id, result)     # mark done
                def fail(self, task_id, reason)    # mark failed, schedule retry if retries < 3
                def status(self) -> dict            # {pending, running, done, failed, total}
                def pending_list(self) -> list[Task]

            class Worker:
                def __init__(self, queue: TaskQueue, worker_id: int)
                def execute(self, task: Task) -> str:
                    # "shell": subprocess.run(task.payload["cmd"], shell=True, capture_output=True)
                    # "http":  httpx.get(task.payload["url"], timeout=10)
                    # "python": exec(task.payload["code"]) capturing stdout via io.StringIO
                    # returns output string or raises exception

            def run_demo():
                # Creates a queue, submits 5 varied tasks (mix of types and priorities),
                # runs 2 workers concurrently using threading.Thread,
                # prints live status table every 0.5s using rich until all tasks complete,
                # then prints final results table (id, type, status, result[:60])

            if __name__ == "__main__":
                run_demo()

            REQUIREMENTS:
            - stdlib only (threading, subprocess, io, uuid, time) + httpx + rich
            - All code fully implemented — no `pass`, no `...`, no stubs
            - run_demo() must work when executed: python taskqueue.py
        """),
    },

    "support": {
        "title":    "Build: Customer Support Platform (SaaS Helpdesk)",
        "tagline":  "Tickets · SLA Tracking · Auto-triage · Agent Queue · REST API",
        "model":    DEFAULT_MODEL,
        "prompt": textwrap.dedent("""\
            Write a single Python file called helpdesk.py — a complete, fully-implemented
            customer support API. Every function must be fully implemented with real code.
            No stubs, no `pass`, no `# TODO`, no `...`.

            First, print this ASCII architecture diagram as a comment block at the top:
            # Customer ──POST /tickets──▶ auto_triage() ──▶ SQLite DB
            #                                 │                  │
            #                          assign_agent()     sla_deadline set
            #                                 │
            # Agent ◀── GET /agent/queue ─────┘
            # Agent ──POST /agent/reply──▶ notify customer

            IMPLEMENT ALL OF THE FOLLOWING in helpdesk.py (~150 lines), using FastAPI + sqlite3:

            DATABASE (sqlite3, file: helpdesk.db, created on startup):
            - tickets: id TEXT (TICKET-001...), subject, body, customer_email, status,
                       priority, category, agent_id, sla_deadline, created_at, resolved_at
            - messages: id, ticket_id, body, author (customer|agent), created_at

            def auto_triage(subject: str, body: str) -> dict:
                # Returns {priority, category, sla_hours} using keyword rules:
                # subject/body contains "down"|"outage"|"broken" → priority=urgent, sla=1h
                # contains "billing"|"charge"|"payment" → priority=high, sla=4h
                # contains "bug"|"error"|"crash" → priority=high, sla=4h
                # contains "feature"|"request" → priority=low, sla=72h
                # else → priority=medium, sla=24h, category=general
                # category: billing|bug|feature|general (from same keywords)

            FastAPI app = FastAPI(title="Helpdesk API"):

            POST /tickets  body: {subject, body, customer_email}
                → calls auto_triage(), assigns agent_id = (ticket_count % 3) + 1
                → inserts ticket with sla_deadline = now + sla_hours
                → returns {ticket_id, priority, category, sla_deadline, agent_id, message: "Ticket created"}

            GET /tickets/{ticket_id}
                → returns ticket row + all messages for that ticket as {ticket: {...}, messages: [...]}

            GET /tickets?email=alice@example.com
                → returns all tickets for that customer email, sorted by created_at desc

            POST /tickets/{ticket_id}/reply  body: {body, customer_email}
                → inserts message with author="customer", updates ticket status="pending"
                → returns {message_id, ticket_id, status: "pending"}

            GET /agent/queue?agent_id=1
                → returns open+pending tickets for that agent, ordered by priority
                   (urgent first, then high, medium, low), includes sla_breach=true if past deadline

            POST /agent/reply  body: {ticket_id, body}
                → inserts message with author="agent", updates ticket status="open"
                → returns {message_id, ticket_id}

            GET /agent/stats
                → returns {total_open, total_pending, total_resolved, sla_breached, avg_resolution_hrs}
                   computed with SQL COUNT and AVG queries

            SEED DATA — on startup if DB is empty, insert:
                3 tickets with different priorities and realistic subjects:
                  TICKET-001: "Payment failed on checkout" (high, billing)
                  TICKET-002: "App crashes on iOS 17" (high, bug)
                  TICKET-003: "Add dark mode please" (low, feature)
                With one message each from the customer.

            REQUIREMENTS:
            - Dependencies: fastapi, uvicorn only (sqlite3 is stdlib)
            - All code fully implemented — no `pass`, no `...`, no stubs
            - Run with: uvicorn helpdesk:app --reload
        """),
    },

    "monitor": {
        "title":    "Build: Real-Time API Cost Monitor",
        "tagline":  "Multi-Provider · Budget Alerts · Terminal Dashboard · CSV Export",
        "model":    DEFAULT_MODEL,
        "prompt": textwrap.dedent("""\
            Write a single Python file called cost_monitor.py — a complete, fully-implemented
            API cost tracker with a rich terminal dashboard. Every function must be fully
            implemented with real code. No stubs, no `pass`, no `# TODO`.

            First, print this ASCII architecture diagram as a comment block at the top:
            # Providers (OpenAI / Anthropic / OpenRouter)
            #      │
            #  log_usage()  ──▶  SQLite (usage_log table)
            #      │
            #  aggregate()  ──▶  [daily_cost, model_breakdown, budget_status]
            #      │
            #  check_alerts() ──▶  terminal warning if over threshold
            #      │
            #  dashboard()   ──▶  rich Live table (refreshes every 3s)

            IMPLEMENT ALL OF THE FOLLOWING in cost_monitor.py (~140 lines):

            DATABASE (sqlite3, file: costs.db, auto-created):
            - usage_log: id, provider, model, input_tokens, output_tokens,
                         cost_usd, request_at (ISO timestamp)

            def log_usage(provider, model, input_tokens, output_tokens, cost_usd):
                # Inserts a row into usage_log with current timestamp

            def daily_summary() -> list[dict]:
                # Returns [{date, provider, requests, total_tokens, total_cost_usd}]
                # grouped by date + provider, ordered by date desc, limit 14 days

            def model_breakdown() -> list[dict]:
                # Returns [{model, provider, requests, total_tokens, total_cost_usd, avg_cost_per_request}]
                # ordered by total_cost_usd desc

            def budget_status(daily_limit_usd: float) -> dict:
                # Returns {today_spend, daily_limit, pct_used, remaining, on_track_to_exceed}
                # on_track_to_exceed: True if (today_spend / hours_elapsed * 24) > daily_limit

            def check_alerts(daily_limit_usd: float, threshold_pct: float = 80.0) -> str | None:
                # Returns a warning string if pct_used >= threshold_pct, else None
                # e.g. "⚠️  BUDGET ALERT: 83% of $50.00 daily limit used ($41.50 of $50.00)"

            def seed_demo_data():
                # Inserts 30 realistic usage rows spread across last 7 days:
                # Mix of providers: openai (gpt-4o, gpt-4o-mini), anthropic (claude-3-5-sonnet),
                # openrouter (llama-3.1-70b), with realistic token counts and costs
                # Only seeds if usage_log is empty

            def print_dashboard(daily_limit_usd: float = 50.0):
                # Uses rich to print:
                # 1. A budget progress bar: "Today: $X.XX / $Y.YY  [=====>    ] 52%"
                # 2. A Table: "Daily Summary (last 7 days)" with columns:
                #    Date | Provider | Requests | Tokens | Cost
                # 3. A Table: "Model Breakdown" with columns:
                #    Model | Provider | Requests | Tokens | Total Cost | Avg/Request
                # 4. Any budget alert in red if triggered

            if __name__ == "__main__":
                import sys
                seed_demo_data()
                if "--export" in sys.argv:
                    # Print CSV of daily_summary() to stdout
                    import csv, io
                    rows = daily_summary()
                    w = csv.DictWriter(io.sys.stdout, fieldnames=rows[0].keys())
                    w.writeheader(); w.writerows(rows)
                else:
                    print_dashboard()

            REQUIREMENTS:
            - Dependencies: rich only (sqlite3 is stdlib)
            - All code fully implemented — no `pass`, no `...`, no stubs
            - Run with: python cost_monitor.py
        """),
    },

    "pipeline": {
        "title":    "Build: Async Data Pipeline with Fan-Out",
        "tagline":  "Ingestion · Transform · Fan-Out · Dead Letter · Metrics",
        "model":    DEFAULT_MODEL,
        "prompt": textwrap.dedent("""\
            Write a single Python file called pipeline.py — a complete, fully-implemented
            async data pipeline with a fluent builder API, transforms, fan-out sinks, and
            a dead letter queue. Every method must be fully implemented. No stubs, no `pass`.

            First, print this ASCII architecture diagram as a comment block at the top:
            # Source ──▶ [FilterTransform] ──▶ [MapTransform] ──▶ FanOutRouter
            #                                                           │
            #                                              ┌───────────┼───────────┐
            #                                           LogSink   FileSink   HTTPSink
            #                                                           │
            #                                              failed ──▶ DeadLetterQueue
            #                                                           │
            #                                              RetryWorker (up to 3x)

            IMPLEMENT ALL OF THE FOLLOWING in pipeline.py (~160 lines):

            class Record:
                data: dict
                source: str
                attempt: int = 0

            class FilterTransform:
                def __init__(self, predicate):  # e.g. lambda r: r["age"] > 18
                def process(self, record: Record) -> Record | None:
                    # Returns record if predicate(record.data) is True, else None (dropped)

            class MapTransform:
                def __init__(self, fn):  # e.g. lambda r: {**r, "name": r["name"].upper()}
                def process(self, record: Record) -> Record:
                    # Returns new Record with data = fn(record.data)

            class LogSink:
                def write(self, record: Record):
                    # Prints: "[LogSink] {record.data}" to stdout

            class FileSink:
                def __init__(self, path: str)
                def write(self, record: Record):
                    # Appends JSON line to file at path (creates if not exists)

            class DeadLetterQueue:
                def __init__(self, path="failed.jsonl")
                def push(self, record: Record, reason: str):
                    # Appends {data, source, attempt, reason, failed_at} as JSON line to path
                def drain(self) -> list[Record]:
                    # Reads all records from file, returns as list, clears file

            class Pipeline:
                def __init__(self, name: str)
                def source(self, records: list[dict]) -> "Pipeline":  # sets input records
                def transform(self, t) -> "Pipeline":                 # appends to transform chain
                def fan_out(self, sinks: list) -> "Pipeline":         # sets output sinks
                def dead_letter(self, dlq: DeadLetterQueue) -> "Pipeline"

                async def run(self) -> dict:
                    # 1. For each record in source:
                    #    a. Run through each transform in chain; if any returns None, skip record
                    #    b. Fan out to all sinks; if a sink raises, push to DLQ with reason
                    # 2. Returns {processed, dropped, failed, duration_ms}

            async def demo():
                # Creates a pipeline with:
                # - 10 sample user records: [{"name": "Alice", "age": 17}, {"name": "Bob", "age": 25}, ...]
                # - FilterTransform(lambda r: r["age"] >= 18)   # drop minors
                # - MapTransform(lambda r: {**r, "name": r["name"].upper(), "verified": True})
                # - fan_out: [LogSink(), FileSink("output.jsonl")]
                # - dead_letter: DeadLetterQueue("failed.jsonl")
                # Runs the pipeline and prints the result summary with rich:
                #   "Pipeline 'demo' complete: 7 processed, 3 dropped, 0 failed in 12ms"

            if __name__ == "__main__":
                import asyncio
                asyncio.run(demo())

            REQUIREMENTS:
            - stdlib only (asyncio, json, time, dataclasses) + rich for the summary print
            - All code fully implemented — no `pass`, no `...`, no stubs
            - Run with: python pipeline.py
        """),
    },
}

# ── Architecture Renderer ─────────────────────────────────────────────────────

def _term_width() -> int:
    return max(60, min(72, shutil.get_terminal_size(fallback=(80, 24)).columns - 4))


def render_gateway_architecture(steps_done: list[str], active_step: str | None) -> str:
    """Render the Namango gateway orchestration architecture as it executes."""
    W = _term_width()

    NODES = [
        ("context",     "🌐  Context Scraper"),
        ("intent",      "🧠  Intent Classifier"),
        ("llm_routing", "⚡  LLM Router"),
        ("agents",      "🤖  Agent Selector"),
        ("tools",       "🔧  Tool Executor"),
        ("generation",  "✍️   Code Generator"),
    ]

    lines = []
    lines.append(f"{CYAN}╔{'═' * (W-2)}╗{R}")
    lines.append(f"{CYAN}║{BOLD}{'  NAMANGO GATEWAY — ORCHESTRATION PIPELINE':^{W-2}}{R}{CYAN}║{R}")
    lines.append(f"{CYAN}╠{'═' * (W-2)}╣{R}")

    for i, (step_id, label) in enumerate(NODES):
        is_done   = step_id in steps_done
        is_active = step_id == active_step

        if is_active:
            status_icon = f"{BYLW}▶ RUNNING {R}"
            color = BYLW
        elif is_done:
            status_icon = f"{BGRN}✓ DONE    {R}"
            color = BGRN
        else:
            status_icon = f"{DIM}  PENDING {R}"
            color = DIM

        node_str = f"{color}{label:<26}{R}"
        line = f"{CYAN}║{R}  {node_str}  {status_icon}  {CYAN}║{R}"
        lines.append(line)

        # Arrow between nodes (except after last)
        if i < len(NODES) - 1:
            arrow_color = GRN if (step_id in steps_done) else DIM
            lines.append(f"{CYAN}║{R}  {arrow_color}{'':4}↓{R}{'':50}  {CYAN}║{R}")

    lines.append(f"{CYAN}╚{'═' * (W-2)}╝{R}")
    return "\n".join(lines)


# ── Step tracking (for re-rendering architecture) ────────────────────────────

STEP_DETAIL_LINES: list[str] = []

def record_step_done(step: str, label: str, details: dict) -> None:
    """Format a completed step detail line for the summary section."""
    if step == "llm_routing":
        model = details.get("model_id", details.get("llm", "?"))
        STEP_DETAIL_LINES.append(f"  {GRN}⚡  Router chose:{R} {CYAN}{model}{R}")

    elif step == "agents":
        agents = details.get("agents", [])
        names = "  ".join(f"{a.get('icon','')} {a['name']}" for a in agents)
        if names:
            STEP_DETAIL_LINES.append(f"  {GRN}🤖  Agents:{R} {MAG}{names}{R}")

    elif step == "tools":
        tools = [t.get("tool","") for t in details.get("tools_executed", [])]
        if tools:
            STEP_DETAIL_LINES.append(f"  {GRN}🔧  Tools:{R} {CYAN}{', '.join(tools)}{R}")

    elif step == "generation":
        in_t = details.get("input_tokens", 0)
        out_t = details.get("output_tokens", 0)
        lat  = details.get("latency_ms", 0)
        cost = details.get("cost_usd", 0.0)
        STEP_DETAIL_LINES.append(
            f"  {GRN}✍️   Generated:{R} {BGRN}{in_t:,} in → {out_t:,} out{R}"
            f"  {DIM}{lat:,}ms  ${cost:.4f}{R}"
        )


# ── Main streaming function ───────────────────────────────────────────────────

def stream_build(gateway_url: str, api_key: str, task: dict, save_dir: str | None) -> None:
    W = _term_width()
    IS_TTY = sys.stdout.isatty()

    # ── Header ─────────────────────────────────────────────────────────────
    print()
    print(f"{CYAN}╔{'═'*(W-2)}╗{R}")
    print(f"{CYAN}║{BOLD}{'  NAMANGO GATEWAY — PRODUCT BUILDER DEMO':^{W-2}}{R}{CYAN}║{R}")
    print(f"{CYAN}╠{'═'*(W-2)}╣{R}")
    print(f"{CYAN}║{R}  {BOLD}Task:{R}  {task['title']}")
    print(f"{CYAN}║{R}  {DIM}{task['tagline']}{R}")
    print(f"{CYAN}╚{'═'*(W-2)}╝{R}")
    print()

    # ── Initial architecture render (all pending) ───────────────────────────
    arch_text = render_gateway_architecture([], None)
    print(arch_text)
    print()
    print(f"  {DIM}Sending request to gateway...{R}", flush=True)
    print()

    steps_done: list[str] = []
    active_step: str | None = None
    full_response = ""
    usage: dict = {}
    metadata: dict = {}
    start = time.time()

    arch_lines = len(arch_text.splitlines()) + 3  # arch + blank + status + blank

    def redraw(active: str | None = None) -> None:
        if IS_TTY:
            sys.stdout.write(f"\033[{arch_lines}A")
            sys.stdout.flush()
        new_arch = render_gateway_architecture(steps_done, active)
        print(new_arch)
        print(flush=True)

    headers = {"Content-Type": "application/json", "X-API-Key": api_key}
    body = {"prompt": task["prompt"], "preferred_model": task.get("model", DEFAULT_MODEL)}

    try:
        with httpx.stream("POST", f"{gateway_url}/v1/query/stream",
                          json=body, headers=headers, timeout=180.0) as resp:
            if resp.status_code != 200:
                print(f"\n  {RED}Error {resp.status_code}: {resp.read().decode()[:200]}{R}")
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
                        ev = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    etype = ev.get("type")

                    if etype == "step_start":
                        active_step = ev.get("step")
                        redraw(active_step)
                        step_label = ev.get("label", active_step)
                        print(f"  {BYLW}▶{R}  {step_label}...")
                        print()

                    elif etype == "step_complete":
                        sid = ev.get("step", "")
                        steps_done.append(sid)
                        active_step = None
                        record_step_done(sid, ev.get("label",""), ev.get("details", {}))
                        redraw(None)

                    elif etype == "token":
                        # Per-token streaming (if supported)
                        full_response += ev.get("text", "")

                    elif etype == "done":
                        usage = {k: ev.get(k, 0) for k in
                                 ("input_tokens", "output_tokens", "cost_usd", "latency_ms")}
                        if ev.get("response"):
                            full_response = ev["response"]

                    elif etype == "metadata":
                        metadata = ev

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

    # ── Response ───────────────────────────────────────────────────────────
    if full_response:
        print()
        print(f"{CYAN}{'═'*W}{R}")
        print(f"{BOLD}  📄  GENERATED OUTPUT{R}")
        print(f"{CYAN}{'─'*W}{R}")
        print()
        _pretty_print_response(full_response, W)

        # Save to disk
        if save_dir:
            _save_output(full_response, save_dir, task)

    # ── Orchestration summary ──────────────────────────────────────────────
    print()
    print(f"{CYAN}{'═'*W}{R}")
    print(f"{BOLD}  📊  ORCHESTRATION SUMMARY{R}")
    print(f"{CYAN}{'─'*W}{R}")
    print()

    for line in STEP_DETAIL_LINES:
        print(line)

    if metadata:
        cat = metadata.get("task_category", "—")
        cx  = metadata.get("complexity", "—")
        why = metadata.get("routing_reason", "")
        print(f"  {GRN}🧠  Category:{R} {YLW}{cat}{R}  ({cx})")
        if why:
            short = why[:90] + "..." if len(why) > 90 else why
            print(f"  {DIM}     {short}{R}")

    if usage:
        in_t  = usage["input_tokens"]
        out_t = usage["output_tokens"]
        cost  = usage["cost_usd"]
        lat   = usage["latency_ms"]
        tps   = out_t / (lat / 1000) if lat > 0 else 0
        print()
        print(f"  {BOLD}Tokens   {R}{BGRN}{in_t:,} in + {out_t:,} out = {in_t+out_t:,} total{R}")
        print(f"  {BOLD}Speed    {R}{BGRN}{tps:.0f} tokens/sec{R}   {DIM}({lat:,}ms gateway latency){R}")
        print(f"  {BOLD}Cost     {R}{BGRN}${cost:.6f}{R}  (via OpenRouter)")
        print(f"  {BOLD}Wall     {R}{elapsed:.1f}s end-to-end")

    print()
    print(f"{CYAN}{'─'*W}{R}")
    print(f"  {DIM}📈 Dashboard: https://frontend-five-theta-69.vercel.app{R}")
    if save_dir:
        print(f"  {DIM}💾 Code saved to: {save_dir}{R}")
    print(f"{CYAN}{'═'*W}{R}")
    print()


def _pretty_print_response(text: str, width: int = 72) -> None:
    """Print response with syntax-highlighted code blocks."""
    in_code = False
    lang = ""
    for line in text.split("\n"):
        if line.startswith("```"):
            if not in_code:
                in_code = True
                lang = line[3:].strip()
                fence = f"  {CYAN}┌─ {lang or 'code'} {'─'*(width-8-len(lang or 'code'))}┐{R}"
                print(fence)
            else:
                in_code = False
                print(f"  {CYAN}└{'─'*(width-4)}┘{R}")
        elif in_code:
            # Syntax-highlight key tokens
            hl = line
            for kw in ("def ", "class ", "async ", "await ", "import ", "from ", "return "):
                hl = hl.replace(kw, f"{MAG}{kw}{R}")
            for kw in ("if ", "else:", "elif ", "for ", "while ", "try:", "except ",
                       "with ", "raise ", "yield "):
                hl = hl.replace(kw, f"{BBLU}{kw}{R}")
            print(f"  {DIM}│{R} {hl}")
        else:
            # Markdown headings
            if line.startswith("## "):
                print(f"\n  {BOLD}{BCYAN}{line[3:]}{R}")
            elif line.startswith("# "):
                print(f"\n  {BOLD}{WHT}{line[2:]}{R}")
            elif line.startswith("**") and line.endswith("**"):
                print(f"  {BOLD}{line[2:-2]}{R}")
            elif line.startswith("- ") or line.startswith("* "):
                print(f"  {CYAN}•{R} {line[2:]}")
            else:
                # Wrap long lines
                if len(line) > width - 4:
                    for wrapped in textwrap.wrap(line, width - 4):
                        print(f"  {wrapped}")
                else:
                    print(f"  {line}")


def _save_output(text: str, save_dir: str, task: dict) -> None:
    """Extract code blocks from response and save to files."""
    out = Path(save_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Save full output
    (out / "output.md").write_text(f"# {task['title']}\n\n{text}\n")

    # Extract individual code files
    pattern = re.compile(r"```(?:python|bash|yaml|dockerfile|toml)?\n(.*?)```", re.DOTALL)
    blocks = pattern.findall(text)

    # Try to infer filenames from surrounding headings
    file_pattern = re.compile(
        r'(?:^|\n)(?:#+\s*)?`?(\w[\w./\-]*\.(?:py|sh|yaml|yml|toml|md|txt))`?\s*(?:[:\-—].*?)?\n```.*?\n(.*?)```',
        re.DOTALL
    )
    named = file_pattern.findall(text)
    saved = []
    for fname, code in named:
        fpath = out / fname
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text(code.strip() + "\n")
        saved.append(fname)

    # Fallback: save unnamed blocks as block_N.py
    if not saved and blocks:
        for i, code in enumerate(blocks, 1):
            (out / f"block_{i}.py").write_text(code.strip() + "\n")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Namango Gateway — Build anything with AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "prompt", nargs="?", default=None,
        help="What to build, e.g. 'build a rate limiter in Python'"
    )
    parser.add_argument("--url",  default=DEFAULT_GATEWAY, help="Gateway base URL")
    parser.add_argument("--key",  default=DEFAULT_KEY,     help="Gateway API key")
    parser.add_argument("--save", metavar="DIR",           help="Save generated code to DIR")
    args = parser.parse_args()

    # Interactive prompt if nothing given
    if not args.prompt:
        print(f"\n{CYAN}  Namango Gateway — AI Product Builder{R}")
        print(f"  {DIM}Describe what you want to build and the gateway will generate it.{R}\n")
        try:
            args.prompt = input(f"  {BOLD}What do you want to build?{R}  ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            return
        if not args.prompt:
            return

    # Build a task dict from the free-form prompt
    title = args.prompt if len(args.prompt) <= 60 else args.prompt[:57] + "..."
    task = {
        "title":   title,
        "tagline": "Custom build via Namango Gateway",
        "model":   DEFAULT_MODEL,
        "prompt":  (
            f"Write a single, complete, fully-implemented Python file for the following:\n\n"
            f"{args.prompt}\n\n"
            "REQUIREMENTS:\n"
            "- Single file, fully implemented — no stubs, no `pass`, no `# TODO`\n"
            "- Start with an ASCII architecture diagram as a comment block\n"
            "- Every function must contain real, working code\n"
            "- Include a runnable demo / main block at the bottom\n"
            "- Use only stdlib + httpx + rich (no other dependencies)\n"
        ),
    }

    stream_build(args.url, args.key, task, args.save)


if __name__ == "__main__":
    main()
