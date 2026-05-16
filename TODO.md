# CIRO — Project Implementation TODO
## Crisis Intelligence & Response Orchestrator · Backend Build Checklist

> **Source of truth:** PRD.md v1.0  
> **Target:** All 10 Postman tests pass reliably before UI phase begins.

---

## PHASE 0 — Environment & Project Setup

### 0.1 Folder Structure
- [x] Create `CIRO/` root directory
- [x] Create empty placeholder files according to new modular structure (e.g. `backend/agents/`, `backend/services/`, etc.)
- [x] Create `backend/requirements.txt`
- [x] Create `backend/.env.example` and `backend/.env` (never commit)
- [x] Create `.gitignore` covering `backend/.env`, `backend/firebase_credentials.json`, `__pycache__/`, `*.pyc`, `*.pyo`, `.venv/`, `node_modules/`, etc.
- [x] Create `.agents/` directory with `rules/`, `skills/`, `workflows/` subdirs
- [x] Create `mobile/CIROApp/` and `docs/` directories

### 0.2 Dependencies
- [x] Install: `pip install flask flask-cors python-dotenv google-generativeai firebase-admin requests`
- [x] Pin versions in `requirements.txt`

### 0.3 API Keys & Credentials
- [x] Add `OPENWEATHER_KEY` to `.env`
- [x] Add `GEMINI_KEY` to `.env`
- [x] Add `GOOGLE_MAPS_KEY` to `.env` (reserved for UI)
- [x] Add `FIREBASE_CRED_PATH=./firebase_credentials.json` to `.env`
- [x] Add `FLASK_ENV=development` and `FLASK_PORT=5000` to `.env`
- [x] Download Firebase service account JSON → save as `firebase_credentials.json` in project root
- [x] **Verify OWM key:** `curl "https://api.openweathermap.org/data/2.5/weather?q=Islamabad,PK&appid=YOUR_KEY&units=metric"` — confirm `rain['1h']` field exists
- [x] **Verify Gemini:** paste Signal Intelligence prompt into AI Studio, confirm JSON output
- [x] **Verify Firebase:** create and read a test document from Python
- [x] **List Gemini models** in Python: `[m.name for m in genai.list_models()]` — confirm `gemini-2.0-flash` available

---

## PHASE 1 — Foundation Modules

### 1.1 `constants.py`
- [x] Define `COLLECTION_SESSIONS = 'crisis_sessions'`
- [x] Define `COLLECTION_HISTORICAL = 'historical_incidents'`
- [x] Define agent name constants: `AGENT_SIGNAL_INTEL`, `AGENT_CRISIS_ANALYST`, `AGENT_RESPONSE_COMMANDER`, `AGENT_ORCHESTRATOR`
- [x] Define `COORDS` dict with all 6 G-10 area coordinates (G-10 Markaz, G-10/1, G-10/2, G-10/3, G-9 Markaz, G-11)
- [x] Define `BASELINES` dict: `rainfall_normal_mmh=7`, `wind_normal_kmh=25`, `visibility_normal_km=5`, `congestion_normal_pct=30`, `traffic_speed_normal_kmh=45`
- [x] Define `GEMINI_MODEL = 'gemini-2.0-flash'`

### 1.2 `backend/services/weather_service.py`
- [x] Implement `classify_rain(mm: float) -> str` — returns EXTREME/SEVERE/HEAVY/MODERATE/LIGHT
- [x] Implement `fetch_weather(location: str) -> dict`:
  - [x] Call OWM endpoint with `q={location},PK`, `units=metric`, `timeout=5`
  - [x] Extract `rain['1h']` (NOT `rainfall_mm_last_hour`)
  - [x] Extract `wind.speed` → convert m/s to km/h (× 3.6)
  - [x] Extract `visibility` → convert m to km (÷ 1000)
  - [x] Extract `weather[0].description` and `main.humidity`
  - [x] Set `is_fallback: False` on success
  - [x] On any exception → return hardcoded fallback: `rainfall_mm_1h=87, alert_level='SEVERE', wind_kmh=45, visibility_km=0.8, humidity_pct=92, is_fallback=True`

### 1.3 `backend/services/traffic_service.py`
- [x] Implement `generate_traffic_data(location: str) -> dict`:
  - [x] `congestion_pct`: `random.randint(78, 98)`
  - [x] `avg_speed_kmh`: `random.randint(2, 8)`
  - [x] `normal_speed_kmh`: `45` (fixed)
  - [x] `incidents`: `random.randint(2, 5)`
  - [x] `data_source`: `"simulated_traffic_feed"`

