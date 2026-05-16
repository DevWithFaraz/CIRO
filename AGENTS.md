# CIRO — Agent Guidelines

## Project Overview
Crisis Intelligence & Response Orchestrator. 4 Gemini-powered runtime agents
that ingest multi-source crisis signals, detect emergencies, and simulate
coordinated response actions with measurable before/after city-state metrics.

## Runtime Agent Architecture
Located in `backend/agents/`:

| Agent | File | Function Signature | Output |
|-------|------|--------------------|--------|
| Signal Intelligence | `signal_intelligence.py` | `agent_signal_intelligence(db, social_reports, location, session_id, reprocessing_note=None)` | `signal_bundle` |
| Crisis Analyst | `crisis_analyst.py` | `agent_crisis_analyst(db, signal_bundle, session_id, reanalysis_note=None)` | `situation_report` |
| Response Commander | `response_commander.py` | `agent_response_commander(db, situation_report, session_id)` | `action_plan` |
| Orchestrator | `orchestrator.py` | `agent_orchestrator(db, social_reports, location, session_id)` | full pipeline result |

Also in `signal_intelligence.py` — GeoTemporal Correlation Engine:
- `count_location_matches(reports, location) -> int`
- `run_geo_temporal_correlation(social_reports, location, weather, traffic, gov_alert_exists) -> dict`

## Data Flow
```
POST /analyse
  → Orchestrator
    → Agent 1 (Signal Intelligence) → signal_bundle
    → Checkpoint 1 (Orchestrator Gemini call) → proceed or reprocess
    → Agent 2 (Crisis Analyst) → situation_report
    → Checkpoint 2 (Orchestrator Gemini call) → proceed or re-analyse
    → Agent 3 (Response Commander) → action_plan
    → City-State Simulator → city_state {before, after}
  → Return full result to client
```

## Services (`backend/services/`)
- `weather_service.py` — OpenWeatherMap integration. Field is `rain['1h']` NOT `rainfall_mm_last_hour`
- `traffic_service.py` — TomTom primary, Google Maps secondary, simulated fallback. Randomization per session
- `firebase_service.py` — Historical incident memory: `find_historical_match()`, `build_historical_context_string()`, `seed_historical_incidents()`
- `gemini_service.py` — `parse_gemini_json()` for all Gemini response parsing

## Utilities (`backend/utils.py`)
- `create_session(db, location)` — generates `sess_YYYYMMDD_HHMMSS_ffffff` session IDs
- `log_step(db, session_id, step, message)` — appends to `step_log` via `ArrayUnion`
- `log_agent_trace(db, session_id, entry)` — appends to `agent_trace` via `ArrayUnion`
- `write_before_state(db, session_id, state)` — sets `before_state` field
- `write_after_state(db, session_id, state)` — sets `after_state` field
- `update_session(db, session_id, fields)` — updates arbitrary fields

## Simulation (`backend/simulation/`)
- `city_state_simulator.py` — computes before/after numeric city-state metrics

## Coding Standards

### Parameter Passing
- `db` is passed as a parameter to every function — NEVER imported inside agent or utility files to avoid circular imports
- `db` is initialized once in `app.py` and passed down the call chain

### Firestore Writes
- Use `ArrayUnion([entry])` from `google.cloud.firestore` for array appends
- ALL Firestore writes are wrapped in silent `try/except` — print error, NEVER raise
- Collection names come from `constants.py`: `COLLECTION_SESSIONS`, `COLLECTION_HISTORICAL`

### Agent Trace (8 Required Fields)
Every `log_agent_trace()` call — both success AND error paths — must include:
1. `agent_name` — string from constants
2. `timestamp` — ISO 8601 UTC
3. `input_summary` — brief description of input
4. `output_summary` — brief description of output
5. `gemini_prompt` — truncated to 500 chars (empty string `""` on error path)
6. `gemini_response` — truncated to 500 chars (empty string `""` on error path)
7. `decision` — what the agent decided (or `"error"` on error path)
8. `status` — `"success"` or `"error"`

### Gemini Integration
- Model: `gemini-2.0-flash` (from `constants.GEMINI_MODEL`)
- ALL agents use `genai.GenerativeModel()` with explicit `system_instruction`
- ALL responses parsed via `gemini_service.parse_gemini_json()`
- Fallback on any Gemini error must return the same dict shape as the success path

### Error Handling
- Every agent function is wrapped in `try/except` at the Gemini call level
- Fallback returns a typed dict matching the success shape, never crashes the pipeline
- Weather: falls back to 87mm SEVERE simulated data
- Traffic: falls back to randomized simulated data
- Historical: returns `None` on any error

## Firebase Schema
- Collection: `crisis_sessions` — one document per analysis session
- Collection: `historical_incidents` — seeded reference data
- Field names must match PRD Section 6 exactly — never typed freehand

## React Native Rules
- Use firebase npm SDK NOT @react-native-firebase (breaks Expo Go)
- Use `getApps().length === 0` guard to prevent hot-reload crashes
- Use react-native-webview for maps NOT react-native-maps
- All colors from `mobile/CIROApp/constants/colors.js`

## Absolute Rules
- Never hardcode traffic — use `traffic_service.get_traffic_data()`
- Never use `rain['rainfall_mm_last_hour']` — correct field is `rain['1h']`
- Never skip CORS on Flask
- Never put secrets in source files
- Never initialize Firebase inside agent files — `db` comes as a parameter
- Never omit the error-path agent_trace — it must have all 8 fields
