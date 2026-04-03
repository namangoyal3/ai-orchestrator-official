import logging
from fastapi import APIRouter, Depends
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Literal, Optional
from app.database import get_db
from app.models import Skill, MCP, LLMModel
from app.llm_router import execute_llm, route_llm, LLMChoice, LLMProvider, ComplexityLevel
from app.api.stacks import STACK_CATALOG
from app.agents.registry import AGENT_REGISTRY
from app.tools.registry import TOOL_REGISTRY

logger = logging.getLogger(__name__)
router = APIRouter()


class ArchitectRequest(BaseModel):
    prompt: str
    optimization: Literal["cost", "quality"] = "quality"
    # Product context — collected by the CLI's clarifying questions
    product_type: Optional[str] = None      # e.g. "B2B SaaS", "B2C consumer app"
    scale: Optional[str] = None             # e.g. "MVP / prototype", "Scale-up"
    seo_required: Optional[bool] = None     # True = prefer Next.js SSR
    deployment_model: Optional[str] = None  # e.g. "Container / self-hosted"
    app_structure: Optional[str] = None     # e.g. "Single monolith", "Microservices"
    team_size: Optional[str] = None         # e.g. "Solo founder", "Small (2–5)"
    # api_key removed — was leaking into server logs via request body; use X-API-Key header