### 1.4 `utils.py`
- [x] Implement `create_session(location: str) -> str` — format: `sess_YYYYMMDD_HHMMSS_ffffff` (include microseconds to avoid collision)
- [x] Implement `log_step(session_id, step, message)` — writes to `step_log` array via `ArrayUnion`; never raises (silent catch)
- [x] Implement `log_agent_trace(session_id, entry: dict)` — writes to `agent_trace` via `ArrayUnion`
- [x] Implement `write_before_state(session_id, state: dict)` — sets `before_state` field
- [x] Implement `write_after_state(session_id, state: dict)` — sets `after_state` field
- [x] All Firestore writes wrapped in try/except — log error, do NOT propagate exception

### 1.5 `parse_gemini_json()` (in `backend/services/gemini_service.py`)
- [x] Strip leading/trailing whitespace
- [x] Strip ` ```json ` and ` ``` ` fences using regex
- [x] Call `json.loads()` and return dict
- [x] Test against: fenced JSON, unfenced JSON, JSON with leading newline

### 1.6 `app.py` — Flask Skeleton
- [x] Import and call `load_dotenv()`
- [x] Configure Gemini: `genai.configure(api_key=os.getenv('GEMINI_KEY'))`
- [x] Initialize Firebase: `credentials.Certificate(os.getenv('FIREBASE_CRED_PATH'))` → `firebase_admin.initialize_app(cred)` → `db = firestore.client()`
- [x] Initialize Flask app with CORS: `CORS(app)`
- [x] Implement `GET /health` → return `{"status": "ok", "version": "CIRO v1.0", "agents": [...], "subsystems": [...]}`
- [x] **Postman Test 1:** GET /health → 200, all 4 agents listed ✓

---

## PHASE 2 — Core Agents

### 2.1 Agent 1 — Signal Intelligence (`backend/agents/signal_intelligence.py`)
- [x] Define function signature: `agent_signal_intelligence(social_reports, location, session_id, reprocessing_note=None)`
- [x] Step 1: Call `fetch_weather(location)` → `weather`
- [x] Step 2: Call `generate_traffic_data(location)` → `traffic`
- [x] Step 3: Generate `gov_reports` — 2 hardcoded realistic NDMA/news mocks with `source`, `text`, `severity`
- [x] Step 4: Query historical incidents (call `find_historical_match` from memory.py)
- [x] Step 5: Build Gemini prompt with all variables: `social_reports_text`, `weather_json`, `traffic_json`, `gov_reports_text`, anomaly baselines, optional `reprocessing_note`
- [x] Set system instruction: `"You are the Signal Intelligence Agent in CIRO. Return ONLY valid JSON. No markdown. No backticks."`
- [x] Step 6: Call `gemini-2.0-flash` → parse with `parse_gemini_json()`
- [x] Step 7: Build and return `signal_bundle` with all required fields:
  - [x] `processed_reports[]` — each with: `original_text`, `language`, `location_mentioned`, `crisis_indicators`, `urgency`, `entities`, `timestamp_indicator`
  - [x] `cluster_analysis` — `primary_location`, `location_matches`, `temporal_cluster`, `cluster_score`, `cluster_reasoning`
  - [x] `anomalies_detected[]` — quantified strings (e.g. "Rainfall 87mm is 12.4x above baseline of 7mm")
  - [x] `signal_quality` — HIGH/MEDIUM/LOW
  - [x] `quality_reasoning`
- [x] Implement fallback on Gemini error: `signal_quality='LOW'`, empty `processed_reports`, fallback `cluster_score` from keyword matching
- [x] Log `step_log` entry 1 (start) and entry 2 (complete with cluster + anomalies count)
- [x] Log `agent_trace` entry with `agent_name`, `timestamp`, `input_summary`, `output_summary`, `gemini_prompt` (truncated 500 chars), `gemini_response` (truncated 500 chars), `decision`, `status`

