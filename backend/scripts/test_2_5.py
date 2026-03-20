import os
import httpx
import asyncio
from dotenv import load_dotenv

async def test_2_5():
    key = "AIzaSyCr8YNGpdJME7b8d60NpWojc_njGLLJKp4"
    model = "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = {"contents": [{"parts": [{"text": "Say 'AURA 2.5 ONLINE'"}]}]}
    
    async with httpx.AsyncClient() as client:
        res = await client.post(url, json=payload, timeout=10.0)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            print("Response:", res.json()['candidates'][0]['content']['parts'][0]['text'])
        else:
            print("Error:", res.text)

if __name__ == "__main__":
    asyncio.run(test_2_5())
