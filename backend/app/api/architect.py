from fastapi import APIRouter, Depends
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models import Skill, MCP, LLMModel
from app.llm_router import execute_llm, LLMChoice, LLMProvider, ComplexityLevel

router = APIRouter()

class ArchitectRequest(BaseModel):
    prompt: str
    optimization: str  # "cost" or "quality"
    api_key: Optional[str] = None

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

    # 2. Architect LLM Logic
    # We use a solid baseline model conceptually to do this routing
    # But since execute_llm routes dynamically we can just use anthropic or openrouter
    
    architect_choice = LLMChoice(
        provider=LLMProvider.OPENROUTER,
        model_id="anthropic/claude-3-5-sonnet", # Claude 3.5 Sonnet is amazing at JSON architecture
        display_name="Solutions Architect Model",
        reason="Architect",
        cost_per_1m_input=0,
        cost_per_1m_output=0
    )

    system_prompt = f"""You are the Namango Solutions Architect AI. 
The user wants to build an application. You MUST design the architecture selecting from the provided lists of available marketplace tools.
Your ONLY output should be a strict JSON object (Do not wrap in markdown or backticks):
{{
  "framework": "LangChain (Python)" or "CrewAI (Python)",
  "recommended_agents": ["List of agent/skill strings selected from marketplace"],
  "recommended_mcps": ["List of exact MCP strings selected from marketplace"],
  "recommended_llm": "Select ONE exact LLM ID string from the marketplace",
  "explanation": "A 1-2 sentence pitch of why you chose these."
}}
Cost Optimization Priority: {request.optimization.upper()}

Available Skills Market: {skill_names}
Available MCP Market: {mcp_names}
Available LLMs: {llm_names}
"""

    messages = [{"role": "user", "content": request.prompt}]

    try:
        response_text, _, _ = await execute_llm(architect_choice, messages, system_prompt, max_tokens=1024)
        
        # Strip standard markdown from response
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        import json
        data = json.loads(response_text)
        return data
        
    except Exception as e:
        # Fallback payload in case OpenRouter fails
        return {
            "framework": "LangChain (Python)",
            "recommended_agents": ["Fallback Agent Analyzer"],
            "recommended_mcps": ["GitHub Repository MCP"],
            "recommended_llm": "meta-llama/llama-3-8b-instruct" if request.optimization == "cost" else "openai/gpt-4o",
            "explanation": f"Failed to dynamically architect due to API error: {e}. Provided safe sandbox defaults.",
            "error_fallback": True
        }
