"""
Core Orchestrator Engine

Flow:
1. Parse incoming request (prompt + optional context URL/doc)
2. Extract context from URL/document if provided
3. Use Claude Haiku to analyze intent: task category, complexity, needed tools/agents
4. Select appropriate LLM, agents, and tools
5. Execute pipeline (tool calls → agent prompts → final synthesis)
6. Return unified structured response
"""
import asyncio
import json
import time
from dataclasses import dataclass
from typing import Any, Optional

import anthropic

from app.config import settings
from app.llm_router import (
    LLMChoice, ComplexityLevel, MODELS,
    route_llm, execute_llm, estimate_cost,
)
from app.agents.registry import AGENT_REGISTRY, get_agents_for_task
from app.tools.registry import TOOL_REGISTRY, execute_tool


# ─────────────────────────────────────────────
# Request / Response schemas
# ─────────────────────────────────────────────

@dataclass
class OrchestratorRequest:
    prompt: str
    context_url: Optional[str] = None
    context_text: Optional[str] = None
    preferred_model: Optional[str] = None
    preferred_agents: Optional[list[str]] = None
    preferred_tools: Optional[list[str]] = None
    max_tokens: int = 8096
    stream: bool = False


@dataclass
class OrchestratorResponse:
    response: str
    task_category: str
    complexity: str
    selected_llm: str
    selected_agents: list[str]
    selected_tools: list[str]
    tools_executed: list[dict]
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    context_extracted: bool
    error: Optional[str] = None
    routing_reason: str = ""


# ─────────────────────────────────────────────
# Intent Analyzer (uses Claude Haiku for speed + cost)
# ─────────────────────────────────────────────

INTENT_ANALYSIS_SYSTEM = """You are an AI task analyzer. Given a user prompt (and optional context),
return a JSON object describing the task. Never include markdown fences in your response.

Return ONLY valid JSON with exactly these fields:
{
  "task_category": "<one of: coding, analysis, research, writing, summarization, document_qa, extraction, classification, translation, simple_qa, customer_support, data_analysis, image_analysis, planning, reasoning, general>",
  "complexity": "<one of: low, medium, high>",
  "needed_capabilities": ["list of strings describing what capabilities are needed"],
  "suggested_tools": ["list of tool slugs from: web_scrape, web_search, http_request, parse_pdf, parse_docx, json_query, calculator, github_repo_info, sql_query, extract_entities, summarize_text, translate, weather, news_search, send_slack"],
  "reasoning": "brief explanation of your analysis"
}

Complexity guide:
- low: simple lookup, classification, single-step task
- medium: multi-step, content generation, summarization
- high: deep reasoning, complex code, multi-source research, data modeling"""


async def analyze_intent(prompt: str, context_snippet: str = "") -> dict:
    """Use preferred model (e.g. Haiku) to rapidly analyze the task."""
    try:
        # We use Haiku for intent analysis (fast & cheap)
        # route_llm will fallback to Bedrock if Anthropic key is missing
        llm_choice = route_llm("intent_analysis", ComplexityLevel.LOW, "claude-haiku-4-5")
        
        content = prompt
        if context_snippet:
            content += f"\n\n[Context snippet]:\n{context_snippet[:2000]}"

        messages = [{"role": "user", "content": content}]
        text, _, _ = await execute_llm(
            llm_choice, 
            messages, 
            system=INTENT_ANALYSIS_SYSTEM, 
            max_tokens=512
        )

        # Parse JSON response
        return json.loads(text)

    except json.JSONDecodeError:
        # Fallback to defaults
        return {
            "task_category": "general",
            "complexity": "medium",
            "needed_capabilities": ["reasoning", "text_generation"],
            "suggested_tools": [],
            "reasoning": "Could not analyze intent, using defaults",
        }
    except Exception:
        return {
            "task_category": "general",
            "complexity": "medium",
            "needed_capabilities": [],
            "suggested_tools": [],
            "reasoning": "Analysis failed, using defaults",
        }


# ─────────────────────────────────────────────
# Context Extractor
# ─────────────────────────────────────────────

