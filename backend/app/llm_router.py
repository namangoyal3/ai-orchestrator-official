"""
LLM Router — automatically selects the best model based on task complexity,
category, and available provider keys.
"""
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import anthropic

from app.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    AWS = "aws"
    OPENROUTER = "openrouter"


class ComplexityLevel(str, Enum):
    LOW = "low"        # Simple Q&A, classification, extraction
    MEDIUM = "medium"  # Summarization, content generation, conversational
    HIGH = "high"      # Reasoning, analysis, coding, multi-step


@dataclass
class LLMChoice:
    provider: LLMProvider
    model_id: str
    display_name: str
    reason: str
    cost_per_1m_input: float
    cost_per_1m_output: float


# Model catalog
MODELS = {
    # Anthropic
    "claude-opus-4-6": LLMChoice(
        provider=LLMProvider.ANTHROPIC,
        model_id="claude-opus-4-6",
        display_name="Claude Opus 4.6",
        reason="Most capable — best for complex reasoning, coding, agentic tasks",
        cost_per_1m_input=5.00,
        cost_per_1m_output=25.00,
    ),
    "claude-sonnet-4-6": LLMChoice(
        provider=LLMProvider.ANTHROPIC,
        model_id="claude-sonnet-4-6",
        display_name="Claude Sonnet 4.6",
        reason="Balanced speed and intelligence — ideal for most tasks",
        cost_per_1m_input=3.00,
        cost_per_1m_output=15.00,
    ),
    "claude-haiku-4-5": LLMChoice(
        provider=LLMProvider.ANTHROPIC,
        model_id="claude-haiku-4-5-20251001",
        display_name="Claude Haiku 4.5",
        reason="Fastest and cheapest — best for simple tasks and high-volume",
        cost_per_1m_input=1.00,
        cost_per_1m_output=5.00,
    ),
    # OpenAI
    "gpt-4o": LLMChoice(
        provider=LLMProvider.OPENAI,
        model_id="gpt-4o",
        display_name="GPT-4o",
        reason="Strong general purpose model from OpenAI",
        cost_per_1m_input=2.50,
        cost_per_1m_output=10.00,
    ),
    "gpt-4o-mini": LLMChoice(
        provider=LLMProvider.OPENAI,
        model_id="gpt-4o-mini",
        display_name="GPT-4o Mini",
        reason="Fast and affordable OpenAI model",
        cost_per_1m_input=0.15,
        cost_per_1m_output=0.60,
    ),
    # Google
    "gemini-2.0-flash": LLMChoice(
        provider=LLMProvider.GOOGLE,
        model_id="gemini-2.0-flash",
        display_name="Gemini 2.0 Flash",
        reason="Google's fast multimodal model",
        cost_per_1m_input=0.10,
        cost_per_1m_output=0.40,
    ),
    # AWS Bedrock
    "anthropic.claude-3-5-sonnet-20240620-v1:0": LLMChoice(
        provider=LLMProvider.AWS,
        model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
        display_name="Claude 3.5 Sonnet (Bedrock)",
        reason="Anthropic model provided via AWS Bedrock",
        cost_per_1m_input=3.00,
        cost_per_1m_output=15.00,
    ),
    "anthropic.claude-3-opus-20240229-v1:0": LLMChoice(
        provider=LLMProvider.AWS,
        model_id="anthropic.claude-3-opus-20240229-v1:0",
        display_name="Claude 3 Opus (Bedrock)",
        reason="Claude 3 Opus via AWS Bedrock",
        cost_per_1m_input=15.00,
        cost_per_1m_output=75.00,
    ),
    "anthropic.claude-3-haiku-20240307-v1:0": LLMChoice(
        provider=LLMProvider.AWS,
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        display_name="Claude 3 Haiku (Bedrock)",
        reason="Claude 3 Haiku via AWS Bedrock",
        cost_per_1m_input=0.25,
        cost_per_1m_output=1.25,
    ),
}

# Mapping of Anthropic direct IDs to nearest Bedrock equivalents.
# NOTE: claude-4.x models are not yet available on Bedrock — these fall back to
# the closest available Bedrock generation. Upgrade these IDs when Bedrock adds claude-4.
ANTHROPIC_TO_BEDROCK = {
    "claude-opus-4-6": "anthropic.claude-3-opus-20240229-v1:0",       # best available Bedrock fallback
    "claude-sonnet-4-6": "anthropic.claude-3-5-sonnet-20240620-v1:0", # best available Bedrock fallback
    "claude-haiku-4-5": "anthropic.claude-3-haiku-20240307-v1:0",     # best available Bedrock fallback
}

