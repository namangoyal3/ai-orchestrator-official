"""
pipeline.py
───────────
Single-run pipeline: generate script → render avatar video → post to LinkedIn.
Called by the scheduler (scheduler.py) or run directly for a one-off post.
"""

from __future__ import annotations

import pathlib
import tempfile
import logging

from rich.console import Console
from rich.panel import Panel

from config import Config
from content_generator import ContentGenerator, VideoScript
from avatar_video import AvatarVideoGenerator
from linkedin_publisher import LinkedInPublisher


console = Console()
log = logging.getLogger(__name__)


def run_pipeline(cfg: Config, topic: str | None = None) -> dict:
    """
    Execute the full automation pipeline.

    Args:
        cfg:   Loaded Config object.
        topic: Optional explicit topic. If None, Claude picks one automatically.

    Returns:
        dict with keys: topic, post_urn, video_path
    """
    # ── 1. Generate script ────────────────────────────────────────────────────
    console.rule("[bold blue]Step 1 — Generating script")
    generator = ContentGenerator(cfg)

    if topic:
        console.print(f"[cyan]Using provided topic:[/cyan] {topic}")
        script: VideoScript = generator.generate_script(topic)
    else:
        console.print("[cyan]Brainstorming and picking best topic…[/cyan]")
        script = generator.pick_and_generate()

    console.print(Panel(
        f"[bold]Topic:[/bold] {script.topic}\n\n"
        f"[bold]Hook:[/bold] {script.hook}\n\n"
        f"[bold]CTA:[/bold] {script.cta}",
        title="Generated Script Preview",
        border_style="green",
    ))

    # ── 2. Render avatar video ────────────────────────────────────────────────
    console.rule("[bold blue]Step 2 — Rendering avatar video (HeyGen)")
    console.print("[cyan]Submitting render job… this takes 3–8 minutes.[/cyan]")

    with tempfile.TemporaryDirectory() as tmp_dir:
        video_gen = AvatarVideoGenerator(cfg)
        video_path: pathlib.Path = video_gen.generate(script, output_dir=tmp_dir)
        console.print(f"[green]Video rendered:[/green] {video_path.name} ({video_path.stat().st_size // 1024} KB)")

        # ── 3. Post to LinkedIn ───────────────────────────────────────────────
        console.rule("[bold blue]Step 3 — Publishing to LinkedIn")
        publisher = LinkedInPublisher(cfg)
        post_urn = publisher.publish(video_path, script)

    console.print(Panel(
        f"[bold green]Posted successfully![/bold green]\n"
        f"Post URN: {post_urn}\n"
        f"Topic: {script.topic}",
        title="Done",
        border_style="green",
    ))

    return {
        "topic": script.topic,
        "post_urn": post_urn,
        "video_path": str(video_path),
    }
