import os
import httpx
import asyncio
from dotenv import load_dotenv

async def list_models():
    # Use the specific key from .env to verify it
    key = "AIzaSyCr8YNGpdJME7b8d60NpWojc_njGLLJKp4"
    print(f"Testing Key: {key}")
    
    for v in ["v1", "v1beta"]:
        url = f"https://generativelanguage.googleapis.com/{v}/models?key={key}"
        print(f"\n--- Testing {v} ---")
        async with httpx.AsyncClient() as client:
            try:
                res = await client.get(url)
                print(f"Status: {res.status_code}")
                if res.status_code == 200:
                    with open("models_list.txt", "w") as f:
                        models = res.json().get('models', [])
                        for m in models:
                            f.write(f"{m['name']}\n")
                    print("Models saved to models_list.txt")
                else:
                    print(f"Error: {res.text}")
            except Exception as e:
                print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(list_models())