# Task category → recommended model mapping
CATEGORY_TO_MODEL = {
    "coding": "claude-opus-4-6",
    "analysis": "claude-opus-4-6",
    "reasoning": "claude-opus-4-6",
    "research": "claude-sonnet-4-6",
    "writing": "claude-sonnet-4-6",
    "summarization": "claude-sonnet-4-6",
    "document_qa": "claude-sonnet-4-6",
    "extraction": "claude-haiku-4-5",
    "classification": "claude-haiku-4-5",
    "translation": "claude-haiku-4-5",
    "simple_qa": "claude-haiku-4-5",
    "customer_support": "claude-sonnet-4-6",
    "data_analysis": "claude-opus-4-6",
    "image_analysis": "claude-opus-4-6",
    "planning": "claude-opus-4-6",
    "general": "claude-sonnet-4-6",
}


_PLACEHOLDER_PREFIXES = ("your-", "sk-your-", "change-me", "replace-me", "xxx")


def _is_real_key(value: Optional[str]) -> bool:
    """Return True only if the value looks like a real key, not a placeholder."""
    if not value:
        return False
    lower = value.lower()
    return not any(lower.startswith(p) for p in _PLACEHOLDER_PREFIXES)


def get_available_providers() -> set[str]:
    """Return set of providers with real (non-placeholder) API keys configured."""
    available = set()
    if _is_real_key(settings.anthropic_api_key):
        available.add("anthropic")
    if _is_real_key(settings.openai_api_key):
        available.add("openai")
    if _is_real_key(settings.google_api_key):
        available.add("google")
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        available.add("aws")
    if _is_real_key(settings.openrouter_api_key):
        available.add("openrouter")
    return available


def route_llm(
    task_category: str,
    complexity: ComplexityLevel,
    preferred_model: Optional[str] = None,
) -> LLMChoice:
    """
    Select the best LLM for a given task.

    Priority:
    1. User-specified model (if valid and key available)
    2. Category-based routing with automatic provider fallback (Anthropic -> Bedrock)
    3. Complexity-based fallback
    """
    available = get_available_providers()

    def get_choice(model_id: str) -> Optional[LLMChoice]:
        if model_id not in MODELS:
            return None
        choice = MODELS[model_id]
        
        # If Anthropic key missing, fall back to nearest Bedrock equivalent (older generation)
        if choice.provider == LLMProvider.ANTHROPIC and "anthropic" not in available:
            bedrock_id = ANTHROPIC_TO_BEDROCK.get(model_id)
            if bedrock_id and "aws" in available:
                logger.warning(
                    "Anthropic key unavailable — falling back from %s to Bedrock %s (different model generation)",
                    model_id, bedrock_id,
                )
                return MODELS[bedrock_id]
        
        if choice.provider.value in available:
            return choice
        return None

    # User-specified model
    if preferred_model:
        choice = get_choice(preferred_model)
        if choice:
            return choice
        # Fast fallback for dynamic OpenRouter models (they contain a '/')
        if "openrouter" in available and "/" in preferred_model:
            return LLMChoice(
                provider=LLMProvider.OPENROUTER,
                model_id=preferred_model,
                display_name=preferred_model,
                reason="Dynamically routed via OpenRouter integration",
                cost_per_1m_input=0,
                cost_per_1m_output=0,
            )

    # Category-based routing
    category_model = CATEGORY_TO_MODEL.get(task_category, "claude-sonnet-4-6")
    choice = get_choice(category_model)
    if choice:
        return choice

    # Complexity fallback (with provider logic)
    if complexity == ComplexityLevel.HIGH:
        choice = get_choice("claude-opus-4-6")
    elif complexity == ComplexityLevel.MEDIUM:
        choice = get_choice("claude-sonnet-4-6")
    else:
        choice = get_choice("claude-haiku-4-5")
        
    if choice:
        return choice
    
    # Absolute fallback (first available from MODELS)
    for model_id in CATEGORY_TO_MODEL.values():
        choice = get_choice(model_id)
        if choice:
            return choice
            
    # If still nothing, return the first model we have keys for
    for choice in MODELS.values():
        if choice.provider.value in available:
            return choice

    # Last resort: OpenRouter free tier (works with any OpenRouter key)
    if "openrouter" in available:
        logger.warning("All preferred models exhausted — falling back to OpenRouter free tier")
        return LLMChoice(
            provider=LLMProvider.OPENROUTER,
            model_id="openrouter/auto",
            display_name="OpenRouter Auto (free fallback)",
            reason="All configured providers exhausted — using OpenRouter free routing",
            cost_per_1m_input=0,
            cost_per_1m_output=0,
        )

    raise RuntimeError("No LLM providers available. Please configure at least one API key.")


