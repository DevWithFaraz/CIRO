# CIRO — Project Implementation TODO
## Crisis Intelligence & Response Orchestrator · Backend Build Checklist

> **Source of truth:** PRD.md v1.0  
> **Target:** All 10 Postman tests pass reliably before UI phase begins.

---

## PHASE 0 — Environment & Project Setup

### 0.1 Folder Structure
- [ ] Create `CIRO/` root directory
- [ ] Create empty placeholder files according to new modular structure (e.g. `backend/agents/`, `backend/services/`, etc.)
- [ ] Create `backend/requirements.txt`
- [ ] Create `backend/.env.example` and `backend/.env` (never commit)
- [ ] Create `.gitignore` covering `backend/.env`, `backend/firebase_credentials.json`, `__pycache__/`, `*.pyc`, `*.pyo`, `.venv/`, `node_modules/`, etc.
- [ ] Create `.agents/` directory with `rules/`, `skills/`, `workflows/` subdirs
- [ ] Create `mobile/CIROApp/` and `docs/` directories

### 0.2 Dependencies
- [ ] Install: `pip install flask flask-cors python-dotenv google-generativeai firebase-admin requests`
- [ ] Pin versions in `requirements.txt`

### 0.3 API Keys & Credentials
- [ ] Add `OPENWEATHER_KEY` to `.env`
- [ ] Add `GEMINI_KEY` to `.env`
- [ ] Add `GOOGLE_MAPS_KEY` to `.env` (reserved for UI)
- [ ] Add `FIREBASE_CRED_PATH=./firebase_credentials.json` to `.env`
- [ ] Add `FLASK_ENV=development` and `FLASK_PORT=5000` to `.env`
- [ ] Download Firebase service account JSON → save as `firebase_credentials.json` in project root
- [ ] **Verify OWM key:** `curl "https://api.openweathermap.org/data/2.5/weather?q=Islamabad,PK&appid=YOUR_KEY&units=metric"` — confirm `rain['1h']` field exists
- [ ] **Verify Gemini:** paste Signal Intelligence prompt into AI Studio, confirm JSON output
- [ ] **Verify Firebase:** create and read a test document from Python
- [ ] **List Gemini models** in Python: `[m.name for m in genai.list_models()]` — confirm `gemini-2.0-flash` available

---

## PHASE 1 — Foundation Modules

### 1.1 `constants.py`
- [ ] Define `COLLECTION_SESSIONS = 'crisis_sessions'`
- [ ] Define `COLLECTION_HISTORICAL = 'historical_incidents'`
- [ ] Define agent name constants: `AGENT_SIGNAL_INTEL`, `AGENT_CRISIS_ANALYST`, `AGENT_RESPONSE_COMMANDER`, `AGENT_ORCHESTRATOR`
- [ ] Define `COORDS` dict with all 6 G-10 area coordinates (G-10 Markaz, G-10/1, G-10/2, G-10/3, G-9 Markaz, G-11)
- [ ] Define `BASELINES` dict: `rainfall_normal_mmh=7`, `wind_normal_kmh=25`, `visibility_normal_km=5`, `congestion_normal_pct=30`, `traffic_speed_normal_kmh=45`
- [ ] Define `GEMINI_MODEL = 'gemini-2.0-flash'`

### 1.2 `backend/services/weather_service.py`
- [ ] Implement `classify_rain(mm: float) -> str` — returns EXTREME/SEVERE/HEAVY/MODERATE/LIGHT
- [ ] Implement `fetch_weather(location: str) -> dict`:
  - [ ] Call OWM endpoint with `q={location},PK`, `units=metric`, `timeout=5`
  - [ ] Extract `rain['1h']` (NOT `rainfall_mm_last_hour`)
  - [ ] Extract `wind.speed` → convert m/s to km/h (× 3.6)
  - [ ] Extract `visibility` → convert m to km (÷ 1000)
  - [ ] Extract `weather[0].description` and `main.humidity`
  - [ ] Set `is_fallback: False` on success
  - [ ] On any exception → return hardcoded fallback: `rainfall_mm_1h=87, alert_level='SEVERE', wind_kmh=45, visibility_km=0.8, humidity_pct=92, is_fallback=True`

