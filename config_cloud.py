#!/usr/bin/env python3
"""
Alternative configuration using FREE cloud APIs instead of Ollama
Works on Render, Railway, Fly.io, etc.
"""

# ==================== FREE API OPTIONS ====================

# Option 1: Groq (FREE - 14,400 requests/day)
# https://console.groq.com
GROQ_API_KEY = "your_groq_api_key_here"
GROQ_MODEL = "mixtral-8x7b-32768"  # Fast and free

# Option 2: Together.ai (FREE $25/month credit)
# https://together.ai
TOGETHER_API_KEY = "your_together_api_key_here"
TOGETHER_MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1"

# Option 3: Hugging Face (FREE inference)
# https://huggingface.co
HF_API_KEY = "your_hf_token_here"
HF_MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1"

# Option 4: OpenRouter (Multiple free models)
# https://openrouter.ai
OPENROUTER_API_KEY = "your_openrouter_key_here"
OPENROUTER_MODEL = "mistralai/mixtral-8x7b-instruct"  # Free tier

# ==================== CONFIGURATION ====================

USE_CLOUD_API = True  # Set to True for cloud hosting
CLOUD_PROVIDER = "groq"  # Options: "groq", "together", "huggingface", "openrouter"

# ==================== CODE CHANGES ====================

def get_llm():
    """Get LLM based on configuration"""
    
    if not USE_CLOUD_API:
        # Use local Ollama (for your laptop)
        from langchain_ollama import OllamaLLM
        return OllamaLLM(model="qwen2.5-coder:3b", temperature=0.1)
    
    # Use cloud API (for free hosting)
    if CLOUD_PROVIDER == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model_name=GROQ_MODEL,
            temperature=0.1
        )
    
    elif CLOUD_PROVIDER == "together":
        from langchain_together import Together
        return Together(
            together_api_key=TOGETHER_API_KEY,
            model=TOGETHER_MODEL,
            temperature=0.1
        )
    
    elif CLOUD_PROVIDER == "huggingface":
        from langchain_community.llms import HuggingFaceHub
        return HuggingFaceHub(
            huggingfacehub_api_token=HF_API_KEY,
            repo_id=HF_MODEL,
            model_kwargs={"temperature": 0.1}
        )
    
    elif CLOUD_PROVIDER == "openrouter":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            openai_api_key=OPENROUTER_API_KEY,
            openai_api_base="https://openrouter.ai/api/v1",
            model_name=OPENROUTER_MODEL,
            temperature=0.1
        )

# ==================== USAGE ====================

"""
To use on Render/Railway/Fly.io:

1. Sign up for Groq (recommended - fastest & most generous free tier)
   https://console.groq.com

2. Get API key and add to environment variables:
   GROQ_API_KEY=your_key_here

3. Update oem_search.py:
   Replace:
     llm = OllamaLLM(model=OLLAMA_MODEL, ...)
   With:
     from config_cloud import get_llm
     llm = get_llm()

4. Deploy to Render/Railway with cron job

That's it! No local Ollama needed.
"""

# ==================== FREE TIER LIMITS ====================

FREE_TIER_LIMITS = {
    "groq": {
        "requests_per_day": 14400,
        "requests_per_minute": 30,
        "tokens_per_minute": 20000,
        "cost": "FREE",
        "best_for": "Production use - very generous limits"
    },
    "together": {
        "monthly_credit": "$25",
        "requests": "~500,000/month",
        "cost": "FREE $25/month",
        "best_for": "High volume testing"
    },
    "huggingface": {
        "requests": "Limited by model",
        "cost": "FREE (rate limited)",
        "best_for": "Experimentation"
    },
    "openrouter": {
        "requests": "Varies by model",
        "cost": "FREE models available",
        "best_for": "Model variety"
    }
}

print("="*60)
print("CLOUD API OPTIONS FOR FREE HOSTING")
print("="*60)
for provider, limits in FREE_TIER_LIMITS.items():
    print(f"\n{provider.upper()}:")
    for key, value in limits.items():
        print(f"  {key}: {value}")
print("\n" + "="*60)
print("RECOMMENDATION: Use Groq - 14,400 free requests/day!")
print("="*60)
