import re
import json

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