async def extract_context(url: Optional[str] = None, text: Optional[str] = None) -> tuple[str, str]:
    """
    Extract context from URL or raw text.
    Returns (context_text, context_type)
    """
    if url:
        result = await execute_tool("web_scrape", {"url": url, "extract": "text"})
        if result.success:
            return result.output, "url"
        return f"[Failed to extract URL content: {result.error}]", "url_failed"

    if text:
        return text[:20000], "text"

    return "", "none"


# ─────────────────────────────────────────────
# Pipeline Builder
# ─────────────────────────────────────────────

def build_agent_system_prompt(agent_slugs: list[str], context: str) -> str:
    """Compose a system prompt from selected agents' prompts."""
    if not agent_slugs:
        return "You are a helpful AI assistant."

    parts = []
    for slug in agent_slugs:
        if slug in AGENT_REGISTRY:
            agent = AGENT_REGISTRY[slug]
            parts.append(f"## Role: {agent.name}\n{agent.system_prompt}")

    system = "\n\n---\n\n".join(parts)

    if context:
        system += f"\n\n---\n\n## Context Provided\nUse the following extracted content to answer the user's question:\n\n{context[:8000]}"

    return system


async def execute_tool_pipeline(
    tool_slugs: list[str],
    prompt: str,
    context: str,
) -> list[dict]:
    """
    Execute relevant tools in parallel and collect results.
    Intelligently determines tool parameters from the prompt.
    """
    results = []

    async def run_tool(slug: str) -> dict:
        params = {}

        # Auto-infer parameters from context
        if slug == "web_search":
            params = {"query": prompt[:200], "num_results": 3}
        elif slug == "extract_entities":
            params = {"text": context or prompt}
        elif slug == "summarize_text":
            params = {"text": context or prompt}
        elif slug == "calculator":
            # Try to extract expression from prompt
            import re
            nums = re.findall(r'[\d\s\+\-\*\/\(\)\.]+', prompt)
            params = {"expression": nums[0].strip() if nums else "1+1"}
        elif slug == "weather":
            # Extract location from prompt (simple heuristic)
            params = {"location": "New York"}  # Default; production: NER
        else:
            # Skip tools that need explicit params not inferable from prompt
            return {}

        result = await execute_tool(slug, params)
        return {
            "tool": slug,
            "success": result.success,
            "output": result.output if result.success else result.error,
        }

    # Run all tools concurrently
    tasks = [run_tool(slug) for slug in tool_slugs[:5]]  # max 5 tools
    tool_results = await asyncio.gather(*tasks, return_exceptions=True)

    for r in tool_results:
        if isinstance(r, dict) and r:
            results.append(r)

    return results


def format_tool_results(tool_results: list[dict]) -> str:
    """Format tool execution results for injection into LLM context."""
    if not tool_results:
        return ""

    parts = ["\n\n## Tool Results\n"]
    for result in tool_results:
        if result.get("success"):
            output = result["output"]
            if isinstance(output, (dict, list)):
                output = json.dumps(output, indent=2)[:2000]
            else:
                output = str(output)[:2000]
            parts.append(f"**{result['tool']}**:\n{output}\n")

    return "\n".join(parts)


# ─────────────────────────────────────────────
# Main Orchestrator
# ─────────────────────────────────────────────

from typing import Callable, Awaitable

# Step event type for streaming pipeline visibility
StepCallback = Callable[[dict], Awaitable[None]]


async def _noop_callback(event: dict) -> None:
    pass


