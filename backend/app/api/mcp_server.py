"""
Namango MCP Server — exposes stack intelligence as an MCP-compatible endpoint.

Any MCP client (Claude Code, Cursor, Windsurf, Cline) can connect to this server
and call Namango's stack recommender inline while building.

Protocol: JSON-RPC 2.0 over HTTP POST /mcp
Spec: https://modelcontextprotocol.io/specification

Tools exposed:
  - recommend_stack   → LLM-ranked stack for a product idea
  - get_catalog       → full tool catalog by category
  - explain_tool      → why a specific tool fits a product

Discovery: GET /.well-known/mcp.json
"""
import logging
import os
from typing import Any, Optional

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.api.stacks import STACK_CATALOG
from app.api.catalog_utils import find_tool, flatten_catalog, relevance_score, prompt_to_words

logger = logging.getLogger(__name__)

router = APIRouter(tags=["MCP"])

# ── Tool schemas (MCP inputSchema format) ────────────────────────────────────

TOOLS = [
    {
        "name": "recommend_stack",
        "description": (
            "Get an opinionated tech stack recommendation for a product idea. "
            "Returns 6-10 curated tools covering frontend, backend, database, auth, "
            "notifications, and any product-specific layers (AI, automation, no-code, etc.). "
            "Each tool includes a product-specific reason for the recommendation."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Describe the product to build, e.g. 'no-code workflow automation builder with drag-and-drop UI'",
                },
                "context": {
                    "type": "object",
                    "description": "Optional product context",
                    "properties": {
                        "scale": {"type": "string", "description": "Expected scale, e.g. 'MVP', '10k users', 'enterprise'"},
                        "team_size": {"type": "string", "description": "e.g. 'solo', 'small team', '10+ engineers'"},
                        "deployment": {"type": "string", "description": "e.g. 'cloud', 'self-hosted', 'edge'"},
                        "seo": {"type": "boolean", "description": "Whether SEO/SSR is required"},
                    },
                },
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "get_catalog",
        "description": (
            "List all tools in the Namango catalog, grouped by category. "
            "Returns 73 curated open-source and freemium tools across 15 categories "
            "including automation, no-code builders, AI frameworks, MCP servers, and more."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Filter to a specific category (e.g. 'automation', 'database', 'ai'). Omit for all.",
                },
            },
        },
    },
    {
        "name": "explain_tool",
        "description": (
            "Explain why a specific tool from the catalog is or isn't a good fit for a product. "
            "Returns the tool's strengths, weaknesses, and when to use vs avoid it."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "tool_slug": {
                    "type": "string",
                    "description": "The tool slug, e.g. 'n8n', 'supabase', 'nextjs'",
                },
                "product_context": {
                    "type": "string",
                    "description": "What you're building, so the explanation is product-specific",
                },
            },
            "required": ["tool_slug"],
        },
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _catalog_result(category: Optional[str]) -> dict:
    if category:
        tools = STACK_CATALOG.get(category, [])
        return {
            "category": category,
            "count": len(tools),
            "tools": tools,
        }
    summary = {}
    for cat, tools in STACK_CATALOG.items():
        summary[cat] = [
            {"slug": t.get("slug"), "name": t.get("name"), "tier": t.get("tier"), "description": t.get("description", "")[:80]}
            for t in tools
        ]
    total = sum(len(v) for v in STACK_CATALOG.values())
    return {"total_tools": total, "categories": list(STACK_CATALOG.keys()), "catalog": summary}


def _openrouter_key() -> str:
    """Read OpenRouter API key from env — never hardcode credentials."""
    from app.config import settings
    key = settings.openrouter_api_key or os.getenv("OPENROUTER_API_KEY", "")
    return key