### 1.3 `backend/services/traffic_service.py`
- [ ] Implement `generate_traffic_data(location: str) -> dict`:
  - [ ] `congestion_pct`: `random.randint(78, 98)`
  - [ ] `avg_speed_kmh`: `random.randint(2, 8)`
  - [ ] `normal_speed_kmh`: `45` (fixed)
  - [ ] `incidents`: `random.randint(2, 5)`
  - [ ] `data_source`: `"simulated_traffic_feed"`

### 1.4 `utils.py`
- [ ] Implement `create_session(location: str) -> str` — format: `sess_YYYYMMDD_HHMMSS_ffffff` (include microseconds to avoid collision)
- [ ] Implement `log_step(session_id, step, message)` — writes to `step_log` array via `ArrayUnion`; never raises (silent catch)
- [ ] Implement `log_agent_trace(session_id, entry: dict)` — writes to `agent_trace` via `ArrayUnion`
- [ ] Implement `write_before_state(session_id, state: dict)` — sets `before_state` field
- [ ] Implement `write_after_state(session_id, state: dict)` — sets `after_state` field
- [ ] All Firestore writes wrapped in try/except — log error, do NOT propagate exception

### 1.5 `parse_gemini_json()` (in `backend/services/gemini_service.py`)
- [ ] Strip leading/trailing whitespace
- [ ] Strip ` ```json ` and ` ``` ` fences using regex
- [ ] Call `json.loads()` and return dict
- [ ] Test against: fenced JSON, unfenced JSON, JSON with leading newline

### 1.6 `app.py` — Flask Skeleton
- [ ] Import and call `load_dotenv()`
- [ ] Configure Gemini: `genai.configure(api_key=os.getenv('GEMINI_KEY'))`
- [ ] Initialize Firebase: `credentials.Certificate(os.getenv('FIREBASE_CRED_PATH'))` → `firebase_admin.initialize_app(cred)` → `db = firestore.client()`
- [ ] Initialize Flask app with CORS: `CORS(app)`
- [ ] Implement `GET /health` → return `{"status": "ok", "version": "CIRO v1.0", "agents": [...], "subsystems": [...]}`
- [ ] **Postman Test 1:** GET /health → 200, all 4 agents listed ✓

---

## PHASE 2 — Core Agents

### 2.1 Agent 1 — Signal Intelligence (`backend/agents/signal_intelligence.py`)
- [ ] Define function signature: `agent_signal_intelligence(social_reports, location, session_id, reprocessing_note=None)`
- [ ] Step 1: Call `fetch_weather(location)` → `weather`
- [ ] Step 2: Call `generate_traffic_data(location)` → `traffic`
- [ ] Step 3: Generate `gov_reports` — 2 hardcoded realistic NDMA/news mocks with `source`, `text`, `severity`
- [ ] Step 4: Query historical incidents (call `find_historical_match` from memory.py)
- [ ] Step 5: Build Gemini prompt with all variables: `social_reports_text`, `weather_json`, `traffic_json`, `gov_reports_text`, anomaly baselines, optional `reprocessing_note`
- [ ] Set system instruction: `"You are the Signal Intelligence Agent in CIRO. Return ONLY valid JSON. No markdown. No backticks."`
- [ ] Step 6: Call `gemini-2.0-flash` → parse with `parse_gemini_json()`
- [ ] Step 7: Build and return `signal_bundle` with all required fields:
  - [ ] `processed_reports[]` — each with: `original_text`, `language`, `location_mentioned`, `crisis_indicators`, `urgency`, `entities`, `timestamp_indicator`
  - [ ] `cluster_analysis` — `primary_location`, `location_matches`, `temporal_cluster`, `cluster_score`, `cluster_reasoning`
  - [ ] `anomalies_detected[]` — quantified strings (e.g. "Rainfall 87mm is 12.4x above baseline of 7mm")
  - [ ] `signal_quality` — HIGH/MEDIUM/LOW
  - [ ] `quality_reasoning`