### 2.2 Agent 2 — Crisis Analyst (`backend/agents/crisis_analyst.py`)
- [x] Define function signature: `agent_crisis_analyst(signal_bundle, session_id, reanalysis_note=None)`
- [x] Extract: `processed_reports`, `weather`, `traffic` from `signal_bundle`
- [x] Query historical incidents → build `historical_context` string
- [x] Append `reanalysis_note` to prompt if provided
- [x] Set system instruction: `"You are the Crisis Analysis Agent in CIRO. You MUST connect ALL signal sources. Return ONLY valid JSON."`
- [x] Call Gemini, parse JSON
- [x] Required output fields in `situation_report`:
  - [x] `crisis_type` — one of: flood/heatwave/accident/road_blockage/infrastructure_failure/unknown
  - [x] `location`
  - [x] `confidence_level` (HIGH/MEDIUM/LOW), `confidence_score` (0–100)
  - [x] `reasoning` — must reference ALL 4 signal sources (social + weather + traffic + gov)
  - [x] `severity` — `{people_affected: int, km_affected: float}`
  - [x] `impact[]`
  - [x] `cluster_evidence`
  - [x] `anomalies_found[]`
  - [x] `historical_context` — string or null
- [x] Fallback: `{crisis_type: "unknown", confidence_level: "LOW", confidence_score: 0, reasoning: f"Analysis error: {str(e)}"}`
- [x] Log step_log entries 3 (start) and 4 (complete with crisis_type + confidence)
- [x] Log agent_trace entry

### 2.3 Agent 3 — Response Commander (`backend/agents/response_commander.py`)
- [x] Define function signature: `agent_response_commander(situation_report, session_id)`
- [x] Format situation_report fields into prompt
- [x] Include in prompt: Islamabad resources (F-8/G-9/I-8 fire stations, PIMS/Shifa hospitals, Kohsar/Margalla police)
- [x] Include in prompt: G-10 area coordinates (all 6 points from constants.py)
- [x] Include alert channels: SMS, push notification, loudspeaker, radio
- [x] Call Gemini, parse JSON
- [x] Add ISO timestamp to each action (`rerouting`, `dispatch`, `alert`) after parsing
- [x] Required `action_plan` structure:
  - [x] `rerouting` — `closed_road`, `alternate_route`, `reasoning`, `timestamp`, `route_coords.closed[]`, `route_coords.alternate[]`
  - [x] `dispatch` — `ticket_id` (format EMR-XXXX), `services[]`, `station`, `teams_deployed`, `vehicles[]`, `eta_minutes`, `reasoning`, `timestamp`
  - [x] `alert` — `zones_affected[]`, `message`, `severity`, `channels[]`, `reasoning`, `timestamp`
- [x] Fallback: hardcoded G-10 flood action plan with `random.randint(1000,9999)` for ticket_id
- [x] Log step_log entries 6 (start) and 7 (complete with 3 action summaries)
- [x] Log agent_trace entry

### 2.4 Agent 4 — Orchestrator (`backend/agents/orchestrator.py`)
- [x] Define function signature: `agent_orchestrator(social_reports, location, session_id)`
- [x] Log step 0: "Pipeline start, N reports for location"
- [x] Call Agent 1 (`agent_signal_intelligence`) → `signal_bundle`
- [x] **Checkpoint 1 — Signal Quality Evaluation:**
  - [x] Log step 2.5
  - [x] Build `ORCHESTRATOR_SIGNAL_EVAL_PROMPT` evaluating: all reports processed? entities/locations extracted? cluster score justified? anomalies detected? signal quality reasonable?
  - [x] Make own Gemini call → parse `{decision, reasoning, guidance_for_reprocessing}`
  - [x] If parse error → default `{decision: "proceed"}`
  - [x] If `decision == "reprocess"` → log step 2.6, re-invoke Agent 1 with `reprocessing_note`, log step 2.7
- [x] Call Agent 2 (`agent_crisis_analyst`) → `situation_report`
- [x] **Checkpoint 2 — Analysis Quality Evaluation:**
  - [x] Log step 5
  - [x] Build `ORCHESTRATOR_ANALYSIS_EVAL_PROMPT` evaluating: reasoning connects all 4 sources? confidence justified? anomalies quantified? crisis_type specific? severity reasonable?
  - [x] Make own Gemini call → parse `{decision, reasoning, guidance_for_reanalysis}`
  - [x] If parse error → `proceed` if confidence >= 40, else `re-analyse`
  - [x] If `decision == "re-analyse"` → log step 5.5, re-invoke Agent 2 with `reanalysis_note`, log step 5.6
