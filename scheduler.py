"""
scheduler.py
────────────
Runs the pipeline on a daily schedule using APScheduler with a persistent
SQLAlchemy job store. Jobs survive process restarts; missed runs within the
grace period are caught up automatically.

Usage:
    python scheduler.py              # run forever, post at POST_TIME_UTC daily
    python scheduler.py --now        # run immediately then exit
    python scheduler.py --topic "X"  # run immediately with a specific topic

Dependencies (add to requirements.txt):
    apscheduler>=3.10
    sqlalchemy>=2.0
"""

from __future__ import annotations

import argparse
import logging
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from rich.console import Console

from config import Config
from pipeline import run_pipeline


console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("scheduler")

# Scheduler state is persisted here so jobs survive restarts.
JOBSTORE_URL = "sqlite:///scheduler_jobs.db"


def _job(topic: str | None = None) -> None:
    """Wrapper called by APScheduler. Loads config fresh each run."""
    cfg = Config.from_env()
    try:
        result = run_pipeline(cfg, topic=topic)
        log.info("Pipeline completed. Post URN: %s", result["post_urn"])
    except Exception as exc:
        log.exception("Pipeline failed: %s", exc)


def main() -> None:
    parser = argparse.ArgumentParser(description="LinkedIn AI Avatar Automation")
    parser.add_argument("--now", action="store_true", help="Run the pipeline immediately")
    parser.add_argument("--topic", type=str, default=None, help="Explicit topic to use")
    args = parser.parse_args()

    cfg = Config.from_env()

    if args.now or args.topic:
        console.print("[bold yellow]Running pipeline immediately…[/bold yellow]")
        _job(topic=args.topic)
        return

    # ── Scheduled mode ────────────────────────────────────────────────────────
    post_time = cfg.post_time_utc          # e.g. "09:00"
    hour, minute = post_time.split(":")

    scheduler = BlockingScheduler(
        jobstores={"default": SQLAlchemyJobStore(url=JOBSTORE_URL)},
        timezone="UTC",
    )

    scheduler.add_job(
        _job,
        CronTrigger(hour=int(hour), minute=int(minute), timezone="UTC"),
        id="daily_pipeline",
        replace_existing=True,
        misfire_grace_time=3600,    # catch up if process was down for up to 1h
    )

    console.print(
        f"[bold green]Scheduler started.[/bold green] "
        f"Will post daily at [cyan]{post_time} UTC[/cyan]. "
        f"Job store: [dim]{JOBSTORE_URL}[/dim]"
    )
    console.print("Press Ctrl+C to stop.\n")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        console.print("\n[yellow]Scheduler stopped.[/yellow]")
        sys.exit(0)


if __name__ == "__main__":
    main()
