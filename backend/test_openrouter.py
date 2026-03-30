import asyncio
import os
os.environ["OPENROUTER_API_KEY"] = "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"

from app.llm_router import execute_llm, route_llm, ComplexityLevel

async def test():
    print("Testing OpenRouter Integration...")
    
    # Force a route to an OpenRouter specific model
    choice = route_llm(task_category="general", complexity=ComplexityLevel.LOW, preferred_model="meta-llama/llama-3-8b-instruct")
    
    print(f"Routed Choice: {choice.provider} - {choice.model_id}")
    
    messages = [{"role": "user", "content": "What is the capital of France? Answer in one word."}]
    response, p_tokens, c_tokens = await execute_llm(choice, messages)
    
    print(f"\nResponse: {response.strip()}")
    print(f"Tokens: In={p_tokens}, Out={c_tokens}")

if __name__ == "__main__":
    asyncio.run(test())
