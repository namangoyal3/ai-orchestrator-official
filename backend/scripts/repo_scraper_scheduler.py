"""
repo_scraper_scheduler.py
─────────────────────────
Runs the GitHub repo scraper on a recurring schedule on Railway.
Searches for open-source AI/no-code/agent repos, deduplicates,
and upserts into the TrendingRepo table.

Usage:
    python scripts/repo_scraper_scheduler.py          # run on schedule (every 6h)
    python scripts/repo_scraper_scheduler.py --now    # run once immediately
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import time
import urllib.request
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("repo-scraper")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
JOBSTORE_URL = "sqlite:///scraper_jobs.db"
RUN_INTERVAL_HOURS = 6

SEARCH_QUERIES = [
    # AI agent frameworks
    "ai+agent+orchestrator+stars:>200",
    "multi+agent+system+llm+stars:>150",
    "autonomous+agent+llm+stars:>150",
    "agentic+workflow+framework+stars:>100",
    # No-code / low-code builders
    "no-code+ai+automation+stars:>200",
    "low-code+workflow+builder+stars:>200",
    "visual+workflow+ai+agent+stars:>100",
    "drag+drop+ai+workflow+stars:>100",
    "visual+ai+builder+stars:>100",
    "zapier+alternative+open+source+stars:>200",
    # MCP ecosystem
    "mcp+model+context+protocol+stars:>100",
    "model+context+protocol+server+stars:>100",
    # LLM tooling
    "llm+tool+calling+framework+stars:>200",
    "ai+workflow+automation+stars:>300",
]

RELEVANT_TERMS = [
    "ai", "agent", "tool", "mcp", "model", "context", "protocol",
    "orchestrat", "automat", "workflow", "no-code", "low-code", "visual"
]

CATEGORY_MAP = {
    "no-code": ["no-code", "nocode", "low-code", "lowcode", "drag", "visual", "builder"],
    "mcp": ["mcp", "model context protocol"],
    "agent": ["agent", "agentic", "autonomous", "swarm", "multi-agent"],
    "tool": ["tool", "calling", "function"],
    "workflow": ["workflow", "orchestrat", "pipeline", "automat"],
}


def _gh_request(path: str) -> Optional[Dict]:
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "ai-orchestrator-scraper/1.0",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    url = f"https://api.github.com/{path.lstrip('/')}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            remaining = r.headers.get("X-RateLimit-Remaining", "?")
            data = json.loads(r.read())
            return {"data": data, "remaining": remaining}
    except Exception as e:
        log.warning("GitHub request failed for %s: %s", path, e)
        return None


def scrape_github() -> List[Dict]:
    seen = set()
    results = []

    for query in SEARCH_QUERIES:
        resp = _gh_request(f"search/repositories?q={query}&sort=stars&order=desc&per_page=20")
        if not resp:
            continue
        items = resp["data"].get("items", [])
        remaining = resp["remaining"]
        log.info("Query '%s' → %s results (rate limit remaining: %s)", query[:50], len(items), remaining)

        for item in items:
            full_name = item["full_name"]
            if full_name in seen:
                continue
            seen.add(full_name)
            results.append({
                "github_url": item["html_url"],
                "name": item["name"],
                "full_name": full_name,
                "description": (item.get("description") or "")[:300],
                "stars": item["stargazers_count"],
                "forks": item["forks_count"],
                "language": item.get("language"),
                "topics": item.get("topics", []),
                "last_commit": item.get("pushed_at"),
                "updated_at": item.get("updated_at"),
            })

        time.sleep(1)  # be polite to GitHub API

    return results


def filter_repo(data: Dict) -> bool:
    if data["stars"] < 100:
        return False
    text = " ".join(data["topics"]) + " " + data["description"].lower()
    return any(term in text for term in RELEVANT_TERMS)


def categorize_repo(data: Dict) -> str:
    text = " ".join(data["topics"]) + " " + data["description"].lower()
    for category, keywords in CATEGORY_MAP.items():
        if any(kw in text for kw in keywords):
            return category
    return "general"


def upsert_repos(repos: List[Dict]) -> int:
    """Write results to a local JSON file (Railway-friendly, no DB setup needed)."""
    output_path = os.getenv("SCRAPER_OUTPUT", "/tmp/trending_repos.json")

    # Load existing
    existing = {}
    if os.path.exists(output_path):
        try:
            with open(output_path) as f:
                for r in json.load(f):
                    existing[r["github_url"]] = r
        except Exception:
            pass

    new_count = 0
    for repo in repos:
        if not filter_repo(repo):
            continue
        repo["category"] = categorize_repo(repo)
        repo["scraped_at"] = datetime.utcnow().isoformat()
        is_new = repo["github_url"] not in existing
        existing[repo["github_url"]] = repo
        if is_new:
            new_count += 1

    # Sort by stars descending
    sorted_repos = sorted(existing.values(), key=lambda x: x["stars"], reverse=True)

    with open(output_path, "w") as f:
        json.dump(sorted_repos, f, indent=2, default=str)

    log.info("Upserted %d repos. %d new. Total: %d. Saved to %s",
             len(repos), new_count, len(sorted_repos), output_path)
    return new_count


def run_scraper():
    log.info("=" * 60)
    log.info("Starting scrape run at %s UTC", datetime.utcnow().isoformat())
    repos = scrape_github()
    log.info("Found %d unique repos from GitHub search", len(repos))
    new_count = upsert_repos(repos)
    log.info("Scrape complete. %d new repos added.", new_count)
    log.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="GitHub Repo Scraper Scheduler")
    parser.add_argument("--now", action="store_true", help="Run once immediately and exit")
    args = parser.parse_args()

    if args.now:
        run_scraper()
        return

    scheduler = BlockingScheduler(
        jobstores={"default": SQLAlchemyJobStore(url=JOBSTORE_URL)},
        timezone="UTC",
    )

    scheduler.add_job(
        run_scraper,
        IntervalTrigger(hours=RUN_INTERVAL_HOURS),
        id="repo_scraper",
        replace_existing=True,
        misfire_grace_time=3600,
        next_run_time=datetime.utcnow(),  # run immediately on start
    )

    log.info("Scheduler started. Scraping every %dh. Press Ctrl+C to stop.", RUN_INTERVAL_HOURS)

    try:
        scheduler.start()
    except KeyboardInterrupt:
        log.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