- [x] Call Agent 3 (`agent_response_commander`) → `action_plan`
- [x] Call City-State Simulator → `city_state`
- [x] Log step 9: "Pipeline complete"
- [x] Return full result dict (see PRD Section 8.4 for exact shape)
- [x] Add `time.sleep(0.5)` between each consecutive Gemini call

---

## PHASE 3 — New Subsystems

### 3.1 `backend/agents/signal_intelligence.py` (GeoTemporal Logic)
- [x] Implement `count_location_matches(reports: list, location: str) -> int`:
  - [x] Normalize to lowercase
  - [x] Check variants: `loc`, `loc.replace('-',' ')`, `loc.replace(' ','-')`
  - [x] Count reports containing any variant
- [x] Implement `run_geo_temporal_correlation(social_reports, location, weather, traffic, gov_alert_exists=True) -> dict`:
  - [x] Compute `nearby_reports` via `count_location_matches`
  - [x] Compute `rainfall_mm` from `weather.get('rainfall_mm_1h', 0)`
  - [x] Compute `congestion_pct` from `traffic.get('congestion_pct', 0)`
  - [x] Compute `traffic_speed_drop` percentage
  - [x] Apply confidence boost rules:
    - [x] `nearby_reports >= 3` → +10
    - [x] `rainfall_mm > 50` → +10
    - [x] `congestion_pct > 80` → +5
    - [x] `traffic_speed_drop > 70` → +5
    - [x] `gov_alert_exists` → +10
  - [x] Apply severity escalation table (7 rows from PRD Section 9)
  - [x] Cap `confidence_boost` at 40
  - [x] Return: `{report_cluster_count, time_window_minutes: 15, confidence_boost, escalated_severity, correlation_factors[]}`
- [x] **Integration points:**
  - [x] Call from Orchestrator BEFORE Agent 1, pass result into `signal_bundle.geo_correlation`
  - [x] Pass GeoTemporal result as context in Agent 1 Gemini prompt
  - [x] In Agent 2 / Checkpoint 2: if `confidence_score < geo_correlation.confidence_boost * 2` → flag for re-analysis

### 3.2 `backend/simulation/city_state_simulator.py` — City-State Simulation Engine
- [x] Implement `build_before_state(traffic: dict, situation_report: dict) -> dict`:
  - [x] `congestion_pct`: from `traffic['congestion_pct']`
  - [x] `avg_speed_kmh`: from `traffic['avg_speed_kmh']`
  - [x] `roads_blocked`: hardcoded 3 (minor deviation — fixed value instead of randint)
  - [x] `vehicles_stranded`: hardcoded 42 (minor deviation — fixed value instead of randint)
  - [x] `ambulance_eta`: hardcoded 31 (minor deviation — fixed value instead of randint)
  - [x] `citizens_at_risk`: hardcoded 1200 (minor deviation — default instead of from situation_report)
  - [x] `severity_level`: `'CRITICAL'`
  - [x] `timestamp`: `datetime.utcnow().isoformat()`
- [x] Implement `simulate_after_state(before: dict, action_plan: dict) -> dict`:
  - [x] Copy `before`, update `timestamp`
  - [x] If `rerouting` present: reduce `congestion_pct` by `random.randint(20,36)`, increase `avg_speed_kmh` by `random.randint(8,18)`, reduce `roads_blocked` to 1
  - [x] If `dispatch` present: reduce `vehicles_stranded` by `random.randint(15,30)`, set `ambulance_eta` from `dispatch.eta_minutes`
  - [x] If `alert` present: reduce `citizens_at_risk` by `random.randint(400,900)` (min 0)
  - [x] Recalculate `severity_level`: `congestion < 35` → MEDIUM, `< 60` → HIGH, else CRITICAL
- [x] Implement `run_city_simulation(traffic, situation_report, action_plan) -> dict` — orchestrates before/after, returns `{before, after}`
- [x] **Integration:** Called by Orchestrator after Agent 3; result stored in Firestore as `city_state`; included in `/analyse` response

### 3.3 `backend/services/firebase_service.py` (Memory Layer)
- [x] Implement `find_historical_match(location: str, crisis_type: str = None) -> dict | None`:
  - [x] Query `historical_incidents` Firestore collection
  - [x] Match on `location` (case-insensitive `in` check)
  - [x] Optional filter on `crisis_type`
  - [x] Return first match or `None`
  - [x] Wrap in try/except → return `None` on any error