def estimate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost in USD for a request."""
    if model_id not in MODELS:
        return 0.0
    model = MODELS[model_id]
    input_cost = (input_tokens / 1_000_000) * model.cost_per_1m_input
    output_cost = (output_tokens / 1_000_000) * model.cost_per_1m_output
    return round(input_cost + output_cost, 6)


async def call_anthropic(
    model_id: str,
    messages: list[dict],
    system: Optional[str] = None,
    max_tokens: int = 8096,
    stream: bool = False,
) -> tuple[str, int, int]:
    """Call Anthropic API and return (response_text, input_tokens, output_tokens)."""
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    kwargs = {
        "model": model_id,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if system:
        kwargs["system"] = system

    response = await client.messages.create(**kwargs)

    text = ""
    for block in response.content:
        if block.type == "text":
            text = block.text
            break

    return text, response.usage.input_tokens, response.usage.output_tokens


async def call_openai(
    model_id: str,
    messages: list[dict],
    system: Optional[str] = None,
    max_tokens: int = 4096,
) -> tuple[str, int, int]:
    """Call OpenAI API."""
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)

        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        response = await client.chat.completions.create(
            model=model_id,
            messages=full_messages,
            max_tokens=max_tokens,
        )

        text = response.choices[0].message.content or ""
        return text, response.usage.prompt_tokens, response.usage.completion_tokens
    except ImportError:
        raise RuntimeError("openai package not installed")


async def call_google(
    model_id: str,
    messages: list[dict],
    system: Optional[str] = None,
    max_tokens: int = 4096,
) -> tuple[str, int, int]:
    """Call Google Gemini API."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.google_api_key)
        model = genai.GenerativeModel(model_id, system_instruction=system)

        # Convert messages to Gemini format
        history = []
        last_msg = messages[-1]["content"] if messages else ""
        for msg in messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})

        chat = model.start_chat(history=history)
        response = await chat.send_message_async(last_msg)

        text = response.text
        # Gemini doesn't always return token counts in the same way
        input_tokens = getattr(response, "usage_metadata", None)
        if input_tokens:
            return text, input_tokens.prompt_token_count, input_tokens.candidates_token_count
        return text, 0, 0
    except ImportError:
        raise RuntimeError("google-generativeai package not installed")


async def call_aws_bedrock(
    model_id: str,
    messages: list[dict],
    system: Optional[str] = None,
    max_tokens: int = 4096,
) -> tuple[str, int, int]:
    """Call AWS Bedrock API."""
    try:
        import boto3
        import json
        import asyncio

        client = boto3.client(
            service_name="bedrock-runtime",
            region_name=settings.aws_region_name,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )

        # Convert messages to Bedrock (Claude) format
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            payload["system"] = system

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.invoke_model(
                body=json.dumps(payload),
                modelId=model_id,
            )
        )

        response_body = json.loads(response.get("body").read())
        text = response_body.get("content", [{}])[0].get("text", "")
        input_tokens = response_body.get("usage", {}).get("input_tokens", 0)
        output_tokens = response_body.get("usage", {}).get("output_tokens", 0)

        return text, input_tokens, output_tokens
    except ImportError:
        raise RuntimeError("boto3 package not installed")
    except Exception as e:
        raise RuntimeError(f"AWS Bedrock error: {str(e)}")


async def call_openrouter(
    model_id: str,
    messages: list[dict],
    system: Optional[str] = None,
    max_tokens: int = 4096,
) -> tuple[str, int, int]:
    """Call OpenRouter API."""
    import httpx
    
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://namango.ai",
        "X-Title": "Namango3 Gateway",
    }
    
    full_messages = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.extend(messages)
    
    payload = {
        "model": model_id,
        "messages": full_messages,
        "max_tokens": max_tokens
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=60.0
        )
        response.raise_for_status()
        data = response.json()
        
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = data.get("usage", {})
        
        return text, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


async def execute_llm(
    llm_choice: LLMChoice,
    messages: list[dict],
    system: Optional[str] = None,
    max_tokens: int = 8096,
) -> tuple[str, int, int]:
    """Execute LLM call based on the chosen provider."""
    if llm_choice.provider == LLMProvider.ANTHROPIC:
        return await call_anthropic(llm_choice.model_id, messages, system, max_tokens)
    elif llm_choice.provider == LLMProvider.OPENAI:
        return await call_openai(llm_choice.model_id, messages, system, max_tokens)
    elif llm_choice.provider == LLMProvider.GOOGLE:
        return await call_google(llm_choice.model_id, messages, system, max_tokens)
    elif llm_choice.provider == LLMProvider.AWS:
        return await call_aws_bedrock(llm_choice.model_id, messages, system, max_tokens)
    elif llm_choice.provider == LLMProvider.OPENROUTER:
        return await call_openrouter(llm_choice.model_id, messages, system, max_tokens)
    else:
        raise ValueError(f"Unsupported provider: {llm_choice.provider}")
