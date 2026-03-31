"""
Analytics endpoints — usage metrics, costs, and performance.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.auth import validate_api_key
from app.database import get_db
from app.models import APIKey, Organization, RequestLog

router = APIRouter(prefix="/v1/analytics", tags=["Analytics"])


@router.get("/summary", summary="Get usage summary")
async def get_summary(
    days: int = 30,
    auth: tuple[APIKey, Organization] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated usage statistics for your organization."""
    _, org = auth
    since = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(
            func.count(RequestLog.id).label("total_requests"),
            func.sum(func.cast(RequestLog.status == "completed", int)).label("successful"),
            func.sum(func.cast(RequestLog.status == "failed", int)).label("failed"),
            func.sum(RequestLog.input_tokens).label("total_input_tokens"),
            func.sum(RequestLog.output_tokens).label("total_output_tokens"),
            func.sum(RequestLog.cost_usd).label("total_cost"),
            func.avg(RequestLog.latency_ms).label("avg_latency"),
        ).where(
            RequestLog.org_id == org.id,
            RequestLog.created_at >= since,
        )
    )
    row = result.first()

    total = row.total_requests or 0
    successful = row.successful or 0
    failed = row.failed or 0

    return {
        "period_days": days,
        "total_requests": total,
        "successful_requests": successful,
        "failed_requests": failed,
        "success_rate": round(successful / total * 100, 1) if total > 0 else 0,
        "total_input_tokens": row.total_input_tokens or 0,
        "total_output_tokens": row.total_output_tokens or 0,
        "total_tokens": (row.total_input_tokens or 0) + (row.total_output_tokens or 0),
        "total_cost_usd": round(row.total_cost or 0, 4),
        "avg_latency_ms": round(row.avg_latency or 0),
    }


@router.get("/timeseries", summary="Get daily request counts")
async def get_timeseries(
    days: int = 14,
    auth: tuple[APIKey, Organization] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Get day-by-day request volume for charting."""
    _, org = auth
    since = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(
            func.date(RequestLog.created_at).label("date"),
            func.count(RequestLog.id).label("requests"),
            func.sum(RequestLog.cost_usd).label("cost"),
        )
        .where(RequestLog.org_id == org.id, RequestLog.created_at >= since)
        .group_by(func.strftime("%Y-%m-%d", RequestLog.created_at))
        .order_by("date")
    )
    rows = result.all()

    # Fill in missing days with zeros
    date_map = {row.date: {"requests": row.requests, "cost": round(row.cost or 0, 4)} for row in rows}
    timeline = []
    for i in range(days):
        date = (since + timedelta(days=i + 1)).strftime("%Y-%m-%d")
        timeline.append({
            "date": date,
            "requests": date_map.get(date, {}).get("requests", 0),
            "cost": date_map.get(date, {}).get("cost", 0),
        })

    return {"timeline": timeline}


@router.get("/models", summary="Model usage breakdown")
async def get_model_usage(
    days: int = 30,
    auth: tuple[APIKey, Organization] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Break down requests by LLM model."""
    _, org = auth
    since = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(
            RequestLog.selected_llm,
            func.count(RequestLog.id).label("count"),
            func.sum(RequestLog.cost_usd).label("cost"),
        )
        .where(RequestLog.org_id == org.id, RequestLog.created_at >= since)
        .group_by(RequestLog.selected_llm)
        .order_by(desc("count"))
    )
    rows = result.all()

    _DISPLAY_NAMES = {
        "openai/gpt-4o": "GPT-4o",
        "openai/gpt-4o-mini": "GPT-4o Mini",
        "openai/gpt-oss-120b:free": "GPT OSS 120B",
        "openai/gpt-oss-20b:free": "GPT OSS 20B",
        "anthropic/claude-3-5-sonnet": "Claude 3.5 Sonnet",
        "anthropic/claude-3-5-sonnet-20241022": "Claude 3.5 Sonnet",
        "anthropic/claude-3-haiku": "Claude 3 Haiku",
        "meta-llama/llama-3.1-70b-instruct": "Llama 3.1 70B",
        "meta-llama/llama-3.1-8b-instruct": "Llama 3.1 8B",
        "meta-llama/llama-3.2-3b-instruct:free": "Llama 3.2 3B",
        "meta-llama/llama-3.3-70b-instruct:free": "Llama 3.3 70B",
        "mistralai/mistral-7b-instruct": "Mistral 7B",
        "mistralai/mistral-small-3.1-24b-instruct:free": "Mistral Small 24B",
        "google/gemini-pro": "Gemini Pro",
        "google/gemini-flash-1.5": "Gemini Flash 1.5",
        "google/gemma-3-27b-it:free": "Gemma 3 27B",
        "google/gemma-3-12b-it:free": "Gemma 3 12B",
        "google/gemma-2-9b-it:free": "Gemma 2 9B",
        "nousresearch/hermes-3-llama-3.1-405b:free": "Hermes 3 405B",
        "qwen/qwen3-coder:free": "Qwen3 Coder",
        "qwen/qwen3-next-80b-a3b-instruct:free": "Qwen3 80B",
        "qwen/qwen-2.5-7b-instruct:free": "Qwen 2.5 7B",
        "deepseek/deepseek-r1:free": "DeepSeek R1",
        "cohere/command-r-plus": "Command R+",
        "claude-opus-4-6": "Claude Opus 4.6",
        "claude-sonnet-4-6": "Claude Sonnet 4.6",
        "claude-haiku-4-5-20251001": "Claude Haiku 4.5",
        "gpt-4o": "GPT-4o",
        "gpt-4o-mini": "GPT-4o Mini",
        "gemini-2.0-flash": "Gemini 2.0 Flash",
    }

    def _display(model_id: str) -> str:
        if model_id in _DISPLAY_NAMES:
            return _DISPLAY_NAMES[model_id]
        # Strip provider prefix: "meta-llama/llama-3.1-70b" → "llama-3.1-70b"
        name = model_id.split("/")[-1] if "/" in model_id else model_id
        return name.replace("-", " ").title()

    return {
        "models": [
            {
                "model": row.selected_llm or "unknown",
                "display_name": _display(row.selected_llm or "unknown"),
                "requests": row.count,
                "cost": round(row.cost or 0, 4),
            }
            for row in rows
        ]
    }


@router.get("/categories", summary="Task category breakdown")
async def get_category_usage(
    days: int = 30,
    auth: tuple[APIKey, Organization] = Depends(validate_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Break down requests by task category."""
    _, org = auth
    since = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(
            RequestLog.task_category,
            func.count(RequestLog.id).label("count"),
        )
        .where(RequestLog.org_id == org.id, RequestLog.created_at >= since)
        .group_by(RequestLog.task_category)
        .order_by(desc("count"))
    )
    rows = result.all()

    return {
        "categories": [
            {"category": row.task_category or "general", "requests": row.count}
            for row in rows
        ]
    }
