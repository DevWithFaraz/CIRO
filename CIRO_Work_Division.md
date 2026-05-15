# CIRO — Work Division Plan
**Crisis Intelligence & Response Orchestrator · Backend Sprint**

---

## Team Structure

| Role | Engineer |
|------|----------|
| **Engineer A** | Data & Intelligence Layer |
| **Engineer B** | Orchestration & Response Layer |

---

## PHASE 0 — Environment & Project Setup
> **Owner: Engineer A (Day 1)**

| Task | File / Module | Notes |
|------|---------------|-------|
| Create full folder structure | `CIRO/` root, `backend/`, `.agents/`, `mobile/`, `docs/` | Per PRD Section 14 |
| `requirements.txt` + `.env.example` | `backend/requirements.txt` | Pin all 5 packages |
| `.gitignore` | `.gitignore` | Cover `.env`, `firebase_credentials.json`, `__pycache__` |
| Verify OWM key (curl test) | — | Confirm `rain['1h']` field present |
| Verify Gemini in AI Studio | — | Paste Signal Intelligence prompt, confirm JSON |
| Verify Firebase (test doc write/read) | — | Python SDK init test |

> Eng B can start Phase 2.3 & 2.4 locally in parallel once skeleton is shared.

---

## PHASE 1 — Foundation Modules
> **Owner: Engineer A**

| Task | File / Module | Notes |
|------|---------------|-------|
| `constants.py` | `backend/constants.py` | COORDS, BASELINES, agent names, GEMINI_MODEL |
| `fetch_weather()` + `classify_rain()` | `backend/services/weather_service.py` | OWM call; fallback 87mm on error; `is_fallback` flag |
| `generate_traffic_data()` | `backend/services/traffic_service.py` | `random.randint` ranges per PRD; 3 randomised fields |
| `parse_gemini_json()` | `backend/services/gemini_service.py` | Strip all fence formats; test fenced + unfenced JSON |
| `create_session()`, `log_step()`, `log_agent_trace()` | `backend/utils.py` | ArrayUnion writes; silent catch on Firestore error |
| `write_before_state()`, `write_after_state()` | `backend/utils.py` | Legacy SimState fields for compatibility |
| Flask skeleton + `GET /health` | `backend/app.py` | CORS, Gemini init, Firebase init, `/health` route only |

---

## PHASE 2 — Core Agents

### Engineer A — Agents 1 & 2

**Agent 1 — Signal Intelligence** (`signal_intelligence.py`)
- `fetch_weather` + `generate_traffic`
- 2 gov_reports mocks (NDMA/Dawn)
- Historical match query
- Gemini call → parse `signal_bundle`
- All `ProcessedReport` fields
- `cluster_analysis` + `anomalies`
- Fallback on parse error
- `step_log` 1 & 2; `agent_trace` entry

**Agent 2 — Crisis Analyst** (`crisis_analyst.py`)
- Extract signals from `signal_bundle`
- `historical_context` string
- Gemini call → `situation_report`
- reasoning must cite all 4 sources
- Fallback: unknown / score 0
- `step_log` 3 & 4; `agent_trace` entry

### Engineer B — Agents 3 & 4

**Agent 3 — Response Commander** (`response_commander.py`)
- Situation report → Gemini prompt
- Islamabad resources in prompt
- G-10 coords in prompt
- Parse rerouting/dispatch/alert
- Add ISO timestamps post-parse
- `route_coords` with lat/lng arrays
- Fallback: hardcoded G-10 plan
- `step_log` 6 & 7; `agent_trace` entry

**Agent 4 — Orchestrator** (`orchestrator.py`)
- Owns full pipeline (step 0→9)
- Calls Agent 1 → Checkpoint 1
- Checkpoint 1: own Gemini call
- Feedback loop 1 (reprocess)
- Calls Agent 2 → Checkpoint 2
- Checkpoint 2: own Gemini call
- Feedback loop 2 (re-analyse)
- Calls Agent 3 → City Simulator
- `time.sleep(0.5)` between calls
- Returns full result dict