- [ ] Implement fallback on Gemini error: `signal_quality='LOW'`, empty `processed_reports`, fallback `cluster_score` from keyword matching
- [ ] Log `step_log` entry 1 (start) and entry 2 (complete with cluster + anomalies count)
- [ ] Log `agent_trace` entry with `agent_name`, `timestamp`, `input_summary`, `output_summary`, `gemini_prompt` (truncated 500 chars), `gemini_response` (truncated 500 chars), `decision`, `status`

### 2.2 Agent 2 — Crisis Analyst (`backend/agents/crisis_analyst.py`)
- [ ] Define function signature: `agent_crisis_analyst(signal_bundle, session_id, reanalysis_note=None)`
- [ ] Extract: `processed_reports`, `weather`, `traffic` from `signal_bundle`
- [ ] Query historical incidents → build `historical_context` string
- [ ] Append `reanalysis_note` to prompt if provided
- [ ] Set system instruction: `"You are the Crisis Analysis Agent in CIRO. You MUST connect ALL signal sources. Return ONLY valid JSON."`
- [ ] Call Gemini, parse JSON
- [ ] Required output fields in `situation_report`:
  - [ ] `crisis_type` — one of: flood/heatwave/accident/road_blockage/infrastructure_failure/unknown
  - [ ] `location`
  - [ ] `confidence_level` (HIGH/MEDIUM/LOW), `confidence_score` (0–100)
  - [ ] `reasoning` — must reference ALL 4 signal sources (social + weather + traffic + gov)
  - [ ] `severity` — `{people_affected: int, km_affected: float}`
  - [ ] `impact[]`
  - [ ] `cluster_evidence`
  - [ ] `anomalies_found[]`
  - [ ] `historical_context` — string or null
- [ ] Fallback: `{crisis_type: "unknown", confidence_level: "LOW", confidence_score: 0, reasoning: f"Analysis error: {str(e)}"}`
- [ ] Log step_log entries 3 (start) and 4 (complete with crisis_type + confidence)
- [ ] Log agent_trace entry

### 2.3 Agent 3 — Response Commander (`backend/agents/response_commander.py`)
- [ ] Define function signature: `agent_response_commander(situation_report, session_id)`
- [ ] Format situation_report fields into prompt
- [ ] Include in prompt: Islamabad resources (F-8/G-9/I-8 fire stations, PIMS/Shifa hospitals, Kohsar/Margalla police)
- [ ] Include in prompt: G-10 area coordinates (all 6 points from constants.py)
- [ ] Include alert channels: SMS, push notification, loudspeaker, radio
- [ ] Call Gemini, parse JSON
- [ ] Add ISO timestamp to each action (`rerouting`, `dispatch`, `alert`) after parsing
- [ ] Required `action_plan` structure:
  - [ ] `rerouting` — `closed_road`, `alternate_route`, `reasoning`, `timestamp`, `route_coords.closed[]`, `route_coords.alternate[]`
  - [ ] `dispatch` — `ticket_id` (format EMR-XXXX), `services[]`, `station`, `teams_deployed`, `vehicles[]`, `eta_minutes`, `reasoning`, `timestamp`
  - [ ] `alert` — `zones_affected[]`, `message`, `severity`, `channels[]`, `reasoning`, `timestamp`
- [ ] Fallback: hardcoded G-10 flood action plan with `random.randint(1000,9999)` for ticket_id
- [ ] Log step_log entries 6 (start) and 7 (complete with 3 action summaries)
- [ ] Log agent_trace entry

### 2.4 Agent 4 — Orchestrator (`backend/agents/orchestrator.py`)
- [ ] Define function signature: `agent_orchestrator(social_reports, location, session_id)`
- [ ] Log step 0: "Pipeline start, N reports for location"
- [ ] Call Agent 1 (`agent_signal_intelligence`) → `signal_bundle`
- [ ] **Checkpoint 1 — Signal Quality Evaluation:**
  - [ ] Log step 2.5
  - [ ] Build `ORCHESTRATOR_SIGNAL_EVAL_PROMPT` evaluating: all reports processed? entities/locations extracted? cluster score justified? anomalies detected? signal quality reasonable?
  - [ ] Make own Gemini call → parse `{decision, reasoning, guidance_for_reprocessing}`
  - [ ] If parse error → default `{decision: "proceed"}`
  - [ ] If `decision == "reprocess"` → log step 2.6, re-invoke Agent 1 with `reprocessing_note`, log step 2.7
