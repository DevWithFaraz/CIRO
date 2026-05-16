---
name: Gemini Prompt Engineering
description: How to structure Gemini prompts for CIRO agents
---

# Gemini Prompt Engineering for CIRO

## System Instructions

Every CIRO agent uses a `system_instruction` when creating the `GenerativeModel`. The pattern is:

```python
model = genai.GenerativeModel(
    model_name='gemini-2.0-flash',
    system_instruction=SYSTEM_INSTRUCTION
)
response = model.generate_content(prompt)
```

### Agent 1 — Signal Intelligence
```
You are the Signal Intelligence Agent in CIRO (Crisis Intelligence &
Response Orchestrator). Your job is to process raw crisis signals and
extract structured intelligence. Return ONLY valid JSON. No markdown.
No backticks. If a field is unknown use null. Never omit a required field.
```

### Agent 2 — Crisis Analyst
```
You are the Crisis Analysis Agent in CIRO (Crisis Intelligence &
Response Orchestrator). You MUST connect ALL signal sources — social
reports, weather data, traffic data, and government alerts — in your
reasoning. Return ONLY valid JSON. No markdown. No backticks.
If a field is unknown use null. Never omit a required field.
```

### Agent 3 — Response Commander
```
You are the Response Commander Agent in CIRO. Generate coordinated
emergency response actions using real Islamabad infrastructure.
Return ONLY valid JSON. No markdown. No backticks.
```

### Orchestrator Checkpoints
```
You are the Orchestrator in CIRO. Evaluate the quality of agent output.
Return ONLY valid JSON with decision, reasoning, and guidance fields.
```

## Prompt Structure (7-Block Pattern)

All agent prompts follow this structure as an f-string:

```
1. CONTEXT HEADER
   "Analyze these crisis signals for {location}, Islamabad, Pakistan."

2. DATA SECTIONS (one per signal source)
   SOCIAL REPORTS ({len(reports)} reports):
   {numbered list}
   
   WEATHER DATA:
   {json.dumps(weather, indent=2)}
   
   TRAFFIC DATA:
   {json.dumps(traffic, indent=2)}
   
   GOVERNMENT REPORTS:
   {formatted list with [source] prefix}

3. BASELINE THRESHOLDS
   - Rainfall normal: <7mm/h | Anomaly threshold: >=7mm/h
   - Wind normal: <25km/h | Anomaly threshold: >=25km/h
   - Visibility normal: >5km | Anomaly threshold: <5km
   - Congestion normal: <30% | Anomaly threshold: >=30%
   - Traffic speed normal: 40-60km/h | Anomaly threshold: <20km/h

4. GEOTEMPORAL CORRELATION
   {json.dumps(geo_correlation, indent=2)}

5. HISTORICAL CONTEXT
   {historical_context string from firebase_service}

6. OPTIONAL GUIDANCE
   {f"REPROCESSING GUIDANCE: {note}" if note else ""}

7. JSON SCHEMA TEMPLATE
   Return this exact JSON structure:
   {{ ... }}
```

### F-String Escaping
- Use `{{ }}` for literal braces in the JSON template (Python f-string escaping)
- Use `{chr(10)}` for newlines inside f-string expressions
- Use `json.dumps(obj, indent=2)` for data sections

## JSON Schema Expectations

### Agent 1 Output (Signal Intelligence)
```json
{
  "processed_reports": [
    {
      "original_text": "exact report text",
      "language": "roman_urdu|urdu|english|mixed",
      "location_mentioned": "string or null",
      "crisis_indicators": ["list", "of", "indicators"],
      "urgency": "HIGH|MEDIUM|LOW",
      "entities": ["people", "vehicles", "infrastructure"],
      "timestamp_indicator": "time reference or null"
    }
  ],
  "cluster_analysis": {
    "primary_location": "location name",
    "location_matches": 5,
    "temporal_cluster": true,
    "cluster_score": "HIGH|MEDIUM|LOW",
    "cluster_reasoning": "explanation"
  },
  "anomalies_detected": [
    "Rainfall 87mm is 12.4x above baseline of 7mm"
  ],
  "signal_quality": "HIGH|MEDIUM|LOW",
  "quality_reasoning": "explanation"
}
```

### Agent 2 Output (Crisis Analyst)
```json
{
  "crisis_type": "flood|heatwave|accident|road_blockage|infrastructure_failure|unknown",
  "location": "G-10",
  "confidence_level": "HIGH|MEDIUM|LOW",
  "confidence_score": 85,
  "reasoning": "Multi-paragraph connecting ALL 4 sources",
  "severity": {
    "people_affected": 1200,
    "km_affected": 3.5
  },
  "impact": ["Impact statement 1", "Impact statement 2"],
  "cluster_evidence": "Evidence from clustering",
  "anomalies_found": ["Quantified anomaly string"],
  "historical_context": "Historical context string or null"
}
```

### Agent 3 Output (Response Commander)
```json
{
  "rerouting": {
    "closed_road": "road name",
    "alternate_route": "route description",
    "reasoning": "why this route",
    "route_coords": {
      "closed": [{"lat": 33.6844, "lng": 72.9857}],
      "alternate": [{"lat": 33.6910, "lng": 72.9857}]
    }
  },
  "dispatch": {
    "ticket_id": "EMR-XXXX",
    "services": ["Rescue 1122", "Fire Brigade"],
    "station": "G-9 Fire Station",
    "teams_deployed": 3,
    "vehicles": ["ambulance", "fire truck"],
    "eta_minutes": 12,
    "reasoning": "why these resources"
  },
  "alert": {
    "zones_affected": ["G-10/1", "G-10/2", "G-10/3"],
    "message": "alert text",
    "severity": "CRITICAL|HIGH|MEDIUM",
    "channels": ["SMS", "push notification", "loudspeaker", "radio"],
    "reasoning": "why this alert"
  }
}
```

### Orchestrator Checkpoint Output
```json
{
  "decision": "proceed|reprocess|re-analyse",
  "reasoning": "explanation of decision",
  "guidance_for_reprocessing": "specific instructions if reprocessing"
}
```

## Parsing Rules

1. **Always** use `gemini_service.parse_gemini_json(response.text)`
2. It handles: fenced JSON (` ```json ... ``` `), unfenced JSON, JSON with leading/trailing newlines
3. **Always** wrap the Gemini call + parse in `try/except`
4. The fallback dict must have the **same shape** as the success dict
5. Truncate `prompt[:500]` and `response.text[:500]` for agent trace entries

## Common Pitfalls

| Problem | Solution |
|---------|----------|
| Gemini returns markdown despite instructions | `parse_gemini_json()` strips ` ```json ` and ` ``` ` fences |
| Gemini omits fields | Use `.get("field", default)` for every parsed field |
| F-string braces conflict with JSON | Use `{{ }}` for literal braces |
| Newlines in f-string list comprehensions | Use `{chr(10).join(...)}` |
| Rate limiting (429) | Add `time.sleep(0.5)` between consecutive Gemini calls |
| Non-JSON output | `parse_gemini_json` raises `ValueError` — caught by agent's try/except |
