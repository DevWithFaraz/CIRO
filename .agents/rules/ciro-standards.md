---
name: CIRO Coding Standards
description: Always-active coding standards for the CIRO project
alwaysApply: true
---

# Standards
- Flask backend with flask-cors configured before any route
- Gemini prompts loaded from backend/prompts/*.txt files at runtime
- All prompts end with: Return ONLY valid JSON. No markdown. No explanation.
- Double curly braces {{ }} for JSON fields inside Python f-strings
- parse_gemini_json() for all Gemini response parsing
- try/except on every Gemini call, OWM call, and Firebase write
- Firebase field names from constants.py only
