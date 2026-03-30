"""
Agent management endpoints — list, get, and test agents.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth import validate_api_key
from app.database import get_db
from app.models import APIKey, Organization, Agent
from app.agents.registry import AGENT_REGISTRY

router = APIRouter(prefix="/v1/agents", tags=["Agents"])


@router.get("", summary="List all available agents")
async def list_agents(
    auth: tuple[APIKey, Organization] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_db),
):
    """List all built-in and custom agents available to your organization."""
    # Built-in agents from registry
    builtin = [
        {
            "slug": a.slug,
            "name": a.name,
            "description": a.description,
            "category": a.category,
            "icon": a.icon,
            "capabilities": a.capabilities,
            "required_tools": a.required_tools,
            "preferred_llm": a.preferred_llm,
            "is_builtin": True,
        }
        for a in AGENT_REGISTRY.values()
    ]

    # Custom agents from DB
    _, org = auth
    result = await db.execute(
        select(Agent).where(Agent.is_active == True)
    )
    db_agents = result.scalars().all()
    custom = [
        {
            "slug": a.slug,
            "name": a.name,
            "description": a.description,
            "category": a.category,
            "icon": a.icon,
            "capabilities": a.capabilities,
            "required_tools": a.required_tools,
            "preferred_llm": a.preferred_llm,
            "is_builtin": False,
        }
        for a in db_agents
    ]

    return {"agents": builtin + custom, "total": len(builtin) + len(custom)}


@router.get("/{slug}", summary="Get agent details")
async def get_agent(
    slug: str,
    auth: tuple[APIKey, Organization] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Get details of a specific agent by slug."""
    if slug in AGENT_REGISTRY:
        a = AGENT_REGISTRY[slug]
        return {
            "slug": a.slug,
            "name": a.name,
            "description": a.description,
            "category": a.category,
            "icon": a.icon,
            "capabilities": a.capabilities,
            "required_tools": a.required_tools,
            "preferred_llm": a.preferred_llm,
            "system_prompt": a.system_prompt,
            "is_builtin": True,
        }

    result = await db.execute(select(Agent).where(Agent.slug == slug, Agent.is_active == True))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{slug}' not found.")

    return {
        "slug": agent.slug,
        "name": agent.name,
        "description": agent.description,
        "category": agent.category,
        "icon": agent.icon,
        "capabilities": agent.capabilities,
        "required_tools": agent.required_tools,
        "preferred_llm": agent.preferred_llm,
        "system_prompt": agent.system_prompt,
        "is_builtin": False,
    }
