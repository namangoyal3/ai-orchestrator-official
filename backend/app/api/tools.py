"""
Tool management endpoints — list, get, and execute tools directly.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any

from app.auth import validate_api_key
from app.models import APIKey, Organization
from app.tools.registry import TOOL_REGISTRY, execute_tool

router = APIRouter(prefix="/v1/tools", tags=["Tools"])


class ToolExecuteRequest(BaseModel):
    params: dict[str, Any] = {}


@router.get("", summary="List all available tools")
async def list_tools():
    """List all pre-built tool integrations available in the gateway."""
    tools = [
        {
            "slug": slug,
            "name": t["name"],
            "description": t["description"],
            "category": t["category"],
            "icon": t["icon"],
            "is_builtin": t["is_builtin"],
            "requires_auth": t["requires_auth"],
            "parameters": t["parameters"],
        }
        for slug, t in TOOL_REGISTRY.items()
    ]
    categories = list({t["category"] for t in TOOL_REGISTRY.values()})
    return {"tools": tools, "total": len(tools), "categories": sorted(categories)}


@router.get("/{slug}", summary="Get tool details")
async def get_tool(slug: str):
    """Get details and parameter schema for a specific tool."""
    if slug not in TOOL_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Tool '{slug}' not found.")

    t = TOOL_REGISTRY[slug]
    return {
        "slug": slug,
        "name": t["name"],
        "description": t["description"],
        "category": t["category"],
        "icon": t["icon"],
        "is_builtin": t["is_builtin"],
        "requires_auth": t["requires_auth"],
        "parameters": t["parameters"],
    }


@router.post("/{slug}/execute", summary="Execute a tool directly")
async def execute(
    slug: str,
    request: ToolExecuteRequest,
    auth: tuple[APIKey, Organization] = Depends(validate_api_key),
):
    """
    Execute a specific tool directly with your own parameters.
    Useful for testing or when you know exactly which tool you need.
    """
    if slug not in TOOL_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Tool '{slug}' not found.")

    result = await execute_tool(slug, request.params)
    return {
        "tool": slug,
        "success": result.success,
        "output": result.output,
        "error": result.error,
    }
