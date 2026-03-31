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
            Build a complete, production-ready distributed task queue system in Python.
            This must be real, runnable code — not pseudocode.

            SYSTEM ARCHITECTURE (ASCII diagram required first):
            Show the full architecture: Producer → Queue → Workers → Result Store → CLI Monitor

            COMPONENTS TO BUILD (each as a separate file):

            1. queue_server.py — In-memory queue server over TCP (asyncio):
               - ENQUEUE <task_id> <payload_json> → stores task
               - DEQUEUE → returns next pending task (FIFO)
               - ACK <task_id> → marks complete
               - FAIL <task_id> <reason> → marks failed, increments retry count
               - STATUS → returns JSON: {pending, running, done, failed, total}
               - Auto-retry failed tasks up to 3 times with exponential backoff

            2. worker.py — Task worker process:
               - Connects to queue server, polls for tasks
               - Executes task based on task type: "shell" (runs command), "http" (hits URL), "python" (evals code)
               - Reports ACK or FAIL back to server
               - Graceful shutdown on SIGTERM
               - Configurable concurrency (default: 4 parallel tasks)

            3. producer.py — CLI to submit tasks:
               - namango enqueue --type shell --cmd "echo hello" --priority high
               - namango enqueue --type http --url https://api.example.com/ping
               - namango enqueue --type python --code "import math; print(math.pi)"
               - namango enqueue --file tasks.json  (bulk submit from file)

            4. monitor.py — Live terminal dashboard:
               - Refreshes every second using curses or rich
               - Shows: Queue depth graph (last 60s), Worker status table, Recent task log, Throughput (tasks/sec)
               - Color-coded by status: pending=yellow, running=blue, done=green, failed=red

            5. Dockerfile + docker-compose.yml:
               - server, 3 workers, producer all in separate containers
               - Shared network, server exposed on port 9000

            REQUIREMENTS:
            - Zero external dependencies except: asyncio, rich, httpx
            - Complete imports in every file
            - Each file must be < 150 lines (clean, readable)
            - Include a README.md with quickstart (5 commands to run end-to-end demo)
        """),
    },

    "support": {
        "title":    "Build: Customer Support Platform (SaaS Helpdesk)",
        "tagline":  "Tickets · SLA Tracking · Auto-triage · Customer Portal · REST API",
        "model":    DEFAULT_MODEL,
        "prompt": textwrap.dedent("""\
            Build a complete, production-ready customer support platform in Python.
            This is a real B2B SaaS product — runnable code, not pseudocode.

            SYSTEM ARCHITECTURE (ASCII diagram required first):
            Customer → Submit Ticket → Auto-Triage (priority + category) → Agent Queue
                                                                         → SLA Timer
                                                                         → Email Notify
            Agent → Respond → Customer Portal → Customer sees reply + status

            COMPONENTS TO BUILD:

            1. models.py — Data models (SQLite via aiosqlite):
               - Ticket: id, subject, body, customer_email, status (open/pending/resolved/closed),
                         priority (low/medium/high/urgent), category (billing/bug/feature/general),
                         created_at, updated_at, resolved_at, sla_deadline, agent_id
               - Message: id, ticket_id, body, author_type (customer/agent/system), created_at
               - Agent: id, name, email, active, current_load (# open tickets)
               - Customer: id, email, name, company, plan (free/pro/enterprise)

            2. triage.py — Automatic ticket triage:
               - triage(subject: str, body: str) → {priority, category, sla_hours}
               - Priority rules:
                 "urgent" | "down" | "outage" | "broken" → URGENT (SLA: 1h)
                 "billing" | "charge" | "invoice" → HIGH (SLA: 4h)
                 "bug" | "error" | "crash" → HIGH (SLA: 4h)
                 "feature" | "request" | "suggestion" → LOW (SLA: 72h)
                 default → MEDIUM (SLA: 24h)
               - Category detection via keyword matching
               - Returns SLA deadline = now + sla_hours

            3. api.py — FastAPI REST API:
               Customer-facing endpoints:
               - POST /tickets — submit new ticket {subject, body, customer_email}
                   → auto-triages, assigns agent (round-robin by load), sends confirmation
               - GET /tickets/{ticket_id}?email=... — customer views ticket + messages
               - POST /tickets/{ticket_id}/reply — customer replies to ticket
               - GET /tickets?email=... — customer sees all their tickets

               Agent-facing endpoints:
               - GET /agent/queue?agent_id=... — agent sees their open tickets (sorted by priority)
               - POST /agent/tickets/{ticket_id}/reply — agent sends reply
               - POST /agent/tickets/{ticket_id}/status — update status
               - GET /agent/sla-breaches — tickets past SLA deadline (sorted by overdue time)
               - GET /agent/stats — {open, pending, resolved_today, avg_response_time_hrs, sla_breach_rate}

            4. notifications.py — Email notification stubs:
               - notify_customer_new_ticket(ticket) → prints formatted email to stdout
               - notify_customer_reply(ticket, message) → prints formatted email
               - notify_agent_assigned(agent, ticket) → prints formatted email
               - notify_sla_warning(ticket, hours_remaining) → prints formatted alert
               - (Real SMTP send behind a SEND_EMAIL=true env flag)

            5. sla_monitor.py — Background SLA checker:
               - Runs as asyncio task, checks every 5 minutes
               - Finds tickets where sla_deadline < now and status not resolved/closed
               - Calls notify_sla_warning for tickets within 30 min of breach
               - Logs SLA breach to stderr with ticket_id, customer, priority, overdue_by

            6. seed.py — Demo data seeder:
               - Creates 3 agents, 10 customers (mix of free/pro/enterprise)
               - Creates 20 tickets with realistic subjects/bodies/statuses
               - Mix of priorities and categories
               - Some tickets with multiple back-and-forth messages
               - Some SLA-breached tickets for drama

            7. cli.py — Quick demo runner:
               - python cli.py submit --email alice@acme.com --subject "Payment failed" --body "..."
               - python cli.py view --ticket TICKET-001 --email alice@acme.com
               - python cli.py queue --agent 1
               - python cli.py stats
               - python cli.py seed  (runs seed.py)

            REQUIREMENTS:
            - Dependencies: fastapi, uvicorn, aiosqlite, rich, httpx only
            - All endpoints return proper JSON with status codes (201, 404, 422)
            - Ticket IDs are human-readable: TICKET-001, TICKET-002, ...
            - README.md: 5-command quickstart to run the full demo end-to-end
        """),
    },

    "monitor": {
        "title":    "Build: Real-Time API Cost Monitor",
        "tagline":  "Multi-Provider · Budget Alerts · Terminal UI · Webhooks",
        "model":    DEFAULT_MODEL,
        "prompt": textwrap.dedent("""\
            Build a real-time API cost monitoring tool that tracks spending across
            OpenAI, Anthropic, and OpenRouter — runnable from a single Python file.

            SYSTEM ARCHITECTURE (ASCII diagram required first):
            Providers → Fetcher (polling) → SQLite → Aggregator → [TUI Dashboard | Alert Engine | Webhook]

            COMPONENTS TO BUILD:

            1. fetcher.py — Cost data fetcher:
               - Polls each provider's billing API every 60 seconds
               - OpenAI: GET https://api.openai.com/v1/usage (with OPENAI_API_KEY)
               - Anthropic: parses usage from response headers (anthropic-tokens-used)
               - OpenRouter: GET https://openrouter.ai/api/v1/auth/key (shows credits used)
               - Stores raw usage events in SQLite

            2. aggregator.py — Usage aggregation:
               - hourly_cost(provider) → cost per hour for last 24h
               - model_breakdown() → {model: {requests, tokens, cost}} sorted by cost desc
               - budget_status(daily_limit_usd) → {used, remaining, percent, on_track_to_exceed: bool}
               - trend(days=7) → list of {date, cost} for sparkline

            3. alerts.py — Alert engine:
               - check_budget(threshold_pct=80) → fires alert if over threshold
               - Delivery methods: terminal bell + colored warning, webhook POST, email (smtplib)
               - Cooldown: don't re-alert same threshold within 1 hour
               - Config via ~/.namango/alerts.json

            4. dashboard.py — Rich terminal dashboard (refreshes every 5s):
               - Top bar: total today / monthly pace / budget % bar
               - Provider cards: each shows hourly sparkline + today's cost
               - Model table: sorted by cost, with per-request cost
               - Recent alerts panel: last 5 alerts with timestamps

            5. monitor.py — Single entrypoint:
               - python monitor.py --watch (live dashboard)
               - python monitor.py --report (print daily report and exit)
               - python monitor.py --set-budget openai 50 (set $50/day limit)
               - python monitor.py --export csv (export last 30 days to CSV)

            REQUIREMENTS:
            - Dependencies: rich, httpx, aiosqlite only
            - All provider keys read from env vars (OPENAI_API_KEY, ANTHROPIC_API_KEY, OPENROUTER_API_KEY)
            - README with setup + first-run instructions
        """),
    },

    "pipeline": {
        "title":    "Build: Async Data Pipeline with Fan-Out",
        "tagline":  "Ingestion · Transform · Fan-Out · Dead Letter · Metrics",
        "model":    DEFAULT_MODEL,
        "prompt": textwrap.dedent("""\
            Build a complete async data pipeline framework in Python with fan-out,
            dead letter queue, and metrics. Production-ready, runnable code.

            SYSTEM ARCHITECTURE (ASCII diagram required first):
            Source(s) → Ingester → [Transform Chain] → Fan-Out Router → Sink(s)
                                                    ↓
                                              Dead Letter Queue → Retry Worker

            COMPONENTS TO BUILD:

            1. pipeline.py — Core pipeline engine:
               - Pipeline(name) builder API:
                 p = Pipeline("etl")
                   .source(CSVSource("data.csv"))
                   .transform(FilterTransform(lambda r: r["age"] > 18))
                   .transform(MapTransform(lambda r: {**r, "name": r["name"].upper()}))
                   .fan_out([
                       Sink("postgres", PostgresSink(dsn=...)),
                       Sink("s3",       S3Sink(bucket="output")),
                       Sink("log",      LogSink()),
                   ])
                   .dead_letter(FileSink("failed.jsonl"))
                 await p.run()
               - Backpressure: max 1000 records in-flight, pause ingestion if exceeded
               - Checkpoint: saves last processed offset to disk for resume

            2. sources.py — Data sources:
               - CSVSource(path, batch_size=100): reads CSV in batches
               - JSONLSource(path): reads newline-delimited JSON
               - HTTPSource(url, interval_secs=60): polls HTTP endpoint for JSON
               - AsyncGenSource(gen): wraps any async generator

            3. transforms.py — Transformation primitives:
               - FilterTransform(predicate): drops records not matching
               - MapTransform(fn): 1-to-1 transformation
               - FlatMapTransform(fn): 1-to-many expansion
               - EnrichTransform(async_fn): async lookup enrichment (e.g. geocoding)
               - ValidateTransform(schema: dict): JSON schema validation, routes invalid to DLQ

            4. sinks.py — Output sinks:
               - LogSink: prints to stdout with pretty formatting
               - FileSink(path): writes JSONL to file, flushes every 100 records
               - HTTPSink(url): POSTs each record, retries 3x with backoff
               - BufferedSink(inner, buffer_size=500): batches records before flushing

            5. metrics.py — Pipeline metrics:
               - Counters: records_in, records_out, records_failed, bytes_processed
               - Timers: transform_latency_p50/p95/p99, sink_latency
               - Reporter: prints live metrics table every 10s using rich
               - Export: Prometheus /metrics endpoint (optional, via fastapi)

            6. cli.py — Pipeline runner CLI:
               - python cli.py run pipeline.yaml     (run from YAML config)
               - python cli.py validate pipeline.yaml (dry-run, no sinks write)
               - python cli.py stats                  (show last run metrics)
               - python cli.py replay --from checkpoint.json (resume from checkpoint)

            REQUIREMENTS:
            - Dependencies: rich, httpx, aiofiles, pydantic only
            - Full type annotations throughout
            - Example pipeline.yaml showing real usage
            - README: 3-command quickstart with sample data
        """),
    },
}

# ── Architecture Renderer ─────────────────────────────────────────────────────

def render_gateway_architecture(steps_done: list[str], active_step: str | None) -> str:
    """Render the Namango gateway orchestration architecture as it executes."""
    W = 72

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
    W = 72

    # ── Header ─────────────────────────────────────────────────────────────
    print()
    print(f"{CYAN}╔{'═'*(W-2)}╗{R}")
    print(f"{CYAN}║{BOLD}{'  🏗️  NAMANGO GATEWAY — PRODUCT BUILDER DEMO':^{W-2}}{R}{CYAN}║{R}")
    print(f"{CYAN}╠{'═'*(W-2)}╣{R}")
    print(f"{CYAN}║{R}  {BOLD}Task:{R}  {WHT}{task['title']}{R}")
    print(f"{CYAN}║{R}  {DIM}{task['tagline']}{R}")
    print(f"{CYAN}║{R}  {DIM}Gateway: {gateway_url}{R}")
    print(f"{CYAN}╚{'═'*(W-2)}╝{R}")
    print()

    # ── Initial architecture render (all pending) ───────────────────────────
    print(render_gateway_architecture([], None))
    print()
    print(f"  {DIM}Sending request to gateway...{R}")
    print()

    steps_done: list[str] = []
    active_step: str | None = None
    full_response = ""
    usage: dict = {}
    metadata: dict = {}
    start = time.time()

    CLEAR_ARCH = f"\033[{len(render_gateway_architecture([],[]).splitlines()) + 3}A"

    def redraw(active: str | None = None) -> None:
        print(CLEAR_ARCH, end="")
        print(render_gateway_architecture(steps_done, active))
        print()

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
        description="Namango Gateway — Product Builder Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--task", "-t",
        choices=list(TASKS),
        default="support",
        help="Which product to build (default: support)"
    )
    parser.add_argument("--url",  default=DEFAULT_GATEWAY, help="Gateway base URL")
    parser.add_argument("--key",  default=DEFAULT_KEY,     help="Gateway API key")
    parser.add_argument("--save", metavar="DIR",           help="Save generated code to DIR")
    parser.add_argument("--list", "-l", action="store_true", help="List all tasks and exit")
    args = parser.parse_args()

    if args.list:
        print(f"\n{BOLD}Available build tasks:{R}\n")
        for k, t in TASKS.items():
            print(f"  {CYAN}{k:<12}{R}  {BOLD}{t['title']}{R}")
            print(f"  {'':12}  {DIM}{t['tagline']}{R}\n")
        print(f"Usage: python demo_cli.py --task <name> [--save ./output]\n")
        return

    task = TASKS[args.task]
    stream_build(args.url, args.key, task, args.save)


if __name__ == "__main__":
    main()
