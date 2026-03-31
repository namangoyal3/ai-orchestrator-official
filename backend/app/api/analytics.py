"""
Analytics endpoints — usage metrics, costs, and performance.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, case
import httpx

from app.auth import validate_api_key
from app.config import settings
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

    # Fetch aggregate stats using only portable SQL functions (no CASE/CAST)
    agg = await db.execute(
        select(
            func.count(RequestLog.id).label("total"),
            func.sum(RequestLog.input_tokens).label("in_tok"),
            func.sum(RequestLog.output_tokens).label("out_tok"),
            func.sum(RequestLog.cost_usd).label("cost"),
            func.avg(RequestLog.latency_ms).label("latency"),
        ).where(RequestLog.org_id == org.id, RequestLog.created_at >= since)
    )
    agg_row = agg.first()

    # Count by status with separate queries — avoids CAST/CASE portability issues
    ok_result = await db.execute(
        select(func.count(RequestLog.id)).where(
            RequestLog.org_id == org.id,
            RequestLog.created_at >= since,
            RequestLog.status == "completed",
        )
    )
    fail_result = await db.execute(
        select(func.count(RequestLog.id)).where(
            RequestLog.org_id == org.id,
            RequestLog.created_at >= since,
            RequestLog.status == "failed",
        )
    )

    total = agg_row.total or 0
    successful = ok_result.scalar() or 0
    failed = fail_result.scalar() or 0

    return {
        "period_days": days,
        "total_requests": total,
        "successful_requests": successful,
        "failed_requests": failed,
        "success_rate": round(successful / total * 100, 1) if total > 0 else 0,
        "total_input_tokens": agg_row.in_tok or 0,
        "total_output_tokens": agg_row.out_tok or 0,
        "total_tokens": (agg_row.in_tok or 0) + (agg_row.out_tok or 0),
        "total_cost_usd": round(agg_row.cost or 0, 4),
        "avg_latency_ms": round(agg_row.latency or 0),
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
        .group_by(func.date(RequestLog.created_at))
        .order_by("date")
    )
    rows = result.all()

    # Fill in missing days with zeros.
    # func.date() returns a Python date object on PostgreSQL; convert to string for key lookup.
    date_map = {
        row.date.isoformat() if hasattr(row.date, "isoformat") else str(row.date): {
            "requests": row.requests,
            "cost": round(row.cost or 0, 4),
        }
        for row in rows
    }
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


@router.get("/openrouter", summary="OpenRouter key stats and free models")
async def get_openrouter_analytics(
    auth: tuple[APIKey, Organization] = Depends(validate_api_key),
):
    """Fetch OpenRouter API key usage stats and available free models."""
    or_key = settings.openrouter_api_key
    if not or_key:
        return {"error": "OpenRouter API key not configured", "key_stats": None, "free_models": []}

    headers = {"Authorization": f"Bearer {or_key}"}
    key_stats = None
    free_models = []

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Key usage stats
        try:
            r = await client.get("https://openrouter.ai/api/v1/auth/key", headers=headers)
            if r.status_code == 200:
                data = r.json().get("data", {})
                key_stats = {
                    "usage_total": round(data.get("usage", 0), 6),
                    "usage_daily": round(data.get("usage_daily", 0), 6),
                    "usage_weekly": round(data.get("usage_weekly", 0), 6),
                    "usage_monthly": round(data.get("usage_monthly", 0), 6),
                    "is_free_tier": data.get("is_free_tier", False),
                    "limit": data.get("limit"),
                }
        except Exception:
            pass

        # Free models catalog
        try:
            r = await client.get("https://openrouter.ai/api/v1/models", headers=headers)
            if r.status_code == 200:
                all_models = r.json().get("data", [])
                for m in all_models:
                    pricing = m.get("pricing", {})
                    if str(pricing.get("prompt", "1")) == "0":
                        free_models.append({
                            "id": m["id"],
                            "name": m.get("name", m["id"]),
                            "context_length": m.get("context_length", 0),
                            "description": (m.get("description") or "")[:120],
                        })
                # Sort by context length desc
                free_models.sort(key=lambda x: x["context_length"], reverse=True)
        except Exception:
            pass

    return {
        "key_stats": key_stats,
        "free_models": free_models,
        "free_models_count": len(free_models),
    }
