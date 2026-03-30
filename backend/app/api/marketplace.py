"""
Marketplace API — browse agents/tools and get AI-powered flow recommendations
for a product description.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth import validate_api_key
from app.agents.registry import AGENT_REGISTRY
from app.tools.registry import TOOL_REGISTRY
from app.llm_router import MODELS, route_llm, execute_llm, ComplexityLevel
import json as json_lib

router = APIRouter(prefix="/v1/marketplace", tags=["Marketplace"])


# ─── Response Models ──────────────────────────────────────────────────────────

class AgentCard(BaseModel):
    slug: str
    name: str
    description: str
    category: str
    icon: str
    capabilities: list[str]
    required_tools: list[str]
    preferred_llm: str
    is_builtin: bool


class ToolCard(BaseModel):
    slug: str
    name: str
    description: str
    category: str
    icon: str
    requires_auth: bool
    parameters: dict[str, str]
    is_builtin: bool


class LLMCard(BaseModel):
    id: str
    display_name: str
    provider: str
    description: str
    best_for: list[str]
    pricing: dict[str, float]


class RecommendedAgent(BaseModel):
    slug: str
    name: str
    icon: str
    reason: str
    role_in_flow: str


class RecommendedTool(BaseModel):
    slug: str
    name: str
    icon: str
    reason: str
    used_by_agent: str


class FlowStep(BaseModel):
    id: str
    label: str
    type: str          # input | llm | agent | tool | output
    component: str     # slug or label
    icon: str
    description: str
    connects_to: list[str]


class ActionPlanStep(BaseModel):
    step: int
    title: str
    description: str
    agents: list[str]
    tools: list[str]
    llm: str
    expected_output: str


class FlowRecommendation(BaseModel):
    product_summary: str
    recommended_llm: str
    llm_reason: str
    recommended_agents: list[RecommendedAgent]
    recommended_tools: list[RecommendedTool]
    flow_steps: list[FlowStep]
    action_plan: list[ActionPlanStep]
    api_snippet: str


# ─── Endpoints ────────────────────────────────────────────────────────────────

from app.database import get_db
from app.models import Skill, MCP
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

@router.get("/agents", response_model=dict)
async def list_marketplace_agents(db: AsyncSession = Depends(get_db), api_key=Depends(validate_api_key)):
    """All agents available in the marketplace, grouped by category."""
    agents = []
    
    # 1. Add Dynamic Skills from Postgres as Agents
    results = await db.execute(select(Skill).limit(100))
    skills = results.scalars().all()
    for s in skills:
        agents.append(AgentCard(
            slug=s.id,
            name=s.name,
            description=s.description or "",
            category=s.category or "Community",
            icon="🧠",
            capabilities=[s.description or ""],
            required_tools=[],
            preferred_llm="openai/gpt-4o",
            is_builtin=False,
        ))

    # 2. Add Built-in Registry Agents
    for slug, a in AGENT_REGISTRY.items():
        agents.append(AgentCard(
            slug=a.slug,
            name=a.name,
            description=a.description,
            category=a.category,
            icon=a.icon,
            capabilities=a.capabilities,
            required_tools=a.required_tools,
            preferred_llm=a.preferred_llm,
            is_builtin=a.is_builtin,
        ))

    categories = list(dict.fromkeys(a.category for a in agents))
    return {"agents": [a.model_dump() for a in agents], "total": len(agents), "categories": categories}


@router.get("/tools", response_model=dict)
async def list_marketplace_tools(db: AsyncSession = Depends(get_db), api_key=Depends(validate_api_key)):
    """All tools available in the marketplace, grouped by category."""
    tools = []
    
    # 1. Add Dynamic MCPs/Tools from Postgres
    results = await db.execute(select(MCP).limit(100))
    mcps = results.scalars().all()
    for m in mcps:
        tools.append(ToolCard(
            slug=m.slug,
            name=m.name,
            description=m.description or "",
            category=m.source or "Community",
            icon="🛠️",
            requires_auth=True,
            parameters={"api_key": "Your API Key for this service"},
            is_builtin=False,
        ))

    # 2. Add Built-in Registry Tools
    for slug, t in TOOL_REGISTRY.items():
        tools.append(ToolCard(
            slug=t["slug"],
            name=t["name"],
            description=t["description"],
            category=t["category"],
            icon=t["icon"],
            requires_auth=t["requires_auth"],
            parameters=t["parameters"],
            is_builtin=t["is_builtin"],
        ))

    categories = list(dict.fromkeys(t.category for t in tools))
    return {"tools": [t.model_dump() for t in tools], "total": len(tools), "categories": categories}

@router.get("/tools/{slug}", response_model=ToolCard)
async def get_tool_details(slug: str, db: AsyncSession = Depends(get_db), api_key=Depends(validate_api_key)):
    """Fetch detailed metadata for a specific tool (used for CLI 'add' command)."""
    # Check Built-in
    if slug in TOOL_REGISTRY:
        t = TOOL_REGISTRY[slug]
        return ToolCard(
            slug=t["slug"], name=t["name"], description=t["description"],
            category=t["category"], icon=t["icon"], requires_auth=t["requires_auth"],
            parameters=t["parameters"], is_builtin=t["is_builtin"]
        )
    
    # Check DB
    result = await db.execute(select(MCP).where(MCP.slug == slug))
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Tool not found")
        
    return ToolCard(
        slug=m.slug, name=m.name, description=m.description or "",
        category=m.source or "Community", icon="🛠️", requires_auth=True,
        parameters={"api_key": "API Key"}, is_builtin=False
    )


@router.get("/llms", response_model=dict)
async def list_marketplace_llms(api_key=Depends(validate_api_key)):
    """All LLMs available for routing."""
    best_for_map = {
        "claude-opus-4-6": ["Complex reasoning", "Architecture design", "Strategy", "Long-form writing"],
        "claude-sonnet-4-6": ["Research", "Analysis", "Code review", "Balanced tasks"],
        "claude-haiku-4-5": ["Fast responses", "Simple Q&A", "Classification", "High volume"],
        "gpt-4o": ["Multimodal tasks", "Code generation", "Broad knowledge"],
        "gpt-4o-mini": ["High volume", "Fast inference", "Cost-efficient tasks"],
        "gemini-2.0-flash": ["Long context", "Document analysis", "Multimodal"],
    }
    llm_cards = []
    for model_id, choice in MODELS.items():
        llm_cards.append(LLMCard(
            id=choice.model_id,
            display_name=choice.display_name,
            provider=choice.provider.value,
            description=choice.reason,
            best_for=best_for_map.get(model_id, ["General tasks"]),
            pricing={
                "input_per_1m": choice.cost_per_1m_input,
                "output_per_1m": choice.cost_per_1m_output,
            },
        ))
    return {"llms": [l.model_dump() for l in llm_cards], "total": len(llm_cards)}


class RepoCard(BaseModel):
    name: str
    full_name: str
    description: str
    stars: int
    forks: int
    url: str
    language: str
    topics: list[str]

@router.get("/repos", response_model=dict)
async def list_marketplace_repos(api_key=Depends(validate_api_key)):
    """Fetch top open-source AI repositories from GitHub."""
    import httpx
    try:
        headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "AIGateway/1.0"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.github.com/search/repositories",
                params={"q": "topic:ai OR topic:llm OR topic:machine-learning", "sort": "stars", "order": "desc", "per_page": 20},
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            
            repos = []
            for item in data.get("items", []):
                repos.append(RepoCard(
                    name=item.get("name", ""),
                    full_name=item.get("full_name", ""),
                    description=item.get("description") or "",
                    stars=item.get("stargazers_count", 0),
                    forks=item.get("forks_count", 0),
                    url=item.get("html_url", ""),
                    language=item.get("language") or "Mixed",
                    topics=item.get("topics", [])[:3]
                ))
            
            return {"repos": [r.model_dump() for r in repos], "total": len(repos)}
    except Exception as e:
        # Fallback curated list if GitHub API fails or rate limits
        fallback = [
            RepoCard(name="transformers", full_name="huggingface/transformers", description="State-of-the-art Machine Learning for Pytorch, TensorFlow, and JAX.", stars=120000, forks=24000, url="https://github.com/huggingface/transformers", language="Python", topics=["machine-learning", "nlp", "llm"]),
            RepoCard(name="langchain", full_name="langchain-ai/langchain", description="Build context-aware reasoning applications", stars=80000, forks=12000, url="https://github.com/langchain-ai/langchain", language="Python", topics=["llm", "ai", "agents"]),
            RepoCard(name="llama.cpp", full_name="ggerganov/llama.cpp", description="Port of Facebook's LLaMA model in C/C++", stars=55000, forks=8000, url="https://github.com/ggerganov/llama.cpp", language="C++", topics=["llm", "inference", "cpp"]),
        ]
        return {"repos": [r.model_dump() for r in fallback], "total": len(fallback)}


class RecommendRequest(BaseModel):
    product_description: str = Field(..., min_length=10, max_length=5000)
    use_cases: Optional[list[str]] = Field(default_factory=list)


@router.post("/recommend", response_model=FlowRecommendation)
async def recommend_flow(body: RecommendRequest, api_key=Depends(validate_api_key)):
    """
    Given a product description, use Claude to recommend the optimal
    combination of agents, tools, and LLMs, and generate a visual action plan.
    """
    agents_list = "\n".join(
        f"- {a.slug} ({a.name}): {a.description} | capabilities: {', '.join(a.capabilities)}"
        for a in AGENT_REGISTRY.values()
    )
    tools_list = "\n".join(
        f"- {t['slug']} ({t['name']}): {t['description']}"
        for t in TOOL_REGISTRY.values()
    )
    llms_list = "\n".join(
        f"- {choice.model_id}: {choice.display_name} by {choice.provider.value}"
        for choice in MODELS.values()
    )

    prompt = f"""You are an AI orchestration architect. A user has described their product and wants to know the optimal combination of AI agents, tools, and LLMs to power it.

