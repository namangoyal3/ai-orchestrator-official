"""
AI Gateway — the single public API endpoint companies integrate with.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
import json as json_lib

from app.auth import validate_api_key
from app.database import get_db
from app.models import APIKey, Organization, RequestLog
from app.orchestrator import orchestrate, OrchestratorRequest

router = APIRouter(prefix="/v1", tags=["Gateway"])


class GatewayRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=50000, description="Your task or question")
    context_url: Optional[str] = Field(None, description="URL to extract context from")
    context_text: Optional[str] = Field(None, description="Raw text context")
    preferred_model: Optional[str] = Field(None, description="Specific LLM model ID (e.g. claude-opus-4-6)")
    preferred_agents: Optional[list[str]] = Field(None, description="Specific agent slugs to use")
    preferred_tools: Optional[list[str]] = Field(None, description="Specific tool slugs to use")
    max_tokens: int = Field(8096, ge=256, le=128000, description="Max output tokens")
    metadata: Optional[dict] = Field(None, description="Optional metadata for tracking")


class ToolExecuted(BaseModel):
    tool: str
    success: bool
    output: object


class OrchestratorMeta(BaseModel):
    task_category: str
    complexity: str
    selected_llm: str
    selected_agents: list[str]
    selected_tools: list[str]
    tools_executed: list[ToolExecuted]
    context_extracted: bool
    routing_reason: str = ""


class UsageMeta(BaseModel):
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int


class GatewayResponse(BaseModel):
    id: str
    response: str
    orchestration: OrchestratorMeta
    usage: UsageMeta
    created_at: str


@router.post("/query", response_model=GatewayResponse, summary="Submit a task to the AI Gateway")
async def query(
    request: GatewayRequest,
    auth: tuple[APIKey, Organization] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    **The primary endpoint** — submit any task and the gateway automatically:
    - Extracts context from the provided URL or document
    - Analyzes intent and complexity
    - Selects the optimal LLM, agents, and tools
    - Executes the pipeline
    - Returns a structured response with full orchestration metadata

    Authenticate with `X-API-Key: gw-your-api-key`.
    """
    api_key, org = auth

    # Create request log
    log = RequestLog(
        org_id=org.id,
        api_key_id=api_key.id,
        prompt=request.prompt,
        context_url=request.context_url,
        context_type="url" if request.context_url else ("text" if request.context_text else "none"),
        status="processing",
    )
    db.add(log)
    await db.flush()

    try:
        orch_req = OrchestratorRequest(
            prompt=request.prompt,
            context_url=request.context_url,
            context_text=request.context_text,
            preferred_model=request.preferred_model,
            preferred_agents=request.preferred_agents,
            preferred_tools=request.preferred_tools,
            max_tokens=request.max_tokens,
        )

        result = await orchestrate(orch_req)

        # Update log
        log.response = result.response
        log.status = "completed"
        log.selected_llm = result.selected_llm
        log.selected_agents = result.selected_agents
        log.selected_tools = result.selected_tools
        log.task_category = result.task_category
        log.complexity_score = {"low": 0.3, "medium": 0.6, "high": 0.9}.get(result.complexity, 0.5)
        log.latency_ms = result.latency_ms
        log.input_tokens = result.input_tokens
        log.output_tokens = result.output_tokens
        log.cost_usd = result.cost_usd
        log.completed_at = datetime.utcnow()
        await db.commit()

        return GatewayResponse(
            id=log.id,
            response=result.response,
            orchestration=OrchestratorMeta(
                task_category=result.task_category,
                complexity=result.complexity,
                selected_llm=result.selected_llm,
                selected_agents=result.selected_agents,
                selected_tools=result.selected_tools,
                tools_executed=[ToolExecuted(**t) for t in result.tools_executed],
                context_extracted=result.context_extracted,
                routing_reason=result.routing_reason,
            ),
            usage=UsageMeta(
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                cost_usd=result.cost_usd,
                latency_ms=result.latency_ms,
            ),
            created_at=log.created_at.isoformat() if log.created_at else datetime.utcnow().isoformat(),
        )

    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("Orchestration failed for org=%s prompt=%r", org.id, request.prompt[:100])
        log.status = "failed"
        log.error_message = str(e)
        log.completed_at = datetime.utcnow()
        await db.commit()
        raise HTTPException(status_code=500, detail="Orchestration failed — check server logs")