---

## PHASE 3 — New Subsystems

### Engineer A

**GeoTemporal Correlation Engine** (`backend/agents/signal_intelligence.py`)
- `count_location_matches()` — 3 variants
- `run_geo_temporal_correlation()`
- Confidence boost rules (5 conditions)
- Severity escalation table (7 rows)
- Cap boost at 40
- Returns `GeoCorrelationResult` dict

**Historical Incident Memory Layer** (`backend/services/firebase_service.py`)
- `find_historical_match()` — Firestore query
- `build_historical_context_string()`
- `seed_historical_incidents()` — 3 incidents
- Wrap all in `try/except` → None on error

### Engineer B

**City-State Simulation Engine** (`backend/simulation/city_state_simulator.py`)
- `build_before_state()` — 7 fields from traffic
- `simulate_after_state()` — apply 3 action effects:
  - rerouting: congestion↓, speed↑, roads↓
  - dispatch: stranded↓, eta from plan
  - alert: citizens_at_risk↓
- Recalculate `severity_level` from congestion
- `run_city_simulation()` — orchestrates both
- Returns `{before, after}` dict

---

## PHASE 4 — API Endpoints
> **Owner: Engineer B (adds to `app.py`)**

| Task | File | Notes |
|------|------|-------|
| `POST /analyse` | `backend/app.py` | Validation → session create → orchestrator → return; top-level try/except |
| `GET /logs/<id>` | `backend/app.py` | Fetch full Firestore doc; 404 if missing |
| `GET /historical` | `backend/app.py` | List all `historical_incidents` docs |
| `POST /seed` | `backend/app.py` | Call `seed_historical_incidents()`; return count |

> Eng A writes `GET /health` in Phase 1. Eng B adds the remaining 4 routes. Coordinate on imports at top of `app.py`.

---

## PHASES 5 & 6 — Schema Compliance & Error Handling
> **Owner: Both (own modules)**

| Task | File | Notes |
|------|------|-------|
| `AgentTraceEntry` all fields **(A)** | `signal_intelligence.py`, `crisis_analyst.py` | prompt ≤500 chars, status field, decision |
| `AgentTraceEntry` all fields **(B)** | `response_commander.py`, `orchestrator.py` | prompt ≤500 chars, status field, decision |
| `geo_correlation` + `historical_match` in `signal_bundle` **(A)** | `signal_intelligence.py` | Both new fields present |
| `city_state` written to Firestore **(B)** | `orchestrator.py` / `city_state_simulator.py` | before + after nested; also write legacy `before_state`/`after_state` |
| `route_coords` lat/lng arrays **(B)** | `response_commander.py` | `closed[]` and `alternate[]` with `{lat,lng}` objects |
| Fallbacks — OWM, Gemini, Firestore **(A)** | `weather_service.py`, `signal_intelligence.py`, `crisis_analyst.py` | `is_fallback` flag; silent Firestore catch |
| Fallbacks — Agents 3 & 4, Simulator **(B)** | `response_commander.py`, `orchestrator.py`, `city_state_simulator.py` | Hardcoded plan fallback; simulator error guard |

---

## PHASE 7 — Postman Testing
> **Engineer B leads, A supports**

| Test | File | Notes |
|------|------|-------|
| Tests 1–2: `/health` + `/seed` | Postman | Eng B runs; Eng A fixes any foundation issues |
| Test 3: Full pipeline (5 reports) | Postman | `crisis_type=flood`, `confidence≥70`, all 3 action keys, city_state before > after |
| Test 4: Feedback loop (1 vague report) | Postman | Confidence<50; step_log must have step 2.6 or 5.5 |
| Test 5: Multi-language classification | Postman | roman_urdu / urdu / english / mixed labels |
| Test 6: `GET /logs` session check | Postman | agent_trace ≥5 entries; step_log ≥9 entries; city_state present |
| Tests 7–8: Validation errors | Postman | 400 with correct error messages |
| Test 9: `GET /historical` | Postman | ≥1 incident after seed |
| Test 10: GeoTemporal (8 G-10 reports) | Postman | `cluster_score=HIGH`; `confidence_boost≥25` |