async def orchestrate(
    req: OrchestratorRequest,
    step_callback: StepCallback = _noop_callback,
) -> OrchestratorResponse:
    """
    Main orchestration pipeline.

    step_callback receives real-time step events:
      {"type": "step_start",    "step": str, "label": str}
      {"type": "step_complete", "step": str, "label": str, "details": dict}
    """
    start_time = time.time()
    tools_executed: list[dict] = []
    context_extracted = False
    context_text = ""

    # 1. Extract context from URL/document
    if req.context_url or req.context_text:
        await step_callback({"type": "step_start", "step": "context", "label": "Extracting context"})
        context_text, _ = await extract_context(req.context_url, req.context_text)
        context_extracted = bool(context_text) and not context_text.startswith("[Failed")
        await step_callback({"type": "step_complete", "step": "context", "label": "Context extracted",
                             "details": {"source": req.context_url or "text", "extracted": context_extracted}})

    # 2. Analyze intent
    await step_callback({"type": "step_start", "step": "intent", "label": "Analyzing intent"})
    intent = await analyze_intent(req.prompt, context_text[:1000] if context_text else "")
    task_category = intent.get("task_category", "general")
    complexity_str = intent.get("complexity", "medium")
    complexity = ComplexityLevel(complexity_str)
    needed_capabilities = intent.get("needed_capabilities", [])
    suggested_tools = intent.get("suggested_tools", [])
    await step_callback({"type": "step_complete", "step": "intent", "label": "Intent analyzed",
                         "details": {"category": task_category, "complexity": complexity_str,
                                     "capabilities": needed_capabilities}})

    # 3. Select LLM
    await step_callback({"type": "step_start", "step": "llm_routing", "label": "Routing to optimal LLM"})
    llm_choice = route_llm(task_category, complexity, req.preferred_model)
    routing_reason = f"Routed to {llm_choice.display_name} because: task category '{task_category}' with {complexity_str} complexity. {llm_choice.reason}."
    await step_callback({"type": "step_complete", "step": "llm_routing", "label": "LLM selected",
                         "details": {"llm": llm_choice.display_name, "model_id": llm_choice.model_id,
                                     "provider": llm_choice.provider.value, "reason": llm_choice.reason}})

    # 4. Select agents
    await step_callback({"type": "step_start", "step": "agents", "label": "Loading agents"})
    if req.preferred_agents:
        agent_slugs = [s for s in req.preferred_agents if s in AGENT_REGISTRY]
    else:
        agent_slugs = get_agents_for_task(task_category, needed_capabilities)
    agent_details = [
        {"slug": s, "name": AGENT_REGISTRY[s].name, "icon": AGENT_REGISTRY[s].icon,
         "capabilities": AGENT_REGISTRY[s].capabilities[:3]}
        for s in agent_slugs if s in AGENT_REGISTRY
    ]
    await step_callback({"type": "step_complete", "step": "agents", "label": "Agents loaded",
                         "details": {"agents": agent_details, "count": len(agent_slugs)}})

    # 5. Select tools
    if req.preferred_tools:
        tool_slugs = [s for s in req.preferred_tools if s in TOOL_REGISTRY]
    else:
        tool_slugs = [s for s in suggested_tools if s in TOOL_REGISTRY]

    # 6. Execute tools
    if tool_slugs:
        await step_callback({"type": "step_start", "step": "tools", "label": f"Executing {len(tool_slugs)} tool(s)"})
        tools_executed = await execute_tool_pipeline(tool_slugs, req.prompt, context_text)
        await step_callback({"type": "step_complete", "step": "tools", "label": "Tools executed",
                             "details": {"tools": [{"name": t["tool"], "success": t["success"]} for t in tools_executed]}})

    # 7. Build system prompt from agents + context
    system_prompt = build_agent_system_prompt(agent_slugs, context_text)

    # 8. Build user message with tool results
    user_message = req.prompt
    if tools_executed:
        tool_context = format_tool_results(tools_executed)
        user_message += tool_context

    # 9. Call selected LLM
    await step_callback({"type": "step_start", "step": "generation",
                         "label": f"Generating with {llm_choice.display_name}"})
    messages = [{"role": "user", "content": user_message}]
    response_text, input_tokens, output_tokens = await execute_llm(
        llm_choice, messages, system_prompt, req.max_tokens
    )

    # 10. Calculate metrics
    cost = estimate_cost(llm_choice.model_id, input_tokens, output_tokens)
    latency_ms = int((time.time() - start_time) * 1000)

    await step_callback({"type": "step_complete", "step": "generation", "label": "Response ready",
                         "details": {"input_tokens": input_tokens, "output_tokens": output_tokens,
                                     "cost_usd": cost, "latency_ms": latency_ms}})

    return OrchestratorResponse(
        response=response_text,
        task_category=task_category,
        complexity=complexity_str,
        selected_llm=llm_choice.model_id,
        selected_agents=agent_slugs,
        selected_tools=tool_slugs,
        tools_executed=tools_executed,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost,
        latency_ms=latency_ms,
        context_extracted=context_extracted,
        routing_reason=routing_reason,
    )