- [ ] Call Agent 2 (`agent_crisis_analyst`) → `situation_report`
- [ ] **Checkpoint 2 — Analysis Quality Evaluation:**
  - [ ] Log step 5
  - [ ] Build `ORCHESTRATOR_ANALYSIS_EVAL_PROMPT` evaluating: reasoning connects all 4 sources? confidence justified? anomalies quantified? crisis_type specific? severity reasonable?
  - [ ] Make own Gemini call → parse `{decision, reasoning, guidance_for_reanalysis}`
  - [ ] If parse error → `proceed` if confidence >= 40, else `re-analyse`
  - [ ] If `decision == "re-analyse"` → log step 5.5, re-invoke Agent 2 with `reanalysis_note`, log step 5.6
- [ ] Call Agent 3 (`agent_response_commander`) → `action_plan`
- [ ] Call City-State Simulator → `city_state`
- [ ] Log step 9: "Pipeline complete"
- [ ] Return full result dict (see PRD Section 8.4 for exact shape)
- [ ] Add `time.sleep(0.5)` between each consecutive Gemini call

---

## PHASE 3 — New Subsystems

### 3.1 `backend/agents/signal_intelligence.py` (GeoTemporal Logic)
- [ ] Implement `count_location_matches(reports: list, location: str) -> int`:
  - [ ] Normalize to lowercase
  - [ ] Check variants: `loc`, `loc.replace('-',' ')`, `loc.replace(' ','-')`
  - [ ] Count reports containing any variant
- [ ] Implement `run_geo_temporal_correlation(social_reports, location, weather, traffic, gov_alert_exists=True) -> dict`:
  - [ ] Compute `nearby_reports` via `count_location_matches`
  - [ ] Compute `rainfall_mm` from `weather.get('rainfall_mm_1h', 0)`
  - [ ] Compute `congestion_pct` from `traffic.get('congestion_pct', 0)`
  - [ ] Compute `traffic_speed_drop` percentage
  - [ ] Apply confidence boost rules:
    - [ ] `nearby_reports >= 3` → +10
    - [ ] `rainfall_mm > 50` → +10
    - [ ] `congestion_pct > 80` → +5
    - [ ] `traffic_speed_drop > 70` → +5
    - [ ] `gov_alert_exists` → +10
  - [ ] Apply severity escalation table (7 rows from PRD Section 9)
  - [ ] Cap `confidence_boost` at 40
  - [ ] Return: `{report_cluster_count, time_window_minutes: 15, confidence_boost, escalated_severity, correlation_factors[]}`
- [ ] **Integration points:**
  - [ ] Call from Orchestrator BEFORE Agent 1, pass result into `signal_bundle.geo_correlation`
  - [ ] Pass GeoTemporal result as context in Agent 1 Gemini prompt
  - [ ] In Agent 2 / Checkpoint 2: if `confidence_score < geo_correlation.confidence_boost * 2` → flag for re-analysis

### 3.2 `backend/simulation/city_state_simulator.py` — City-State Simulation Engine
- [ ] Implement `build_before_state(traffic: dict, situation_report: dict) -> dict`:
  - [ ] `congestion_pct`: from `traffic['congestion_pct']`
  - [ ] `avg_speed_kmh`: from `traffic['avg_speed_kmh']`
  - [ ] `roads_blocked`: `random.randint(2, 4)`
  - [ ] `vehicles_stranded`: `random.randint(30, 55)`
  - [ ] `ambulance_eta`: `random.randint(25, 40)`
  - [ ] `citizens_at_risk`: from `situation_report.severity.people_affected` (default 1000)
  - [ ] `severity_level`: `'CRITICAL'`
  - [ ] `timestamp`: `datetime.utcnow().isoformat()`