---

## PHASES 8 & 9 — Hardening & Antigravity Artifacts
> **Owner: Both**

| Task | File | Notes |
|------|------|-------|
| `time.sleep(0.5)` between Gemini calls **(B)** | `orchestrator.py` | Prevents 429 during rapid testing |
| OWM failure test — pull key, confirm fallback **(A)** | — | `is_fallback=true`; pipeline continues |
| Malformed Gemini output test **(A)** | `gemini_service.py` | `parse_gemini_json` handles all fence variants |
| 3× consecutive runs — confirm randomisation **(B)** | — | `congestion_pct` + `vehicles_stranded` must vary |
| 5× demo flow reliability run **(B)** | — | Pipeline must complete every time |
| `AGENTS.md` + `.agents/` rules **(A)** | `.agents/rules/ciro-standards.md` | Coding standards for Antigravity agents |
| `skills/gemini-prompting.md` **(A)** | `.agents/skills/` | Prompt templates, JSON schema expectations |
| `skills/crisis-detection.md` **(A)** | `.agents/skills/` | Baselines, cluster logic, escalation table |
| `workflows/test-pipeline.md` **(B)** | `.agents/workflows/` | Step-by-step Postman instructions |
| `workflows/demo-run.md` **(B)** | `.agents/workflows/` | Judge demo flow with expected outputs |

---

## File Ownership Summary — Zero Merge Conflicts

| Engineer A owns | Engineer B owns | Shared (coordinate) |
|-----------------|-----------------|---------------------|
| `backend/constants.py` | `backend/agents/response_commander.py` | `backend/app.py` |
| `backend/services/weather_service.py` | `backend/agents/orchestrator.py` | *(Eng A writes skeleton + `/health`. Eng B adds `/analyse`, `/logs`, `/historical`, `/seed` routes. Agree on import order before merge.)* |
| `backend/services/traffic_service.py` | `backend/simulation/city_state_simulator.py` | |
| `backend/services/gemini_service.py` | `backend/prompts/response_prompt.txt` | |
| `backend/services/firebase_service.py` | `backend/prompts/orchestrator_prompt.txt` | |
| `backend/utils.py` | `.agents/workflows/test-pipeline.md` | |
| `backend/agents/signal_intelligence.py` | `.agents/workflows/demo-run.md` | |
| `backend/agents/crisis_analyst.py` | | |
| `.agents/rules/ciro-standards.md` | | |
| `.agents/skills/gemini-prompting.md` | | |
| `.agents/skills/crisis-detection.md` | | |

---

## Day-by-Day Sprint (Days 2–5)

| Day | Engineer A | Engineer B |
|-----|------------|------------|
| **Day 2** — May 14 | Phase 0 (full setup) → Phase 1 (all foundation modules) → `/health` passing | Start Agent 3 (`response_commander.py`) locally; design city_simulator skeleton |
| **Day 3** — May 15 | Agent 1 (Signal Intelligence) → Agent 2 (Crisis Analyst) → standalone tests | Agent 4 (Orchestrator) → wire Agents 1–3 → `POST /analyse` + `GET /logs`; Test 3 |
| **Day 4** — May 16 | GeoTemporal engine → Memory Layer → `/seed` + `/historical` → integrate into Agent 1 & 2 | City-State Simulator → integrate into Orchestrator → verify city_state in Firestore |
| **Day 5** — May 17 | All 10 Postman tests; OWM failure test; Gemini bad-JSON test; `.agents/` Antigravity artifacts | All 10 Postman tests; randomisation checks; 5× demo run; `workflows/` artifacts; `requirements.txt` pin |

> `app.py` is the only shared file — agree on a single import block on Day 2 to avoid conflicts. All other files have a single owner. Both engineers run all 10 Postman tests on Day 5 independently to catch integration issues early.
