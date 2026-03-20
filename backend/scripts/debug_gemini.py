import os
from dotenv import load_dotenv
import httpx
import asyncio
import json

async def test_gemini():
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY")
    print(f"Key found: {key[:5]}...{key[-5:] if key else 'None'}")
    
    if not key or "your_gemini" in key:
        print("ERROR: API Key is still a placeholder.")
        return

    payload = {
        "contents": [{"parts": [{"text": "Hello, respond with 'AURA ACTIVE'"}]}]
    }

    # 1. List available models
    print("\n--- Listing Available Models ---")
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(list_url, timeout=5.0)
            if res.status_code == 200:
                models = res.json().get('models', [])
                for m in models:
                    print(f"Model: {m['name']}")
            else:
                print(f"List Error {res.status_code}: {res.text}")
    except Exception as e:
        print(f"List failed: {e}")

    # 2. Try common ones
    variants = [
        ("v1beta", "gemini-1.5-flash"),
        ("v1beta", "gemini-1.5-flash-latest"),
        ("v1beta", "gemini-1.0-pro"),
    ]
    
    for version, model in variants:
        url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={key}"
        print(f"\n--- Testing {version} with {model} ---")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=5.0)
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    print(f"Success with {model}!")
                    return
                else:
                    print(f"Error: {response.json().get('error', {}).get('message', 'No message')}")
        except Exception as e:
            print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini())