PRODUCT DESCRIPTION:
{body.product_description}

USE CASES:
{chr(10).join(f"- {uc}" for uc in body.use_cases) if body.use_cases else "Not specified"}

AVAILABLE AGENTS:
{agents_list}

AVAILABLE TOOLS:
{tools_list}

AVAILABLE LLMs:
{llms_list}

Respond ONLY with valid JSON in this exact schema (no markdown, no explanation):
{{
  "product_summary": "one sentence summary of what the product does",
  "recommended_llm": "model_id from the available LLMs list",
  "llm_reason": "why this LLM is best for this product",
  "recommended_agents": [
    {{
      "slug": "agent_slug",
      "name": "Agent Name",
      "icon": "emoji",
      "reason": "why this agent is needed",
      "role_in_flow": "what this agent does specifically for this product"
    }}
  ],
  "recommended_tools": [
    {{
      "slug": "tool_slug",
      "name": "Tool Name",
      "icon": "emoji",
      "reason": "why this tool is needed",
      "used_by_agent": "which agent primarily uses this tool"
    }}
  ],
  "flow_steps": [
    {{
      "id": "step_id",
      "label": "Step Label",
      "type": "input|llm|agent|tool|output",
      "component": "slug or label",
      "icon": "emoji",
      "description": "what happens at this step",
      "connects_to": ["next_step_id"]
    }}
  ],
  "action_plan": [
    {{
      "step": 1,
      "title": "Phase title",
      "description": "what to implement in this phase",
      "agents": ["agent_slugs"],
      "tools": ["tool_slugs"],
      "llm": "model_id",
      "expected_output": "what this phase produces"
    }}
  ],
  "api_snippet": "curl -X POST https://your-gateway.com/v1/query -H 'X-API-Key: YOUR_KEY' -d '{{...}}'"
}}