@router.post("/design")
async def design_architecture(request: ArchitectRequest, db: AsyncSession = Depends(get_db)):
    # 1. Fetch available tools from our marketplace scraping loops
    mcps_result = await db.execute(select(MCP))
    mcps = mcps_result.scalars().all()
    mcp_names = [m.name for m in mcps]

    # Fetch a subset of skills to avoid blowing up context window
    skills_result = await db.execute(select(Skill).limit(200)) # Adjust as needed
    skills = skills_result.scalars().all()
    skill_names = [s.name for s in skills]

    # Decide preferred LLMs based on cost vs quality
    if request.optimization == "cost":
        # Fetch mostly open source/cheap models
        llm_result = await db.execute(
            select(LLMModel)
            .where(LLMModel.cost_per_1m_input <= 0.5)
            .limit(50)
        )
        llms = llm_result.scalars().all()
    else:
        # Fetch powerful "quality" models (gpt-4, claude, etc.)
        llm_result = await db.execute(
            select(LLMModel)
            .where(LLMModel.cost_per_1m_input > 0.5)
            .limit(50)
        )
        llms = llm_result.scalars().all()
        
    llm_names = [model.id for model in llms]
    if not llm_names:
        llm_names = ["anthropic/claude-3-5-sonnet", "openai/gpt-4o", "meta-llama/llama-3-8b-instruct"]

    # 2. Build product context block from optional fields
    ctx_lines: list[str] = []
    if request.product_type:
        ctx_lines.append(f"- Product type: {request.product_type}")
    if request.scale:
        ctx_lines.append(f"- Expected scale: {request.scale}")
    if request.seo_required is not None:
        ctx_lines.append(f"- SEO / SSR required: {'Yes' if request.seo_required else 'No'}")
    if request.deployment_model:
        ctx_lines.append(f"- Deployment model: {request.deployment_model}")
    if request.app_structure:
        ctx_lines.append(f"- App structure: {request.app_structure}")
    if request.team_size:
        ctx_lines.append(f"- Team size: {request.team_size}")
    ctx_block = ""
    if ctx_lines:
        ctx_block = "PRODUCT CONTEXT (use this to guide all recommendations):\n" + "\n".join(ctx_lines) + "\n\n"

    # 3. Build stack catalog summary — OSS/free tools from the curated catalog
    stack_lines: list[str] = []
    for category, tools in STACK_CATALOG.items():
        for t in tools:
            tier = t.get("tier", "free")
            stack_lines.append(
                f"  [{category}] {t['name']}: {t.get('description','')[:70]} (tier={tier})"
            )
    stack_catalog_block = (
        "NAMANGO STACK CATALOG (OSS & free-tier tools — prefer these over proprietary options):\n"
        + "\n".join(stack_lines[:60])   # cap to avoid blowing context
        + "\n\n"
    )

    # 4. Built-in agents and tools from the marketplace
    builtin_agent_lines = [
        f"  [agent] {slug}: {getattr(meta, 'description', '')[:70]}"
        for slug, meta in list(AGENT_REGISTRY.items())[:12]
    ]
    builtin_tool_lines = [
        f"  [tool]  {slug}: {(meta.get('description') or '')[:70]}"
        for slug, meta in list(TOOL_REGISTRY.items())[:12]
    ]
    marketplace_block = (
        "NAMANGO BUILT-IN AGENTS (select relevant ones for recommended_agents):\n"
        + "\n".join(builtin_agent_lines)
        + "\n\nNAMANGO BUILT-IN TOOLS (select relevant ones for recommended_mcps):\n"
        + "\n".join(builtin_tool_lines)
        + "\n\n"
    )

    # 5. Architect LLM Logic — route to best available provider
    try:
        architect_choice = route_llm("reasoning", ComplexityLevel.HIGH)
    except RuntimeError:
        logger.warning("No LLM providers configured — returning architecture defaults")
        return {
            "framework": "LangChain (Python)",
            "recommended_stack": ["Next.js", "FastAPI", "PostgreSQL", "Supabase Auth", "Resend"],
            "recommended_agents": ["research", "code"],
            "recommended_mcps": ["web_search", "web_scrape"],
            "recommended_llm": "gpt-4o-mini" if request.optimization == "cost" else "claude-opus-4-6",
            "explanation": "Architecture defaults used — no LLM provider keys configured.",
            "error_fallback": True,
        }

    system_prompt = f"""You are the Namango Solutions Architect — a senior principal engineer and CTO-level technical advisor responsible for designing production-grade, cost-efficient application architectures.

Your decisions directly affect what gets built, how fast teams ship, and how much infrastructure costs. Every recommendation must be grounded in the specific product context provided — never give generic advice.

GUIDING PRINCIPLES:
1. Prefer OSS and free-tier tools unless the product context explicitly demands otherwise (high scale, compliance, enterprise features)
2. Choose the simplest stack that solves the problem — no over-engineering
3. Optimize for the team's size and skills — a solo founder needs different tools than a team of 10
4. Pick tools that compose well together — avoid impedance mismatches (e.g. Prisma + SQLite is fine for MVP, PostgreSQL for scale)
5. Every LLM recommendation must match the task complexity — use powerful models only where needed

ARCHITECTURE DECISION PROCESS:
1. Read the product context block carefully — every field matters
2. Identify the core technical constraints: scale, SEO, deployment model, team size
3. Select the minimal viable stack — one tool per job, no duplicates
4. Choose agents that add real value for this specific product (don't just list all agents)
5. Pick the LLM that balances cost vs capability for this workload
6. Write an explanation that ties every choice back to the product context

{ctx_block}{stack_catalog_block}{marketplace_block}COST OPTIMIZATION PRIORITY: {request.optimization.upper()}
- If "cost": Maximize free-tier and OSS. Avoid paid services unless no OSS alternative exists.
- If "quality": Prioritize reliability, developer experience, and scalability. Paid services acceptable.

Available Skills: {skill_names}
Available MCPs: {mcp_names}
Available LLMs: {llm_names}

OUTPUT: Respond with ONLY a valid JSON object. No markdown, no backticks, no explanation outside the JSON.

{{
  "framework": "LangChain (Python)" or "CrewAI (Python)",
  "recommended_stack": ["Exact tool names from STACK CATALOG — 5-8 tools that form a complete, coherent stack"],
  "recommended_agents": ["Agent slugs from BUILT-IN AGENTS — only include if genuinely relevant to this product"],
  "recommended_mcps": ["Tool slugs from BUILT-IN TOOLS or MCP market — only if the product needs them"],
  "recommended_llm": "One exact LLM ID — the best fit for this product's primary AI workload",
  "explanation": "3-4 sentences tying every choice to the specific product context. Mention scale, team size, deployment model, and one key trade-off you considered."
}}"""

    messages = [{"role": "user", "content": request.prompt}]

    try:
        response_text, _, _ = await execute_llm(architect_choice, messages, system_prompt, max_tokens=1024)

        # Strip markdown fences if model wraps JSON anyway
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        import json
        data = json.loads(response_text)
        return data

    except Exception as e:
        # Log the real error server-side; return safe defaults to client
        logger.exception("Architect LLM call failed for prompt=%r", request.prompt[:200])
        return {
            "framework": "LangChain (Python)",
            "recommended_stack": ["Next.js", "FastAPI", "PostgreSQL", "Supabase Auth", "Resend"],
            "recommended_agents": ["research", "code"],
            "recommended_mcps": ["web_search", "web_scrape"],
            "recommended_llm": "gpt-4o-mini" if request.optimization == "cost" else "claude-opus-4-6",
            "explanation": "Architecture defaults used — LLM unavailable at design time.",
            "error_fallback": True,
        }
