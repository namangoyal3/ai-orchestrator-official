#!/usr/bin/env python3
"""
Seed demo API calls through the gateway to OpenRouter.

Usage:
    GATEWAY_URL=https://your-app.railway.app API_KEY=gw-... python seed_demo_calls.py

Defaults to localhost:8000 if GATEWAY_URL is not set.
All models below are free-tier on OpenRouter (no credits required).
"""
import os
import time
import httpx

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000").rstrip("/")
API_KEY = os.getenv("API_KEY", "")

# 25 prompts using only free-tier OpenRouter models.
# Distribution shows variety across model families for the dashboard charts.
CALLS = [
    # Llama 3.3 70B — complex reasoning (30% = 7-8 calls)
    {"model": "meta-llama/llama-3.3-70b-instruct:free", "prompt": "Explain the trade-offs between microservices and monolithic architectures for a startup with 5 engineers."},
    {"model": "meta-llama/llama-3.3-70b-instruct:free", "prompt": "Design a rate limiting system that handles 10,000 requests per second with burst tolerance."},
    {"model": "meta-llama/llama-3.3-70b-instruct:free", "prompt": "What are the key differences between transformer attention mechanisms in GPT vs BERT?"},
    {"model": "meta-llama/llama-3.3-70b-instruct:free", "prompt": "How should a B2B SaaS company price its product for enterprise customers? Walk through the key frameworks."},
    {"model": "meta-llama/llama-3.3-70b-instruct:free", "prompt": "Explain how vector databases work and when to use them over traditional SQL for AI applications."},
    {"model": "meta-llama/llama-3.3-70b-instruct:free", "prompt": "What makes a great AI product demo for YC interviews? What do partners look for?"},
    {"model": "meta-llama/llama-3.3-70b-instruct:free", "prompt": "Compare the CAP theorem implications for a real-time analytics dashboard vs a payment processing system."},
    # Hermes 3 405B — research/analysis (25% = 6 calls)
    {"model": "nousresearch/hermes-3-llama-3.1-405b:free", "prompt": "Analyze the competitive landscape for AI API gateways. Who are the key players and what are their differentiation strategies?"},
    {"model": "nousresearch/hermes-3-llama-3.1-405b:free", "prompt": "What are the most common failure modes when companies try to integrate LLMs into production systems?"},
    {"model": "nousresearch/hermes-3-llama-3.1-405b:free", "prompt": "Research the history of API management tools from MuleSoft to Kong to modern AI gateways."},
    {"model": "nousresearch/hermes-3-llama-3.1-405b:free", "prompt": "What metrics should an AI infrastructure company track to demonstrate product-market fit?"},
    {"model": "nousresearch/hermes-3-llama-3.1-405b:free", "prompt": "Summarize the key insights from the 2024 State of AI report regarding enterprise adoption patterns."},
    {"model": "nousresearch/hermes-3-llama-3.1-405b:free", "prompt": "How do leading AI companies structure their developer relations and ecosystem strategies?"},
    # Llama 3.1 70B — coding/debug (20% = 5 calls)
    {"model": "meta-llama/llama-3.1-70b-instruct", "prompt": "Write a Python function to implement exponential backoff with jitter for API retry logic."},
    {"model": "meta-llama/llama-3.1-70b-instruct", "prompt": "Debug this FastAPI middleware that occasionally drops request headers: def add_headers(request, call_next): headers = request.headers.copy()"},
    {"model": "meta-llama/llama-3.1-70b-instruct", "prompt": "Write a TypeScript React hook for managing streaming API responses with abort controller support."},
    {"model": "meta-llama/llama-3.1-70b-instruct", "prompt": "Implement a simple LRU cache in Python without using OrderedDict."},
    {"model": "meta-llama/llama-3.1-70b-instruct", "prompt": "Write a SQL query to find the top 5 most expensive API calls per user in the last 7 days."},
    # Gemma 3 27B — summarization (15% = 4 calls)
    {"model": "google/gemma-3-27b-it:free", "prompt": "Summarize the key points of the Attention Is All You Need paper in 3 bullet points for a non-technical audience."},
    {"model": "google/gemma-3-27b-it:free", "prompt": "Summarize what an AI gateway does and why developers need it in two sentences."},
    {"model": "google/gemma-3-27b-it:free", "prompt": "Give me a one-paragraph summary of how model routing improves cost efficiency in LLM applications."},
    {"model": "google/gemma-3-27b-it:free", "prompt": "Summarize the differences between prompt caching, semantic caching, and response caching for LLMs."},
    # Qwen3 Coder — extraction/structured (10% = 2-3 calls)
    {"model": "qwen/qwen3-coder:free", "prompt": "Extract all technical requirements from this text: 'We need a system that handles 1000 RPS, has p99 latency under 200ms, costs less than $500/month, and supports both REST and GraphQL.'"},
    {"model": "qwen/qwen3-coder:free", "prompt": "Translate the following developer documentation into plain English for a non-technical executive: 'The gateway implements circuit breaking with a sliding window algorithm to prevent cascade failures across LLM provider endpoints.'"},
    {"model": "qwen/qwen3-coder:free", "prompt": "Extract the action items and owners from this meeting note: 'Alice will set up Railway deployment by Friday. Bob owns the OpenRouter integration. Carol needs to write the seeding script before the YC demo.'"},
]


def seed():
    if not API_KEY:
        print("WARNING: API_KEY not set. Requests may return 401.")

    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["X-API-Key"] = API_KEY

    print(f"Seeding {len(CALLS)} demo calls to {GATEWAY_URL}...")
    success = 0
    failed = 0

    for i, call in enumerate(CALLS, 1):
        payload = {
            "prompt": call["prompt"],
            "preferred_model": call["model"],
        }
        try:
            resp = httpx.post(
                f"{GATEWAY_URL}/v1/query",
                json=payload,
                headers=headers,
                timeout=60.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                model_used = data.get("metadata", {}).get("selected_llm", call["model"])
                tokens = data.get("usage", {}).get("total_tokens", "?")
                print(f"  [{i:02d}/{len(CALLS)}] OK  {model_used} — {tokens} tokens")
                success += 1
            else:
                print(f"  [{i:02d}/{len(CALLS)}] ERR {resp.status_code} — {resp.text[:120]}")
                failed += 1
        except httpx.TimeoutException:
            print(f"  [{i:02d}/{len(CALLS)}] TIMEOUT — {call['model']}")
            failed += 1
        except Exception as e:
            print(f"  [{i:02d}/{len(CALLS)}] FAIL — {e}")
            failed += 1

        # Small delay to avoid hammering the gateway
        if i < len(CALLS):
            time.sleep(0.8)

    print(f"\nDone. {success} succeeded, {failed} failed.")
    if failed > 0:
        print("Tip: Make sure OPENROUTER_API_KEY is set on the gateway and the models above are enabled.")


if __name__ == "__main__":
    seed()
