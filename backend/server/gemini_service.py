import os
import httpx
from typing import Optional, List
from dotenv import load_dotenv

# Use override=True to ensure we use the .env file key even if an OS env var exists
load_dotenv(override=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Using gemini-2.5-flash (Confirmed Working with 200 OK on new key)
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
GEMINI_STREAM_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:streamGenerateContent?alt=sse&key={GEMINI_API_KEY}"

from server.models.chat import MessageHistory

async def get_gemini_response(prompt: str, history: Optional[List[MessageHistory]] = None, image_data: Optional[str] = None, mime_type: Optional[str] = None, context: Optional[str] = None) -> Optional[str]:
    """
    Calls the Gemini API asynchronously and returns the response.
    Passes conversation history if provided.
    """
    if not GEMINI_API_KEY or "your_gemini" in GEMINI_API_KEY:
        return "Backend configuration error: Gemini API Key not set."

    headers = {
        "Content-Type": "application/json"
    }
    
    # Build contents array
    contents = []
    
    # Add history if provided
    if history:
        for msg in history:
            if isinstance(msg, dict):
                role = msg.get('role', 'user')
                text = msg.get('text', '')
            else:
                role = getattr(msg, 'role', 'user')
                text = getattr(msg, 'text', '')
                
            gemini_role = "user" if role == "user" else "model"
            contents.append({
                "role": gemini_role,
                "parts": [{"text": text}]
            })
            
    # Add current prompt and image if provided
    current_prompt = prompt
    if context:
        current_prompt = f"Use the following context to answer the user's question accurately. If the context is not relevant, answer based on your overall knowledge.\n\n[CONTEXT]:\n{context}\n\n[USER QUESTION]:\n{prompt}"
        
    parts = [{"text": current_prompt}]
    if image_data and mime_type:
        parts.append({
            "inline_data": {
                "mime_type": mime_type,
                "data": image_data
            }
        })
        
    contents.append({
        "role": "user",
        "parts": parts
    })
    
    payload = {
        "contents": contents
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(GEMINI_URL, json=payload, headers=headers, timeout=15.0)
            response.raise_for_status()
            data = response.json()
            
            # Extract the text from Gemini response structure
            try:
                answer = data["candidates"][0]["content"]["parts"][0]["text"]
                return answer
            except (KeyError, IndexError):
                return "Failed to parse response from Gemini."
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return f"Sorry, I am unable to process your request at the moment. Error: {e}"

import json

async def stream_gemini_response(prompt: str, history: Optional[List[MessageHistory]] = None, image_data: Optional[str] = None, mime_type: Optional[str] = None, context: Optional[str] = None):
    """
    Calls the Gemini streamGenerateContent API asynchronously and yields response chunks.
    """
    if not GEMINI_API_KEY or "your_gemini" in GEMINI_API_KEY:
        yield f"data: {json.dumps({'text': 'Backend configuration error: Gemini API Key not set.'})}\n\n"
        return

    headers = {
        "Content-Type": "application/json"
    }
    
    contents = []
    if history:
        for msg in history:
            if isinstance(msg, dict):
                role = msg.get('role', 'user')
                text = msg.get('text', '')
            else:
                role = getattr(msg, 'role', 'user')
                text = getattr(msg, 'text', '')
                
            gemini_role = "user" if role == "user" else "model"
            contents.append({
                "role": gemini_role,
                "parts": [{"text": text}]
            })
            
    current_prompt = prompt
    if context:
        current_prompt = f"Use the following context to answer the user's question accurately. If the context is not relevant, answer based on your overall knowledge.\n\n[CONTEXT]:\n{context}\n\n[USER QUESTION]:\n{prompt}"
        
    parts = [{"text": current_prompt}]
    if image_data and mime_type:
        parts.append({
            "inline_data": {
                "mime_type": mime_type,
                "data": image_data
            }
        })
        
    contents.append({
        "role": "user",
        "parts": parts
    })
    
    payload = {
        "contents": contents
    }

    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", GEMINI_STREAM_URL, json=payload, headers=headers, timeout=30.0) as response:
                response.raise_for_status()
                # Read SSE lines
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "":
                            continue
                        
                        try:
                            chunk_data = json.loads(data_str)
                            # Extract text chunk
                            text_chunk = chunk_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                            if text_chunk:
                                # Send chunk as JSON string in SSE format
                                yield f"data: {json.dumps({'text': text_chunk})}\n\n"
                        except json.JSONDecodeError:
                            pass
    except Exception as e:
        print(f"Error streaming from Gemini API: {e}")
        yield f"data: {json.dumps({'text': f' [Stream Error: {e}] '})}\n\n"
