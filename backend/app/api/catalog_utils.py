"""
Shared catalog utilities — used by activate.py and mcp_server.py.

Centralizes _find_tool, _flatten_catalog, and _relevance_score
so changes only need to happen in one place.
"""
import re
from typing import Optional

from app.api.stacks import STACK_CATALOG


def find_tool(slug: str) -> Optional[dict]:
    """Find a tool by slug (case-insensitive). Returns tool dict with category injected."""
    slug = slug.lower().strip()
    for cat, tools in STACK_CATALOG.items():
        for t in tools:
            if t.get("slug", "").lower() == slug:
                return {**t, "category": cat}
    return None


def flatten_catalog(catalog: dict) -> list[dict]:
    """Flatten category → [tools] dict into a single list with category field."""
    result = []
    for cat, tools in catalog.items():
        for t in tools:
            result.append({**t, "category": t.get("category") or cat})
    return result


def relevance_score(tool: dict, prompt_words: set) -> int:
    """Score a tool by keyword overlap between prompt words and tool metadata."""
    text = (
        (tool.get("description") or "") + " " +
        (tool.get("category") or "") + " " +
        " ".join(tool.get("use_case_tags", []))
    ).lower()
    return sum(1 for w in prompt_words if w in text)


def prompt_to_words(prompt: str) -> set:
    """Normalize a user prompt into a set of lowercase words for matching."""
    return set(re.sub(r"[^a-z0-9 ]", "", prompt.lower()).split())