- [x] Implement `build_historical_context_string(match: dict | None) -> str`:
  - [x] If `None` → return `"No historical incidents found for this location."`
  - [x] Else → format: `"Current pattern matches the {month} {crisis_type} at {location} (severity: {severity}, cause: {main_cause}, prior response effectiveness: {response_effectiveness}%). Roads previously affected: {roads_affected}."`
- [x] Implement `seed_historical_incidents() -> int`:
  - [x] Insert 3 incidents: `INC_2025_G10_001` (G-10 flood, HIGH, July), `INC_2025_I8_001` (I-8 road_blockage, MEDIUM, March), `INC_2024_F6_001` (F-6 heatwave, HIGH, June)
  - [x] Each with all required fields including `created_at`
  - [x] Return count of incidents inserted

---

## PHASE 4 — API Endpoints

### 4.1 `POST /analyse`
- [x] Parse JSON body; if no body → `400 {"error": "No JSON body"}`
- [x] Validate `location` present and non-empty after strip → `400 {"error": "Location is required"}`
- [x] Validate `social_reports` is a list → `400 {"error": "social_reports must be a list"}`
- [x] Filter `social_reports`: strip each item, discard empties
- [x] If no valid reports remain → `400 {"error": "At least 1 report required"}`
- [x] Generate `session_id` with microseconds
- [x] Create Firestore document: `{created_at, location, status: "processing"}`
- [x] Wrap `agent_orchestrator()` call in top-level try/except
- [x] On success: update `status: "complete"`, return 200 with full result
- [x] On exception: update `status: "error"`, return `500 {session_id, status: "error", error: str(e)}`

### 4.2 `GET /logs/<session_id>`
- [x] Fetch document from `crisis_sessions/{session_id}`
- [x] If not found → `404 {"error": "Session not found"}`
- [x] Return full Firestore document as JSON with `200`

### 4.3 `GET /health`
- [x] Return `200 {"status": "ok", "version": "CIRO v1.0", "agents": [...], "subsystems": [...]}`

### 4.4 `GET /historical`
- [x] Query all docs in `historical_incidents`
- [x] Return `200 {"incidents": [...]}`

### 4.5 `POST /seed`
- [x] Call `seed_historical_incidents()`
- [x] Return `200 {"status": "seeded", "count": 3}`

---

## PHASE 5 — Firebase Schema Compliance

- [x] Confirm all `AgentTraceEntry` fields written: `agent_name`, `timestamp`, `input_summary`, `output_summary`, `gemini_prompt` (≤500 chars), `gemini_response` (≤500 chars), `decision`, `status`
- [x] Confirm all `StepLogEntry` fields written: `step` (float), `message`, `timestamp`
- [x] Confirm `signal_bundle` includes: `location`, `social_reports`, `weather`, `traffic`, `gov_reports`, `processed_signals`, `cluster_score`, `anomalies`, `geo_correlation`, `historical_match`
- [x] Confirm `situation_report` includes `historical_context` field (string or null)
- [x] Confirm `action_plan.rerouting.route_coords` has `closed[]` and `alternate[]` with `{lat, lng}` objects
- [x] Confirm `city_state` written to Firestore with `before` and `after` nested objects
- [x] Confirm `before_state` and `after_state` (legacy `SimState` fields) still written for compatibility
- [x] Confirm `WeatherData.is_fallback` bool is always present
- [x] Confirm `TrafficData.data_source = "simulated_traffic_feed"`

---

## PHASE 6 — Error Handling & Fallbacks