- [ ] Implement `simulate_after_state(before: dict, action_plan: dict) -> dict`:
  - [ ] Copy `before`, update `timestamp`
  - [ ] If `rerouting` present: reduce `congestion_pct` by `random.randint(20,35)` (min 20), increase `avg_speed_kmh` by `random.randint(8,18)` (max 60), reduce `roads_blocked` by 2 (min 0)
  - [ ] If `dispatch` present: reduce `vehicles_stranded` by `random.randint(15,30)` (min 0), set `ambulance_eta` from `dispatch.eta_minutes`
  - [ ] If `alert` present: reduce `citizens_at_risk` by `random.randint(400,900)` (min 0)
  - [ ] Recalculate `severity_level`: `congestion < 35` → MEDIUM, `< 60` → HIGH, else CRITICAL
- [ ] Implement `run_city_simulation(traffic, situation_report, action_plan) -> dict` — orchestrates before/after, returns `{before, after}`
- [ ] **Integration:** Called by Orchestrator after Agent 3; result stored in Firestore as `city_state`; included in `/analyse` response

### 3.3 `backend/services/firebase_service.py` (Memory Layer)
- [ ] Implement `find_historical_match(location: str, crisis_type: str = None) -> dict | None`:
  - [ ] Query `historical_incidents` Firestore collection
  - [ ] Match on `location` (case-insensitive `in` check)
  - [ ] Optional filter on `crisis_type`
  - [ ] Return first match or `None`
  - [ ] Wrap in try/except → return `None` on any error
- [ ] Implement `build_historical_context_string(match: dict | None) -> str`:
  - [ ] If `None` → return `"No historical incidents found for this location."`
  - [ ] Else → format: `"Current pattern matches the {month} {crisis_type} at {location} (severity: {severity}, cause: {main_cause}, prior response effectiveness: {response_effectiveness}%). Roads previously affected: {roads_affected}."`
- [ ] Implement `seed_historical_incidents() -> int`:
  - [ ] Insert 3 incidents: `INC_2025_G10_001` (G-10 flood, HIGH, July), `INC_2025_I8_001` (I-8 road_blockage, MEDIUM, March), `INC_2024_F6_001` (F-6 heatwave, HIGH, June)
  - [ ] Each with all required fields including `created_at`
  - [ ] Return count of incidents inserted

---

## PHASE 4 — API Endpoints

### 4.1 `POST /analyse`
- [ ] Parse JSON body; if no body → `400 {"error": "No JSON body"}`
- [ ] Validate `location` present and non-empty after strip → `400 {"error": "Location is required"}`
- [ ] Validate `social_reports` is a list → `400 {"error": "social_reports must be a list"}`
- [ ] Filter `social_reports`: strip each item, discard empties
- [ ] If no valid reports remain → `400 {"error": "At least 1 report required"}`
- [ ] Generate `session_id` with microseconds
- [ ] Create Firestore document: `{created_at, location, status: "processing"}`
- [ ] Wrap `agent_orchestrator()` call in top-level try/except
- [ ] On success: update `status: "complete"`, return 200 with full result
- [ ] On exception: update `status: "error"`, return `500 {session_id, status: "error", error: str(e)}`

### 4.2 `GET /logs/<session_id>`
- [ ] Fetch document from `crisis_sessions/{session_id}`
- [ ] If not found → `404 {"error": "Session not found"}`
- [ ] Return full Firestore document as JSON with `200`

### 4.3 `GET /health`
- [ ] Return `200 {"status": "ok", "version": "CIRO v1.0", "agents": [...], "subsystems": [...]}`

### 4.4 `GET /historical`
- [ ] Query all docs in `historical_incidents`
- [ ] Return `200 {"incidents": [...]}`

### 4.5 `POST /seed`
- [ ] Call `seed_historical_incidents()`
- [ ] Return `200 {"status": "seeded", "count": 3}`

---

## PHASE 5 — Firebase Schema Compliance

