import os
import re
import json
from google import genai
from google.genai import types
from constants import GEMINI_MODEL

_client = None

def get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv('GEMINI_KEY'))
    return _client

def parse_gemini_json(text: str) -> dict:
    text = text.strip()

    text = re.sub(r'^```json\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'\s*```$', '', text)

    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise ValueError(f"Gemini returned non-JSON: {text[:200]}")

def generate_content(prompt: str, system_instruction: str = None) -> str:
    """Call Gemini and return raw text response."""
    client = get_client()
    config = None
    if system_instruction:
        config = types.GenerateContentConfig(
            system_instruction=system_instruction
        )
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=config
    )
    return response.text