- [x] OWM timeout/error → hardcoded fallback weather (87mm, SEVERE, is_fallback: true)
- [x] Agent 1 Gemini parse error → fallback bundle with LOW quality, keyword-based cluster score
- [x] Checkpoint 1 parse error → default `{decision: "proceed"}`
- [x] Agent 2 Gemini parse error → `{crisis_type: "unknown", confidence_score: 0}`
- [x] Checkpoint 2 parse error → `proceed` if confidence >= 40, else `re-analyse`
- [x] Agent 3 Gemini parse error → hardcoded G-10 action plan, random EMR-XXXX ticket
- [x] City Simulator error → return before_state and minimally modified after_state
- [x] Firestore write timeout → log error, continue pipeline (don't abort)
- [x] Historical query error → return None (no historical context)
- [x] Every agent wrapped in try/except — no uncaught exceptions anywhere

---

## PHASE 7 — Postman Testing

Run all 10 tests in sequence. All must pass before UI phase.

- [x] **Test 1** — GET /health → 200, all 4 agents listed, all 3 subsystems listed
- [x] **Test 2** — POST /seed → 200, `{"status": "seeded", "count": 3}`
- [x] **Test 3** — POST /analyse (5 G-10 flood reports) → 200; `crisis_type=flood`, `confidence_level=HIGH`, `confidence_score>=70`, all 3 action_plan keys present, `ticket_id` matches `EMR-\d{4}`, `city_state.before.congestion_pct > city_state.after.congestion_pct`
- [ ] **Test 4** — POST /analyse (1 vague report) → 200 (no crash); `confidence_score < 50`, at least one checkpoint = `reprocess` or `re-analyse`, step_log has step 2.6 or 5.5
- [ ] **Test 5** — POST /analyse (Roman Urdu + English + Urdu reports) → each `processed_report.language` correctly classified as roman_urdu/urdu/english/mixed
- [ ] **Test 6** — GET /logs/{session_id} → full Firestore doc; `agent_trace` has ≥ 5 entries; `step_log` has ≥ 9 entries; `city_state` present with before/after
- [x] **Test 7** — POST /analyse missing location → 400 `{"error": "Location is required"}`
- [x] **Test 8** — POST /analyse all-whitespace reports → 400 `{"error": "At least 1 report required"}`
- [x] **Test 9** — GET /historical → 200, `incidents` array with ≥ 1 entry
- [ ] **Test 10** — POST /analyse (8 G-10 reports) → `cluster_score=HIGH`, `geo_correlation.escalated_severity` = CRITICAL or HIGH, `geo_correlation.confidence_boost >= 25`

---

## PHASE 8 — Hardening & Final Checks

- [ ] Add `time.sleep(0.5)` between every consecutive Gemini call within a single request
- [ ] Run demo 5 times consecutively — pipeline must complete reliably each time
- [ ] Pull API key temporarily → confirm OWM fallback activates (`is_fallback=true`), pipeline continues
- [ ] Feed Gemini a deliberately malformed prompt → confirm `parse_gemini_json` handles fenced and non-JSON output
- [ ] Run 3 consecutive requests → confirm `traffic.congestion_pct` and `vehicles_stranded` values differ (randomization working)
- [ ] Confirm `.gitignore` works: `git status` shows `.env` and `firebase_credentials.json` as untracked/ignored
- [ ] Session ID collision test: fire 2 simultaneous requests at the same second → confirm unique IDs (microseconds suffix)
- [x] Confirm `signal_quality` downgrade triggers Checkpoint 1 `reprocess` decision
- [ ] Confirm low `confidence_score` triggers Checkpoint 2 `re-analyse` decision
- [x] Confirm `historical_context` appears in `situation_report` when G-10 flood is detected

---

## PHASE 9 — `.agents/` Antigravity Artifacts

- [x] Write `AGENTS.md` — coding standards for Antigravity build agents (model, style, error handling patterns)
- [x] Write `skills/gemini-prompting.md` — prompt templates for all 4 agents, JSON schema expectations
- [x] Write `skills/crisis-detection.md` — anomaly baselines, cluster logic, escalation table
- [x] Write `workflows/test-pipeline.md` — step-by-step Postman test instructions
- [x] Write `workflows/demo-run.md` — demo flow for judges with expected outputs

---

## Known Risks to Watch

| Risk | Mitigation |
|------|------------|
| OWM `rain['1h']` absent on dry day | Fallback returns 87mm SEVERE — document as a design note |
| Gemini rate limit (429) during testing | `time.sleep(0.5)` between calls; max 2 req/min |
| Gemini returns non-JSON | `parse_gemini_json()` + per-agent try/except with typed fallback |
| Traffic values identical across runs | `random.randint()` on 3 fields per call — verify randomization |
| Historical incidents not seeded | Graceful `None` return — context string says "No historical incidents found" |
| Session ID collision | Microseconds suffix on session ID |
| GeoTemporal boost vs Gemini confidence inconsistency | Boost is informational context; Gemini synthesizes it |

---

*Complete all 10 Postman tests before beginning UI phase.*