Select 2-4 agents and 3-6 tools that are most relevant. Create 4-7 flow steps showing the data pipeline. Create 3-5 action plan phases. Make the api_snippet a realistic example for this specific product."""

    try:
        # Route to optimal LLM (fallback to Bedrock Haiku if direct Anthropic key missing)
        llm_choice = route_llm("marketplace_recommendation", ComplexityLevel.MEDIUM, "claude-haiku-4-5")
        
        raw, _, _ = await execute_llm(
            llm_choice,
            messages=[{"role": "user", "content": prompt}],
            system="You are an AI orchestration architect. Output only valid JSON.",
            max_tokens=4096,
        )
        # Strip any accidental markdown fences
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        data = json_lib.loads(raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation generation failed: {e}")

    # Enrich with icons from registry if missing
    for agent in data.get("recommended_agents", []):
        if agent["slug"] in AGENT_REGISTRY and not agent.get("icon"):
            agent["icon"] = AGENT_REGISTRY[agent["slug"]].icon

    for tool in data.get("recommended_tools", []):
        if tool["slug"] in TOOL_REGISTRY and not tool.get("icon"):
            tool["icon"] = TOOL_REGISTRY[tool["slug"]]["icon"]

    # Build API snippet if not provided
    if not data.get("api_snippet"):
        agent_slugs = [a["slug"] for a in data.get("recommended_agents", [])][:2]
        tool_slugs = [t["slug"] for t in data.get("recommended_tools", [])][:3]
        data["api_snippet"] = (
            f'curl -X POST https://your-gateway.com/v1/query \\\n'
            f'  -H "X-API-Key: YOUR_KEY" \\\n'
            f'  -H "Content-Type: application/json" \\\n'
            f'  -d \'{{"prompt": "Your task here", '
            f'"preferred_agents": {json_lib.dumps(agent_slugs)}, '
            f'"preferred_tools": {json_lib.dumps(tool_slugs)}}}\''
        )

    return FlowRecommendation(**data)