- [ ] Confirm all `AgentTraceEntry` fields written: `agent_name`, `timestamp`, `input_summary`, `output_summary`, `gemini_prompt` (≤500 chars), `gemini_response` (≤500 chars), `decision`, `status`
- [ ] Confirm all `StepLogEntry` fields written: `step` (float), `message`, `timestamp`
- [ ] Confirm `signal_bundle` includes: `location`, `social_reports`, `weather`, `traffic`, `gov_reports`, `processed_signals`, `cluster_score`, `anomalies`, `geo_correlation`, `historical_match`
- [ ] Confirm `situation_report` includes `historical_context` field (string or null)
- [ ] Confirm `action_plan.rerouting.route_coords` has `closed[]` and `alternate[]` with `{lat, lng}` objects
- [ ] Confirm `city_state` written to Firestore with `before` and `after` nested objects
- [ ] Confirm `before_state` and `after_state` (legacy `SimState` fields) still written for compatibility
- [ ] Confirm `WeatherData.is_fallback` bool is always present
- [ ] Confirm `TrafficData.data_source = "simulated_traffic_feed"`

---

## PHASE 6 — Error Handling & Fallbacks

- [ ] OWM timeout/error → hardcoded fallback weather (87mm, SEVERE, is_fallback: true)
- [ ] Agent 1 Gemini parse error → fallback bundle with LOW quality, keyword-based cluster score
- [ ] Checkpoint 1 parse error → default `{decision: "proceed"}`
- [ ] Agent 2 Gemini parse error → `{crisis_type: "unknown", confidence_score: 0}`
- [ ] Checkpoint 2 parse error → `proceed` if confidence >= 40, else `re-analyse`
- [ ] Agent 3 Gemini parse error → hardcoded G-10 action plan, random EMR-XXXX ticket
- [ ] City Simulator error → return before_state and minimally modified after_state
- [ ] Firestore write timeout → log error, continue pipeline (don't abort)
- [ ] Historical query error → return None (no historical context)
- [ ] Every agent wrapped in try/except — no uncaught exceptions anywhere

---

## PHASE 7 — Postman Testing

Run all 10 tests in sequence. All must pass before UI phase.

- [ ] **Test 1** — GET /health → 200, all 4 agents listed, all 3 subsystems listed
- [ ] **Test 2** — POST /seed → 200, `{"status": "seeded", "count": 3}`
- [ ] **Test 3** — POST /analyse (5 G-10 flood reports) → 200; `crisis_type=flood`, `confidence_level=HIGH`, `confidence_score>=70`, all 3 action_plan keys present, `ticket_id` matches `EMR-\d{4}`, `city_state.before.congestion_pct > city_state.after.congestion_pct`
- [ ] **Test 4** — POST /analyse (1 vague report) → 200 (no crash); `confidence_score < 50`, at least one checkpoint = `reprocess` or `re-analyse`, step_log has step 2.6 or 5.5
- [ ] **Test 5** — POST /analyse (Roman Urdu + English + Urdu reports) → each `processed_report.language` correctly classified as roman_urdu/urdu/english/mixed
- [ ] **Test 6** — GET /logs/{session_id} → full Firestore doc; `agent_trace` has ≥ 5 entries; `step_log` has ≥ 9 entries; `city_state` present with before/after
- [ ] **Test 7** — POST /analyse missing location → 400 `{"error": "Location is required"}`
- [ ] **Test 8** — POST /analyse all-whitespace reports → 400 `{"error": "At least 1 report required"}`
- [ ] **Test 9** — GET /historical → 200, `incidents` array with ≥ 1 entry
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
- [ ] Confirm `signal_quality` downgrade triggers Checkpoint 1 `reprocess` decision
- [ ] Confirm low `confidence_score` triggers Checkpoint 2 `re-analyse` decision
- [ ] Confirm `historical_context` appears in `situation_report` when G-10 flood is detected

---

## PHASE 9 — `.agents/` Antigravity Artifacts

- [ ] Write `AGENTS.md` — coding standards for Antigravity build agents (model, style, error handling patterns)
- [ ] Write `skills/gemini-prompting.md` — prompt templates for all 4 agents, JSON schema expectations
- [ ] Write `skills/crisis-detection.md` — anomaly baselines, cluster logic, escalation table
- [ ] Write `workflows/test-pipeline.md` — step-by-step Postman test instructions
- [ ] Write `workflows/demo-run.md` — demo flow for judges with expected outputs

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
