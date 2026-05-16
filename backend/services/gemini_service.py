import os
import re
import json
from google import genai

# Initialize client once — agents import this
client = genai.Client(api_key=os.getenv('GEMINI_KEY'))

def parse_gemini_json(text: str) -> dict:
    text = text.strip()
    
    # Use re.sub to remove ```json and ``` fences (handle both formats)
    text = re.sub(r'^```json\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    
    # Strip again after fence removal
    text = text.strip()
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise ValueError(f"Gemini returned non-JSON: {text[:200]}")