async def _recommend_stack(prompt: str, context: Optional[dict]) -> dict:
    """Rank and select a tech stack for the given product prompt."""
    all_tools = flatten_catalog(STACK_CATALOG)

    # Relevance pre-ranking via shared utility
    prompt_words = prompt_to_words(prompt)
    sorted_tools = sorted(all_tools, key=lambda t: relevance_score(t, prompt_words), reverse=True)

    # Build prompt lines with relevance labels
    lines = []
    for t in sorted_tools:
        score = relevance_score(t, prompt_words)
        label = f" [relevance:{score}]" if score > 0 else ""
        oss = " [OSS]" if t.get("tier") == "free" else ""
        lines.append(f"[{t.get('category','?')}] {t.get('name','?')}: {(t.get('description') or '')[:65]} (tier={t.get('tier','free')}{oss}){label}")

    ctx_lines = ""
    if context:
        ctx_lines = (
            f"- Scale: {context.get('scale', 'not specified')}\n"
            f"- Team size: {context.get('team_size', 'not specified')}\n"
            f"- Deployment: {context.get('deployment', 'not specified')}\n"
            f"- SEO required: {context.get('seo', 'not specified')}\n"
        )

    catalog_block = "\n".join(lines)
    context_block = ("CONTEXT:\n" + ctx_lines) if ctx_lines else ""
    selection_prompt = (
        f"You are the Namango Stack Selector. Pick the minimal, coherent stack for this product.\n\n"
        f"PRODUCT: {prompt}\n\n"
        f"{context_block}"
        f"CATALOG (sorted by relevance to this product):\n"
        f"{catalog_block}"
        "\n\nSelect 6-10 tools. Tools labeled [relevance:N] scored highest — prioritize these.\n"
        "For each tool output exactly: TOOL: <name> | CATEGORY: <cat> | TIER: <tier> | REASON: <one sentence specific to this product>"
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {_openrouter_key()}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "meta-llama/llama-3.3-70b-instruct:free",
                    "messages": [{"role": "user", "content": selection_prompt}],
                    "temperature": 0.3,
                    "max_tokens": 800,
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error("MCP recommend_stack LLM call failed: %s", e)
        # Fallback: return top-scored tools without LLM reasoning
        top = sorted_tools[:8]
        return {
            "prompt": prompt,
            "stack": [
                {"name": t.get("name"), "category": t.get("category"), "tier": t.get("tier"), "reason": t.get("description", "")}
                for t in top
            ],
            "note": "LLM unavailable — returned top relevance-scored tools",
        }

    # Parse TOOL: lines
    stack = []
    for line in content.splitlines():
        if not line.startswith("TOOL:"):
            continue
        parts = {p.split(":", 1)[0].strip(): p.split(":", 1)[1].strip() for p in line.split("|") if ":" in p}
        stack.append({
            "name": parts.get("TOOL", ""),
            "category": parts.get("CATEGORY", ""),
            "tier": parts.get("TIER", "free"),
            "reason": parts.get("REASON", ""),
        })

    return {"prompt": prompt, "stack": stack}


async def _explain_tool(slug: str, product_context: Optional[str]) -> dict:
    tool = find_tool(slug)
    if not tool:
        return {"error": f"Tool '{slug}' not found in catalog. Use get_catalog to see available tools."}

    ctx = f" for: {product_context}" if product_context else ""
    prompt = (
        f"Explain why a developer would or wouldn't use {tool['name']} ({tool['description']}){ctx}.\n"
        f"Cover: strengths, weaknesses, when to use it, when to avoid it. Be concise (4-6 sentences)."
    )
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {_openrouter_key()}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "meta-llama/llama-3.3-70b-instruct:free",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.4,
                    "max_tokens": 300,
                },
            )
            resp.raise_for_status()
            explanation = resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error("MCP explain_tool LLM call failed: %s", e)
        explanation = tool.get("description", "")

    return {
        "tool": tool.get("name"),
        "slug": tool.get("slug"),
        "category": tool.get("category"),
        "tier": tool.get("tier"),
        "explanation": explanation,
    }


# ── MCP JSON-RPC handler ──────────────────────────────────────────────────────

@router.post("/mcp")
async def mcp_handler(request: Request):
    """
    MCP-compatible JSON-RPC 2.0 endpoint.
    Supports: initialize, tools/list, tools/call
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}})

    rpc_id = body.get("id")
    method = body.get("method", "")
    params = body.get("params", {})

    # ── initialize ────────────────────────────────────────────────────────────
    if method == "initialize":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "namango",
                    "version": "1.0.0",
                    "description": "AI stack intelligence — recommends the right tech stack for any product idea",
                },
            },
        })

    # ── tools/list ────────────────────────────────────────────────────────────
    if method == "tools/list":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {"tools": TOOLS},
        })

    # ── tools/call ────────────────────────────────────────────────────────────
    if method == "tools/call":
        tool_name: str = params.get("name", "")
        args: dict[str, Any] = params.get("arguments", {})

        try:
            if tool_name == "recommend_stack":
                prompt = args.get("prompt", "")
                if not prompt:
                    raise ValueError("'prompt' is required")
                result = await _recommend_stack(prompt, args.get("context"))

            elif tool_name == "get_catalog":
                result = _catalog_result(args.get("category"))

            elif tool_name == "explain_tool":
                slug = args.get("tool_slug", "")
                if not slug:
                    raise ValueError("'tool_slug' is required")
                result = await _explain_tool(slug, args.get("product_context"))

            else:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
                })

        except ValueError as e:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {"code": -32602, "message": str(e)},
            })
        except Exception as e:
            logger.error("MCP tools/call error for %s: %s", tool_name, e)
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {"code": -32603, "message": "Internal error"},
            })

        import json
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
                "isError": False,
            },
        })

    # ── unknown method ────────────────────────────────────────────────────────
    return JSONResponse({
        "jsonrpc": "2.0",
        "id": rpc_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    })


# ── MCP Discovery manifest ────────────────────────────────────────────────────

@router.get("/.well-known/mcp.json")
async def mcp_manifest():
    """MCP discovery endpoint — clients use this to auto-configure the server."""
    return {
        "schema_version": "v1",
        "name": "namango",
        "display_name": "Namango Stack Intelligence",
        "description": "Get opinionated tech stack recommendations for any product idea. 73 curated tools across 15 categories, ranked by relevance to your specific product.",
        "version": "1.0.0",
        "url": "https://ai-gateway-backend-production.up.railway.app/mcp",
        "tools": [
            {"name": t["name"], "description": t["description"]}
            for t in TOOLS
        ],
        "categories": list(STACK_CATALOG.keys()),
        "total_tools": sum(len(v) for v in STACK_CATALOG.values()),
        "links": {
            "homepage": "https://namango.dev",
            "docs": "https://ai-gateway-backend-production.up.railway.app/docs",
        },
    }