@router.post("/query/stream", summary="Streaming version of /v1/query — returns SSE stream")
async def query_stream(
    request: GatewayRequest,
    auth: tuple[APIKey, Organization] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Streaming endpoint — returns Server-Sent Events as the response is generated.
    Events: status, metadata, token, done, [DONE]
    """
    api_key, org = auth

    log = RequestLog(
        org_id=org.id,
        api_key_id=api_key.id,
        prompt=request.prompt,
        context_url=request.context_url,
        context_type="url" if request.context_url else ("text" if request.context_text else "none"),
        status="processing",
    )
    db.add(log)
    await db.flush()

    orch_req = OrchestratorRequest(
        prompt=request.prompt,
        context_url=request.context_url,
        context_text=request.context_text,
        preferred_model=request.preferred_model,
        preferred_agents=request.preferred_agents or [],
        preferred_tools=request.preferred_tools or [],
        max_tokens=request.max_tokens or 8096,
    )

    import asyncio
    queue: asyncio.Queue = asyncio.Queue()
    SENTINEL = object()

    async def step_callback(event: dict) -> None:
        await queue.put(event)

    async def run_orchestration():
        try:
            result = await orchestrate(orch_req, step_callback=step_callback)
            log.response = result.response
            log.status = "completed"
            log.selected_llm = result.selected_llm
            log.selected_agents = result.selected_agents
            log.selected_tools = result.selected_tools
            log.task_category = result.task_category
            log.complexity_score = {"low": 0.3, "medium": 0.6, "high": 0.9}.get(result.complexity, 0.5)
            log.latency_ms = result.latency_ms
            log.input_tokens = result.input_tokens
            log.output_tokens = result.output_tokens
            log.cost_usd = result.cost_usd
            log.completed_at = datetime.utcnow()
            await db.commit()
            await queue.put({"type": "_result", "result": result})
        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)
            log.completed_at = datetime.utcnow()
            await db.commit()
            await queue.put({"type": "_error", "detail": str(e)})
        finally:
            await queue.put(SENTINEL)

    async def event_stream():
        task = asyncio.create_task(run_orchestration())
        result = None

        while True:
            event = await queue.get()
            if event is SENTINEL:
                break
            if event.get("type") == "_result":
                result = event["result"]
                continue
            if event.get("type") == "_error":
                yield f"data: {json_lib.dumps({'type': 'error', 'detail': event['detail']})}\n\n"
                break
            # Forward step events directly to client
            yield f"data: {json_lib.dumps(event)}\n\n"

        await task

        if result is None:
            return

        # Stream response text word by word
        words = result.response.split(" ")
        chunk: list[str] = []
        for i, word in enumerate(words):
            chunk.append(word)
            if len(chunk) >= 5 or i == len(words) - 1:
                yield f"data: {json_lib.dumps({'type': 'token', 'text': ' '.join(chunk) + (' ' if i < len(words) - 1 else '')})}\n\n"
                chunk = []

        # Final metadata + done
        yield f"data: {json_lib.dumps({'type': 'metadata', 'task_category': result.task_category, 'complexity': result.complexity, 'selected_llm': result.selected_llm, 'selected_agents': result.selected_agents, 'selected_tools': result.selected_tools, 'tools_executed': result.tools_executed, 'context_extracted': result.context_extracted, 'routing_reason': result.routing_reason})}\n\n"
        yield f"data: {json_lib.dumps({'type': 'done', 'input_tokens': result.input_tokens, 'output_tokens': result.output_tokens, 'cost_usd': result.cost_usd, 'latency_ms': result.latency_ms})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/models", summary="List available LLM models")
async def list_models(auth: tuple[APIKey, Organization] = Depends(validate_api_key)):
    """List all available LLM models with their capabilities and pricing."""
    from app.llm_router import MODELS
    return {
        "models": [
            {
                "id": m.model_id,
                "display_name": m.display_name,
                "provider": m.provider.value,
                "description": m.reason,
                "pricing": {
                    "input_per_1m": m.cost_per_1m_input,
                    "output_per_1m": m.cost_per_1m_output,
                },
            }
            for m in MODELS.values()
        ]
    }


@router.get("/history", summary="Get request history for your organization")
async def get_history(
    limit: int = 20,
    offset: int = 0,
    auth: tuple[APIKey, Organization] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve request history for auditing and debugging."""
    from sqlalchemy import select, desc
    _, org = auth
    result = await db.execute(
        select(RequestLog)
        .where(RequestLog.org_id == org.id)
        .order_by(desc(RequestLog.created_at))
        .limit(limit)
        .offset(offset)
    )
    logs = result.scalars().all()
    return {
        "items": [
            {
                "id": log.id,
                "prompt": log.prompt[:100] + "..." if len(log.prompt) > 100 else log.prompt,
                "status": log.status,
                "selected_llm": log.selected_llm,
                "selected_agents": log.selected_agents,
                "task_category": log.task_category,
                "latency_ms": log.latency_ms,
                "cost_usd": log.cost_usd,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": len(logs),
    }
