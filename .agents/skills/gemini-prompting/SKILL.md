---
name: Gemini Prompt Engineering
description: How to structure Gemini prompts for CIRO agents
---

# Gemini Prompt Engineering

## Loading Prompts
Prompts live in backend/prompts/ and are loaded at runtime:
  with open('prompts/signal_prompt.txt', 'r') as f:
      SIGNAL_PROMPT = f.read()

## Rules
- Every prompt ends with: Return ONLY valid JSON. No markdown. No explanation.
- Use {{ }} for JSON template fields in Python f-strings
- Define exact JSON schema the agent must return inside the prompt
- Include anomaly baselines when anomaly detection is needed
- Include escalation thresholds when cluster scoring is involved

## Parsing
Always use gemini_service.parse_gemini_json() — handles all fence formats.
Wrap in try/except — fallback must return the same shape as success response.
