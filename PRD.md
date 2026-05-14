# CIRO — Product Requirements Document
## Crisis Intelligence & Response Orchestrator
### Backend Engineering Reference · v1.0

> **Scope of this document:** Backend only — Python/Flask, all 4 AI agents, all integrations, all subsystems.
> Frontend/UI is a separate phase. This PRD is the authoritative source for everything testable via Postman.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Scoring Context](#2-scoring-context)
3. [System Architecture](#3-system-architecture)
4. [Tech Stack & Dependencies](#4-tech-stack--dependencies)
5. [Environment & Configuration](#5-environment--configuration)
6. [Firebase Data Schema](#6-firebase-data-schema)
7. [API Endpoints](#7-api-endpoints)
8. [Agent Specifications](#8-agent-specifications)
9. [Subsystem: GeoTemporal Correlation Engine](#9-subsystem-geotemporal-correlation-engine)
10. [Subsystem: City-State Simulation Engine](#10-subsystem-city-state-simulation-engine)
11. [Subsystem: Historical Incident Memory Layer](#11-subsystem-historical-incident-memory-layer)
12. [External Integrations](#12-external-integrations)
13. [Error Handling & Fallback Strategy](#13-error-handling--fallback-strategy)
14. [File & Module Structure](#14-file--module-structure)
15. [Postman Testing Guide](#15-postman-testing-guide)
16. [Backend Build Plan (Day-by-Day)](#16-backend-build-plan-day-by-day)
17. [Known Risks & Mitigations](#17-known-risks--mitigations)

---

## 1. Project Overview

**CIRO (Crisis Intelligence & Response Orchestrator)** is an autonomous, real-time emergency coordination platform for Pakistani urban crises. It ingests multi-source signals — social media reports (Roman Urdu, Urdu, English), live weather data, dynamic traffic feeds, and government advisories — processes them through a chain of four Gemini-powered AI agents, and produces a coordinated emergency response plan with simulated city-state recovery outcomes.

### Primary Scenario
**G-10 Islamabad urban flooding** — waterlogging, road blockages, stranded vehicles, drainage overflow. This is the default demo scenario but the system is designed to handle: flood, heatwave, accident, road_blockage, infrastructure_failure.

### What Makes CIRO Technically Distinct
- **4 Gemini 2.0 Flash agents**, every one makes its own AI call — not helper wrappers
- **Orchestrator with TWO evaluation feedback loops** — genuine agent-to-agent interaction, not a sequential pipeline
- **GeoTemporal Correlation Engine** — synthesizes evidence across location clusters, time windows, and cross-source validation to compute dynamic confidence boost
- **City-State Simulation Engine** — produces measurable before/after city metrics (congestion %, ETA, vehicles stranded) after response is planned
- **Historical Incident Memory Layer** — agents compare current events to past incidents stored in Firestore; contextual reasoning, not just reactive analysis
- **4 signal sources**: social (multi-language), weather (live OpenWeatherMap), traffic (randomized simulation), government/news (realistic mocks)

---

## 2. Scoring Context

The backend must be built to satisfy these scoring criteria. Every subsystem in this PRD maps to at least one criterion.

| Criterion | Weight | Backend Contribution |
|-----------|--------|----------------------|
| Antigravity Usage | 25% | AGENTS.md, Skills, Workflows, Plan Mode artifacts |
| Agentic Reasoning | 20% | 4 Gemini agents, Orchestrator with 2 checkpoints, agent_trace in Firestore |
| Situation Detection | 20% | GeoTemporal correlation, cluster analysis, anomaly detection against baselines |
| Action Simulation | 15% | before_state/after_state, City-State Simulator, action_plan with coords |
| Technical Implementation | 10% | Input validation, try/except everywhere, fallbacks, .env, CORS |
| Innovation & UX | 10% | Roman Urdu handling, Historical Memory, dynamic confidence escalation |

---

## 3. System Architecture

### 3.1 Runtime Flow (Complete)

```
POST /analyse
       │
       ▼
  [INPUT VALIDATION]
  - Require location (string)
  - Require social_reports (non-empty list)
  - Strip whitespace, reject empties
       │
       ▼
  [GEOTEMPORAL CORRELATION ENGINE]   ← NEW SUBSYSTEM
  - Cluster nearby reports (1.2km radius)
  - Check temporal clustering (10–15 min window)
  - Cross-validate: weather intensity + traffic collapse + gov alerts
  - Compute confidence_boost, escalated severity
       │
       ▼
  [ORCHESTRATOR AGENT]  ← Master agent, owns entire pipeline
       │
       ├──► [SIGNAL INTELLIGENCE AGENT]
       │     - Fetch real weather (OpenWeatherMap)
       │     - Generate dynamic traffic data
       │     - Query historical incidents (Firestore)   ← NEW
       │     - Gemini: process reports, cluster, detect anomalies
       │     Output: signal_bundle
       │
       ├──► [CHECKPOINT 1] Orchestrator evaluates signal quality
       │     Own Gemini call: "Are signals structured? Cluster justified?"
       │     If LOW → FEEDBACK LOOP 1: re-invoke Agent 1 with guidance
       │
       ├──► [CRISIS ANALYST AGENT]
       │     - Compare to historical incidents         ← NEW
       │     - Gemini: infer crisis type, severity, confidence
       │     Output: situation_report
       │
       ├──► [CHECKPOINT 2] Orchestrator evaluates analysis quality
       │     Own Gemini call: "Is confidence justified? Multi-source reasoning?"
       │     If LOW → FEEDBACK LOOP 2: re-invoke Agent 2 with guidance
       │
       ├──► [RESPONSE COMMANDER AGENT]
       │     - Gemini: generate 3 coordinated actions (reroute + dispatch + alert)
       │     - Real Islamabad coordinates for routes
       │     Output: action_plan
       │
       ├──► [CITY-STATE SIMULATION ENGINE]            ← NEW SUBSYSTEM
       │     - Apply action_plan to before_state
       │     - Compute after_state metrics
       │     - Write before_state + after_state to Firestore
       │
       └──► Return execution_log to caller

Total Gemini calls: 5–7 per request (up to 9 if both feedback loops trigger)
```

### 3.2 Agent Interaction Diagram

```
                    ┌─────────────────────────────────────┐
                    │         ORCHESTRATOR AGENT           │
                    │  (Master — owns pipeline decisions)  │
                    └────────────┬──────────────────┬──────┘
                                 │                  │
              FEEDBACK LOOP 1    │                  │    FEEDBACK LOOP 2
                    ┌────────────▼──────┐    ┌──────▼────────────┐
                    │ SIGNAL INTEL AGENT│    │ CRISIS ANALYST    │
                    │  (Gemini call #1) │    │  (Gemini call #3) │
                    └────────────┬──────┘    └──────┬────────────┘
                                 │  signal_bundle   │  situation_report
                    ┌────────────▼──────────────────▼────────────┐
                    │         RESPONSE COMMANDER AGENT            │
                    │            (Gemini call #5)                 │
                    └─────────────────────────────────────────────┘
                                         │  action_plan
                    ┌────────────────────▼──────────────────────┐
                    │         CITY-STATE SIMULATOR               │
                    │  (computes before/after city metrics)      │
                    └────────────────────────────────────────────┘
```

---

## 4. Tech Stack & Dependencies

| Dependency | Version | Role |
|-----------|---------|------|
| Python | 3.11 | Runtime |
| Flask | 3.x | HTTP server + API routes |
| flask-cors | latest | CORS headers for all routes |
| google-generativeai | latest | Gemini 2.0 Flash calls for all 4 agents |
| firebase-admin | latest | Firestore writes (server-side SDK) |
| requests | latest | OpenWeatherMap HTTP calls |
| python-dotenv | latest | .env loading, no hardcoded keys |
| random / datetime | stdlib | Traffic generation, session IDs, timestamps |
| re / json | stdlib | Gemini response parsing |

### Install Command

```bash
pip install flask flask-cors python-dotenv google-generativeai firebase-admin requests
```

---

## 5. Environment & Configuration

### 5.1 .env File (Flask root)

```bash
OPENWEATHER_KEY=your_openweathermap_api_key
GEMINI_KEY=your_gemini_api_key
GOOGLE_MAPS_KEY=your_google_maps_key        # reserved for UI phase
FIREBASE_CRED_PATH=./firebase_credentials.json
FLASK_ENV=development
FLASK_PORT=5000
```

### 5.2 .gitignore

```
.env
firebase_credentials.json
__pycache__/
*.pyc
*.pyo
```

### 5.3 Firebase Credentials

Download from: Firebase Console → Project Settings → Service Accounts → Generate New Private Key

Save as `firebase_credentials.json` in the project root. Never commit this file.

### 5.4 API Keys Reference

| Key | Source | Free Tier |
|-----|--------|-----------|
| OPENWEATHER_KEY | openweathermap.org → API keys | 60 calls/min, 1000/day |
| GEMINI_KEY | aistudio.google.com | Free with Google Cloud credits |
| GOOGLE_MAPS_KEY | console.cloud.google.com → Credentials | Covered by hackathon credits |
| FIREBASE_CRED | Firebase Console → Service account JSON | Unlimited on Spark plan |

### 5.5 Initialization in app.py

```python
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import google.generativeai as genai

load_dotenv()

# Gemini init
genai.configure(api_key=os.getenv('GEMINI_KEY'))

# Firebase init
cred = credentials.Certificate(os.getenv('FIREBASE_CRED_PATH'))
firebase_admin.initialize_app(cred)
db = firestore.client()

OPENWEATHER_KEY = os.getenv('OPENWEATHER_KEY')
```

### 5.6 Day 1 Verification Checklist

Run these before writing any agent code:

```bash
# 1. Test OpenWeatherMap — must see rain['1h'] field
curl "https://api.openweathermap.org/data/2.5/weather?q=Islamabad,PK&appid=YOUR_KEY&units=metric"

# 2. Test Gemini — paste Signal Intelligence prompt into AI Studio, verify JSON output

# 3. Test Firebase — create and read a test document from Python

# 4. List available Gemini models
# In Python: [m.name for m in genai.list_models()]
# Use: gemini-2.0-flash
```

---

## 6. Firebase Data Schema

**Lock this schema before writing any code.** All agents write to the same document — field name inconsistencies cause silent data loss.

```
Firestore Collection: crisis_sessions
Document ID:          {session_id}   (format: sess_YYYYMMDD_HHMMSS)

Root fields:
─────────────────────────────────────────────────────────────────
created_at              : string (ISO 8601 UTC)
location                : string
status                  : "processing" | "complete" | "error"

agent_trace             : array<AgentTraceEntry>
step_log                : array<StepLogEntry>

signal_bundle           : SignalBundle
situation_report        : SituationReport
action_plan             : ActionPlan
city_state              : CityState              ← NEW (Simulator output)

before_state            : SimState
after_state             : SimState
─────────────────────────────────────────────────────────────────

AgentTraceEntry:
  agent_name            : "signal_intelligence" | "crisis_analyst"
                          | "response_commander" | "orchestrator"
  timestamp             : string (ISO)
  input_summary         : string
  output_summary        : string
  gemini_prompt         : string (truncated to 500 chars)
  gemini_response       : string (truncated to 500 chars)
  decision              : string
  status                : "success" | "error" | "re-analysis" | "reprocess"

StepLogEntry:
  step                  : float (e.g. 0, 1, 2.5, 2.6)
  message               : string
  timestamp             : string (ISO)

SignalBundle:
  location              : string
  social_reports        : array<ProcessedReport>
  weather               : WeatherData
  traffic               : TrafficData
  gov_reports           : array<GovReport>
  processed_signals     : GeminiSignalOutput
  cluster_score         : "HIGH" | "MEDIUM" | "LOW"
  anomalies             : array<string>
  geo_correlation       : GeoCorrelationResult     ← NEW
  historical_match      : HistoricalIncident | null ← NEW

ProcessedReport:
  original_text         : string
  language              : "roman_urdu" | "urdu" | "english" | "mixed"
  location_mentioned    : string | null
  crisis_indicators     : array<string>
  urgency               : "HIGH" | "MEDIUM" | "LOW"
  entities              : array<string>
  timestamp_indicator   : string | null

WeatherData:
  location              : string
  rainfall_mm_1h        : float       ← CORRECT field from OWM rain['1h']
  alert_level           : "EXTREME" | "SEVERE" | "HEAVY" | "MODERATE" | "LIGHT"
  wind_kmh              : float
  visibility_km         : float
  description           : string
  humidity_pct          : int
  is_fallback           : bool        ← true if OWM call failed

TrafficData:
  location              : string
  congestion_pct        : int         (randomized 78–98 for crisis scenario)
  avg_speed_kmh         : int         (randomized 2–8)
  normal_speed_kmh      : int         (45, fixed)
  incidents             : int         (randomized 2–5)
  data_source           : "simulated_traffic_feed"

GovReport:
  source                : string      (e.g. "NDMA Advisory", "Dawn News")
  text                  : string
  severity              : "HIGH" | "MODERATE" | "LOW"

GeoCorrelationResult:                               ← NEW
  report_cluster_count  : int
  time_window_minutes   : int
  confidence_boost      : int
  escalated_severity    : "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
  correlation_factors   : array<string>

HistoricalIncident:                                 ← NEW
  incident_id           : string
  location              : string
  crisis_type           : string
  month                 : string
  severity              : string
  main_cause            : string
  response_effectiveness: int
  roads_affected        : array<string>

SituationReport:
  crisis_type           : "flood" | "heatwave" | "accident"
                          | "road_blockage" | "infrastructure_failure" | "unknown"
  location              : string
  confidence_level      : "HIGH" | "MEDIUM" | "LOW"
  confidence_score      : int (0–100)
  reasoning             : string (must reference ALL 4 signal sources)
  severity              : { people_affected: int, km_affected: float }
  impact                : array<string>
  cluster_evidence      : string
  anomalies_found       : array<string>
  historical_context    : string | null              ← NEW

ActionPlan:
  rerouting:
    closed_road         : string
    alternate_route     : string
    reasoning           : string
    timestamp           : string (ISO)
    route_coords:
      closed            : array<{ lat: float, lng: float }>
      alternate         : array<{ lat: float, lng: float }>
  dispatch:
    ticket_id           : string (format: EMR-XXXX)
    services            : array<string>
    station             : string
    teams_deployed      : int
    vehicles            : array<string>
    eta_minutes         : int
    reasoning           : string
    timestamp           : string (ISO)
  alert:
    zones_affected      : array<string>
    message             : string
    severity            : "CRITICAL" | "HIGH" | "MEDIUM"
    channels            : array<string>
    reasoning           : string
    timestamp           : string (ISO)

CityState (NEW — from City-State Simulator):
  before:
    congestion_pct      : int
    avg_speed_kmh       : int
    roads_blocked       : int
    vehicles_stranded   : int
    ambulance_eta       : int
    citizens_at_risk    : int
    severity_level      : string
    timestamp           : string (ISO)
  after:
    congestion_pct      : int
    avg_speed_kmh       : int
    roads_blocked       : int
    vehicles_stranded   : int
    ambulance_eta       : int
    citizens_at_risk    : int
    severity_level      : string
    timestamp           : string (ISO)

SimState (legacy before_state / after_state fields — keep for compatibility):
  crisis_active         : bool
  response_status       : string
  roads_status          : string
  emergency_teams_deployed: int
  alerts_sent           : int
  actions_executed      : array<string>  (only in after_state)
  timestamp             : string (ISO)
```

### Historical Incidents Collection

```
Firestore Collection: historical_incidents
Document ID:          {incident_id}

Fields:
  incident_id           : string
  location              : string
  crisis_type           : string
  month                 : string
  severity              : string
  main_cause            : string
  response_effectiveness: int (0–100)
  roads_affected        : array<string>
  created_at            : string (ISO)
```

Seed data (insert on first run or via a `/seed` endpoint):

```json
{
  "incident_id": "INC_2025_G10_001",
  "location": "G-10",
  "crisis_type": "flood",
  "month": "July",
  "severity": "HIGH",
  "main_cause": "drainage overflow",
  "response_effectiveness": 72,
  "roads_affected": ["G-10 Main Boulevard", "Service Road East"]
}
```

---

## 7. API Endpoints

### 7.1 POST /analyse

**Purpose:** Run the full 4-agent pipeline. This is the primary endpoint.

**Request Body (JSON):**

```json
{
  "location": "G-10",
  "social_reports": [
    "G-10 mein pani bhar gaya hai, gaariyan phans gayi hain",
    "Cars trapped near G-10 markaz, road fully blocked",
    "Severe flooding on G-10 main boulevard, avoid the area",
    "G-10 mein baarish ki wajah se traffic jam hai",
    "Water level rising fast at G-10/2, people stuck"
  ]
}
```

**Validation Rules:**

| Field | Type | Rule |
|-------|------|------|
| location | string | Required, non-empty after strip |
| social_reports | array | Required, must be a list |
| social_reports items | string | Each item non-empty after strip; empty strings discarded |
| social_reports (after filtering) | array | Must have at least 1 valid report |

**Success Response (200):**

```json
{
  "session_id": "sess_20260514_212345",
  "situation_report": {
    "crisis_type": "flood",
    "location": "G-10, Islamabad",
    "confidence_level": "HIGH",
    "confidence_score": 91,
    "reasoning": "Multiple Roman Urdu and English reports confirm severe flooding at G-10...",
    "severity": { "people_affected": 1200, "km_affected": 3.5 },
    "impact": ["Road blockage on main boulevard", "Vehicles stranded", "Drainage overflow"],
    "cluster_evidence": "12 reports within 1.2km radius, all within 14-minute window",
    "anomalies_found": [
      "Rainfall 87mm is 12.4x above Islamabad baseline of 7mm",
      "Traffic speed 4km/h is 91% below normal 45km/h"
    ],
    "historical_context": "Pattern matches July 2025 G-10 incident (drainage overflow, HIGH severity)"
  },
  "action_plan": {
    "rerouting": {
      "closed_road": "G-10 Main Boulevard",
      "alternate_route": "G-9/G-11 connector via Nazimuddin Road",
      "reasoning": "...",
      "timestamp": "2026-05-14T21:23:50Z",
      "route_coords": {
        "closed": [{"lat": 33.6844, "lng": 72.9857}, {"lat": 33.6807, "lng": 72.9741}],
        "alternate": [{"lat": 33.6910, "lng": 72.9857}, {"lat": 33.6807, "lng": 72.9741}]
      }
    },
    "dispatch": {
      "ticket_id": "EMR-4821",
      "services": ["rescue", "medical"],
      "station": "F-8 Fire Station",
      "teams_deployed": 3,
      "vehicles": ["rescue boat", "ambulance", "pump truck"],
      "eta_minutes": 12,
      "reasoning": "...",
      "timestamp": "2026-05-14T21:23:52Z"
    },
    "alert": {
      "zones_affected": ["G-10", "G-9", "G-11"],
      "message": "FLOOD ALERT: Avoid G-10 Main Boulevard. Use G-9/G-11 alternate routes.",
      "severity": "CRITICAL",
      "channels": ["SMS", "push", "loudspeaker"],
      "reasoning": "...",
      "timestamp": "2026-05-14T21:23:53Z"
    }
  },
  "city_state": {
    "before": {
      "congestion_pct": 94,
      "avg_speed_kmh": 4,
      "roads_blocked": 3,
      "vehicles_stranded": 42,
      "ambulance_eta": 31,
      "citizens_at_risk": 1200,
      "severity_level": "CRITICAL"
    },
    "after": {
      "congestion_pct": 58,
      "avg_speed_kmh": 18,
      "roads_blocked": 1,
      "vehicles_stranded": 9,
      "ambulance_eta": 12,
      "citizens_at_risk": 320,
      "severity_level": "HIGH"
    }
  },
  "orchestrator_evaluations": {
    "signal_checkpoint": {
      "decision": "proceed",
      "reasoning": "Signal quality HIGH, all reports processed, cluster justified"
    },
    "analysis_checkpoint": {
      "decision": "proceed",
      "reasoning": "Confidence 91% justified by multi-source evidence"
    }
  },
  "signal_bundle_summary": {
    "cluster_score": "HIGH",
    "anomalies_count": 3,
    "signal_quality": "HIGH"
  }
}
```

**Error Responses:**

| Condition | HTTP | Body |
|-----------|------|------|
| No JSON body | 400 | `{"error": "No JSON body"}` |
| Missing location | 400 | `{"error": "Location is required"}` |
| social_reports not a list | 400 | `{"error": "social_reports must be a list"}` |
| All reports empty after strip | 400 | `{"error": "At least 1 report required"}` |
| Pipeline exception | 500 | `{"session_id": "...", "status": "error", "error": "..."}` |

---

### 7.2 GET /logs/{session_id}

**Purpose:** Retrieve complete agent trace and all Firestore data for a session.

**Response (200):**

Full Firestore document as JSON — all fields described in Section 6.

**Error (404):**

```json
{"error": "Session not found"}
```

---

### 7.3 GET /health

**Purpose:** Service liveness check and agent manifest.

**Response (200):**

```json
{
  "status": "ok",
  "version": "CIRO v1.0",
  "agents": [
    "signal_intelligence",
    "crisis_analyst",
    "response_commander",
    "orchestrator"
  ],
  "subsystems": [
    "geotemporal_correlation_engine",
    "city_state_simulator",
    "historical_incident_memory"
  ]
}
```

---

### 7.4 GET /historical

**Purpose:** List all historical incidents (for debugging and Memory Layer verification).

**Response (200):**

```json
{
  "incidents": [
    {
      "incident_id": "INC_2025_G10_001",
      "location": "G-10",
      "crisis_type": "flood",
      ...
    }
  ]
}
```

---

### 7.5 POST /seed

**Purpose:** Seed Firestore with test historical incidents. Run once on fresh deployment.

**Response (200):**

```json
{"status": "seeded", "count": 3}
```

---

## 8. Agent Specifications

All agents use `gemini-2.0-flash`. All agents: (a) log to `step_log`, (b) log to `agent_trace`, (c) have try/except with fallback return values. No agent should ever raise an uncaught exception.

---

### 8.1 Agent 1 — Signal Intelligence Agent

**Function:** `agent_signal_intelligence(social_reports, location, session_id, reprocessing_note=None)`

**Steps:**
1. Call `fetch_weather(location)` → real OWM data
2. Call `generate_traffic_data(location)` → randomized crisis traffic
3. Generate `gov_reports` → 2 realistic NDMA/news mocks
4. Query `historical_incidents` → find matching location/type for context
5. Call Gemini with full prompt
6. Parse JSON response with `parse_gemini_json()`
7. Build and return `signal_bundle`

**Gemini Model:** `gemini-2.0-flash` with system_instruction

**System Instruction:**
```
You are the Signal Intelligence Agent in CIRO.
Your job: process raw crisis signals and extract structured data.
Return ONLY valid JSON. No markdown. No backticks.
If a field is unknown, use null. Never omit a field.
```

**Prompt Variables:** social_reports_text, weather_json, traffic_json, gov_reports_text, (optional) reprocessing_note

**Required Output Fields:**
- `processed_reports[]` — each with: original_text, language, location_mentioned, crisis_indicators, urgency, entities, timestamp_indicator
- `cluster_analysis` — primary_location, location_matches, temporal_cluster, cluster_score (HIGH/MEDIUM/LOW), cluster_reasoning
- `anomalies_detected[]` — quantified strings ("Rainfall 87mm is 12.4x above baseline of 7mm")
- `signal_quality` — HIGH / MEDIUM / LOW
- `quality_reasoning` — string

**Anomaly Baselines (baked into prompt):**

| Signal | Normal Baseline | Anomaly Threshold |
|--------|----------------|-------------------|
| Rainfall | < 7 mm/h | ≥ 7 mm/h |
| Wind | < 25 km/h | ≥ 25 km/h |
| Visibility | > 5 km | < 5 km |
| Congestion | < 30% | ≥ 30% |
| Traffic speed | 40–60 km/h | < 20 km/h |

**Fallback (Gemini fails):**
```python
{
  "processed_reports": [],
  "cluster_analysis": {
    "cluster_score": fallback_cluster_score(social_reports, location),
    ...
  },
  "anomalies_detected": [],
  "signal_quality": "LOW",
  "quality_reasoning": f"Gemini parse error: {str(e)}"
}
```

**step_log entries:** 1 (start), 2 (complete with cluster + anomalies count)

---

### 8.2 Agent 2 — Crisis Analyst Agent

**Function:** `agent_crisis_analyst(signal_bundle, session_id, reanalysis_note=None)`

**Steps:**
1. Extract processed reports, weather, traffic from `signal_bundle`
2. Query historical incidents for context (produce `historical_context` string)
3. Append `reanalysis_note` to prompt if provided
4. Call Gemini
5. Return `situation_report`

**System Instruction:**
```
You are the Crisis Analysis Agent in CIRO.
You MUST connect ALL signal sources in your reasoning — social, weather, traffic, AND government.
crisis_type must be one of: flood | heatwave | accident | road_blockage | infrastructure_failure | unknown
Return ONLY valid JSON. No markdown. No backticks.
```

**Required Output Fields:**
- `crisis_type`, `location`
- `confidence_level` (HIGH/MEDIUM/LOW), `confidence_score` (0–100)
- `reasoning` — 2–3 sentences, MUST reference all 4 signal sources
- `severity` — `{ people_affected, km_affected }`
- `impact[]`
- `cluster_evidence`
- `anomalies_found[]`
- `historical_context` — string or null

**Fallback:**
```python
{
  "crisis_type": "unknown",
  "confidence_level": "LOW",
  "confidence_score": 0,
  "reasoning": f"Analysis error: {str(e)}",
  ...
}
```

**step_log entries:** 3 (start), 4 (complete with crisis_type + confidence)

---

### 8.3 Agent 3 — Response Commander Agent

**Function:** `agent_response_commander(situation_report, session_id)`

**Steps:**
1. Format situation_report fields into prompt
2. Call Gemini
3. Add `timestamp` to each of the 3 actions
4. Return `action_plan`

**Islamabad Resources Available (in prompt):**

| Resource Type | Locations |
|---------------|-----------|
| Fire Stations | F-8, G-9, I-8 |
| Hospitals | PIMS (G-8), Shifa (H-8) |
| Police | Kohsar (F-6), Margalla (E-7) |
| Alert Channels | SMS, push notification, loudspeaker, radio |

**G-10 Area Coordinates (in prompt):**

| Point | Lat | Lng |
|-------|-----|-----|
| G-10 Markaz | 33.6844 | 72.9857 |
| G-10/1 | 33.6831 | 72.9812 |
| G-10/2 | 33.6820 | 72.9778 |
| G-10/3 | 33.6807 | 72.9741 |
| G-9 Markaz | 33.6910 | 72.9857 |
| G-11 | 33.6865 | 72.9741 |

**Required Output:** `{ rerouting, dispatch, alert }` (see schema in Section 6)

**Fallback:** Hardcoded G-10 flood response plan with randomized ticket_id (EMR-XXXX)

**step_log entries:** 6 (start), 7 (complete with 3 action summaries)

---

### 8.4 Agent 4 — Orchestrator Agent (Master)

**Function:** `agent_orchestrator(social_reports, location, session_id)`

**This agent owns the entire pipeline.** It makes its own Gemini calls at two evaluation checkpoints.

**Checkpoint 1 — Signal Quality Evaluation:**

Evaluates `signal_bundle` from Agent 1. Own Gemini call with `ORCHESTRATOR_SIGNAL_EVAL_PROMPT`.

Output JSON: `{ "decision": "proceed|reprocess", "reasoning": "...", "guidance_for_reprocessing": "..." }`

If `decision == "reprocess"` → re-invoke Agent 1 with `guidance_for_reprocessing` as `reprocessing_note`.

**Checkpoint 2 — Analysis Quality Evaluation:**

Evaluates `situation_report` from Agent 2. Own Gemini call with `ORCHESTRATOR_ANALYSIS_EVAL_PROMPT`.

Output JSON: `{ "decision": "proceed|re-analyse", "reasoning": "...", "guidance_for_reanalysis": "..." }`

If `decision == "re-analyse"` → re-invoke Agent 2 with `guidance_for_reanalysis` as `reanalysis_note`.

**Evaluation Criteria for Checkpoint 1:**
- Were all reports processed?
- Are entities/locations extracted from each report?
- Is cluster score justified by evidence?
- Were anomalies detected where baselines exceeded?
- Is signal quality assessment reasonable?

**Evaluation Criteria for Checkpoint 2:**
- Does reasoning connect ALL 4 signal sources (social + weather + traffic + gov)?
- Is confidence score justified?
- Are anomalies quantified (not just listed)?
- Is crisis_type specific (not "unknown")?
- Does severity seem reasonable?

**Full step_log sequence:**

| Step | Message |
|------|---------|
| 0 | Pipeline start, N reports for location |
| 1 | Agent 1 start |
| 2 | Agent 1 complete |
| 2.5 | Checkpoint 1 evaluation |
| 2.6 | (if reprocess) requesting reprocessing |
| 2.7 | (if reprocess) reprocessing complete |
| 3 | Agent 2 start |
| 4 | Agent 2 complete |
| 5 | Checkpoint 2 evaluation |
| 5.5 | (if re-analyse) requesting re-analysis |
| 5.6 | (if re-analyse) re-analysis complete |
| 6 | Agent 3 start |
| 7 | Agent 3 complete |
| 8 | City-State Simulator start |
| 9 | Pipeline complete |

**Return shape:**
```python
{
  "session_id": session_id,
  "situation_report": situation_report,
  "action_plan": action_plan,
  "city_state": city_state,
  "orchestrator_evaluations": {
    "signal_checkpoint": signal_evaluation,
    "analysis_checkpoint": analysis_evaluation,
  },
  "signal_bundle_summary": {
    "cluster_score": ...,
    "anomalies_count": ...,
    "signal_quality": ...,
  }
}
```

---

## 9. Subsystem: GeoTemporal Correlation Engine

**Module:** `geo_temporal.py`

**Purpose:** Synthesize evidence BEFORE passing signals to agents. Compute a `confidence_boost` and `escalated_severity` based on spatial clustering, time clustering, and cross-source validation. This is what makes CIRO an *intelligence system* rather than an AI wrapper.

### Input
- `social_reports` — list of raw report strings
- `location` — string
- `weather` — WeatherData dict (rainfall_mm_1h, alert_level)
- `traffic` — TrafficData dict (congestion_pct, avg_speed_kmh)
- `gov_alert_exists` — bool

### Spatial Clustering Logic

Reports are considered geographically clustered if they mention location variants within the same sector family (e.g. "G-10", "G10", "g-10", "G 10" all match for location `G-10`).

```python
def count_location_matches(reports: list, location: str) -> int:
    loc = location.lower()
    variants = [loc, loc.replace('-', ' '), loc.replace(' ', '-')]
    return sum(1 for r in reports if any(v in r.lower() for v in variants))
```

Radius threshold concept: **1.2 km** — reports within the same sector are treated as co-located.

### Temporal Clustering Logic

If multiple reports arrive within a **10–15 minute window** (inferred from timestamp proximity or report count), confidence increases. In the current implementation (no real timestamps on social reports), use report count as a proxy for temporal density.

### Escalation Decision Table

| Reports (location-matched) | Rainfall | Congestion | Gov Alert | Escalated Severity | Confidence Boost |
|----------------------------|----------|------------|-----------|-------------------|-----------------|
| ≥ 2 | any | any | no | LOW | +0 |
| ≥ 3 | any | any | no | LOW | +10 |
| ≥ 5 | > 50mm | > 80% | no | MEDIUM | +20 |
| ≥ 8 | > 50mm | > 80% | no | HIGH | +25 |
| ≥ 5 | > 50mm | > 80% | yes | HIGH | +30 |
| ≥ 8 | > 50mm | > 80% | yes | CRITICAL | +35 |
| ≥ 12 | > 50mm | > 80% | yes | CRITICAL | +40 |

### Implementation

```python
def run_geo_temporal_correlation(
    social_reports: list,
    location: str,
    weather: dict,
    traffic: dict,
    gov_alert_exists: bool = True
) -> dict:

    nearby_reports = count_location_matches(social_reports, location)
    rainfall_mm = weather.get('rainfall_mm_1h', 0)
    congestion_pct = traffic.get('congestion_pct', 0)
    traffic_speed_drop = (
        (traffic.get('normal_speed_kmh', 45) - traffic.get('avg_speed_kmh', 45))
        / traffic.get('normal_speed_kmh', 45) * 100
    )

    confidence_boost = 0
    severity = 'LOW'
    factors = []

    if nearby_reports >= 3:
        confidence_boost += 10
        factors.append(f'{nearby_reports} location-matched reports in cluster')

    if rainfall_mm > 50:
        confidence_boost += 10
        factors.append(f'Extreme rainfall {rainfall_mm}mm/h exceeds 50mm threshold')

    if congestion_pct > 80:
        confidence_boost += 5
        factors.append(f'Congestion {congestion_pct}% exceeds 80% threshold')

    if traffic_speed_drop > 70:
        confidence_boost += 5
        factors.append(f'Speed drop {traffic_speed_drop:.0f}% from normal')

    if gov_alert_exists:
        confidence_boost += 10
        factors.append('Government/NDMA advisory active')

    # Severity escalation
    if nearby_reports >= 12 and rainfall_mm > 50 and gov_alert_exists:
        confidence_boost += 5
        severity = 'CRITICAL'
    elif nearby_reports >= 8 and rainfall_mm > 50 and congestion_pct > 80:
        severity = 'CRITICAL' if gov_alert_exists else 'HIGH'
    elif nearby_reports >= 5 and rainfall_mm > 50:
        severity = 'HIGH' if gov_alert_exists else 'MEDIUM'
    elif nearby_reports >= 3:
        severity = 'MEDIUM'

    return {
        'report_cluster_count': nearby_reports,
        'time_window_minutes': 15,
        'confidence_boost': min(confidence_boost, 40),   # cap at 40
        'escalated_severity': severity,
        'correlation_factors': factors
    }
```

### Where It's Used

The GeoTemporal result is:
1. Stored in `signal_bundle.geo_correlation`
2. Passed to Agent 1 prompt as additional context
3. Used by Agent 2 to validate its confidence score (if confidence_score < geo_correlation confidence_boost * 2, flag for re-analysis)

---

## 10. Subsystem: City-State Simulation Engine

**Module:** `city_simulator.py`

**Purpose:** After `action_plan` is generated, simulate the measurable impact of executing those actions. Produce a `before` and `after` city state with numeric metrics. This gives judges visible, quantified proof that the system improves city conditions.

### Before State (derived from traffic data)

```python
def build_before_state(traffic: dict, situation_report: dict) -> dict:
    return {
        'congestion_pct': traffic['congestion_pct'],
        'avg_speed_kmh': traffic['avg_speed_kmh'],
        'roads_blocked': random.randint(2, 4),
        'vehicles_stranded': random.randint(30, 55),
        'ambulance_eta': random.randint(25, 40),
        'citizens_at_risk': situation_report.get('severity', {}).get('people_affected', 1000),
        'severity_level': 'CRITICAL',
        'timestamp': datetime.utcnow().isoformat()
    }
```

### After State (apply action effects)

```python
def simulate_after_state(before: dict, action_plan: dict) -> dict:
    updated = before.copy()
    updated['timestamp'] = datetime.utcnow().isoformat()

    # Rerouting reduces congestion and improves speed
    if action_plan.get('rerouting'):
        updated['congestion_pct'] = max(
            20, before['congestion_pct'] - random.randint(20, 35)
        )
        updated['avg_speed_kmh'] = min(
            60, before['avg_speed_kmh'] + random.randint(8, 18)
        )
        updated['roads_blocked'] = max(0, before['roads_blocked'] - 2)

    # Dispatch reduces vehicles stranded and improves ETA
    if action_plan.get('dispatch'):
        updated['vehicles_stranded'] = max(
            0, before['vehicles_stranded'] - random.randint(15, 30)
        )
        updated['ambulance_eta'] = action_plan['dispatch'].get(
            'eta_minutes', before['ambulance_eta']
        )

    # Alert reduces citizens at risk (they evacuate/avoid)
    if action_plan.get('alert'):
        updated['citizens_at_risk'] = max(
            0, before['citizens_at_risk'] - random.randint(400, 900)
        )

    # Recalculate severity based on updated congestion
    if updated['congestion_pct'] < 35:
        updated['severity_level'] = 'MEDIUM'
    elif updated['congestion_pct'] < 60:
        updated['severity_level'] = 'HIGH'
    else:
        updated['severity_level'] = 'CRITICAL'

    return updated
```

### Output Shape

```python
city_state = {
    'before': before,
    'after': after
}
```

### Where It's Used

1. Called by Orchestrator after Agent 3 returns `action_plan`
2. Result stored in `crisis_sessions/{session_id}/city_state`
3. Included in `/analyse` response as `city_state` field

---

## 11. Subsystem: Historical Incident Memory Layer

**Module:** `memory.py`

**Purpose:** Allow agents to compare current crises to historical incidents, providing contextual intelligence instead of purely reactive analysis.

### Interface

```python
def find_historical_match(location: str, crisis_type: str = None) -> dict | None:
    """
    Query Firestore historical_incidents collection.
    Match on location (case-insensitive contains).
    Optionally filter by crisis_type.
    Return most recent match or None.
    """
    query = db.collection('historical_incidents')
    docs = query.stream()
    matches = []
    for doc in docs:
        d = doc.to_dict()
        if location.lower() in d.get('location', '').lower():
            if crisis_type is None or d.get('crisis_type') == crisis_type:
                matches.append(d)
    return matches[0] if matches else None


def build_historical_context_string(match: dict | None) -> str:
    """Convert a historical incident into a context string for agent prompts."""
    if not match:
        return "No historical incidents found for this location."
    return (
        f"Current pattern matches the {match['month']} {match.get('crisis_type', 'incident')} "
        f"at {match['location']} (severity: {match['severity']}, "
        f"cause: {match['main_cause']}, "
        f"prior response effectiveness: {match['response_effectiveness']}%). "
        f"Roads previously affected: {', '.join(match.get('roads_affected', []))}."
    )
```

### Agent Usage

**Agent 1 (Signal Intelligence):** Appends historical context to prompt so Gemini can reference prior incidents when assessing cluster patterns.

**Agent 2 (Crisis Analyst):** Includes historical_context in reasoning. Prompt includes:
```
HISTORICAL CONTEXT:
{historical_context}
If this matches a prior incident, reference it in your reasoning.
```

### Seed Function

```python
def seed_historical_incidents():
    incidents = [
        {
            "incident_id": "INC_2025_G10_001",
            "location": "G-10",
            "crisis_type": "flood",
            "month": "July",
            "severity": "HIGH",
            "main_cause": "drainage overflow",
            "response_effectiveness": 72,
            "roads_affected": ["G-10 Main Boulevard", "Service Road East"]
        },
        {
            "incident_id": "INC_2025_I8_001",
            "location": "I-8",
            "crisis_type": "road_blockage",
            "month": "March",
            "severity": "MEDIUM",
            "main_cause": "accident on expressway",
            "response_effectiveness": 85,
            "roads_affected": ["I-8 Expressway", "Margalla Road"]
        },
        {
            "incident_id": "INC_2024_F6_001",
            "location": "F-6",
            "crisis_type": "heatwave",
            "month": "June",
            "severity": "HIGH",
            "main_cause": "prolonged heat spell",
            "response_effectiveness": 61,
            "roads_affected": []
        }
    ]
    for inc in incidents:
        db.collection('historical_incidents').document(inc['incident_id']).set(inc)
    return len(incidents)
```

---

## 12. External Integrations

### 12.1 OpenWeatherMap

**Endpoint:** `https://api.openweathermap.org/data/2.5/weather`

**Critical field:** `rain['1h']` — NOT `rainfall_mm_last_hour` (does not exist)

```python
def fetch_weather(location: str) -> dict:
    url = 'https://api.openweathermap.org/data/2.5/weather'
    params = {
        'q': f'{location},PK',
        'appid': OPENWEATHER_KEY,
        'units': 'metric'
    }
    try:
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        d = r.json()
        rainfall = d.get('rain', {}).get('1h', 0)
        return {
            'location': location,
            'rainfall_mm_1h': rainfall,
            'alert_level': classify_rain(rainfall),
            'wind_kmh': round(d.get('wind', {}).get('speed', 0) * 3.6, 1),
            'visibility_km': round(d.get('visibility', 10000) / 1000, 1),
            'description': d['weather'][0]['description'],
            'humidity_pct': d['main']['humidity'],
            'is_fallback': False
        }
    except Exception as e:
        # Fallback — pipeline must never break on weather failure
        return {
            'location': location,
            'rainfall_mm_1h': 87,
            'alert_level': 'SEVERE',
            'wind_kmh': 45,
            'visibility_km': 0.8,
            'description': 'heavy rain (simulated fallback)',
            'humidity_pct': 92,
            'is_fallback': True
        }

def classify_rain(mm: float) -> str:
    if mm >= 50: return 'EXTREME'
    if mm >= 20: return 'SEVERE'
    if mm >= 7:  return 'HEAVY'
    if mm >= 2:  return 'MODERATE'
    return 'LIGHT'
```

---

### 12.2 Google Gemini 2.0 Flash

**SDK:** `google-generativeai`

**Model string:** `gemini-2.0-flash`

**JSON Parsing — Robust Version:**

```python
import re
import json

def parse_gemini_json(text: str) -> dict:
    """Parse JSON from Gemini, handling all markdown fence formats."""
    text = text.strip()
    text = re.sub(r'```(?:json|JSON)?\s*\n?', '', text).strip()
    text = re.sub(r'\n?```\s*$', '', text).strip()
    return json.loads(text)
```

**Rate Limit Mitigation:** Add `time.sleep(0.5)` between consecutive Gemini calls within the same request.

---

### 12.3 Firebase Firestore (Admin SDK)

All writes use `ArrayUnion` for array fields (atomic, no conflict):

```python
db.collection('crisis_sessions').document(session_id).update({
    'step_log': firestore.ArrayUnion([{
        'step': step,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }])
})
```

---

## 13. Error Handling & Fallback Strategy

**Core principle: The pipeline must NEVER return a 500 due to an individual agent or integration failing.** Every subsystem has a fallback.

| Component | Failure Mode | Fallback |
|-----------|-------------|----------|
| OpenWeatherMap | Timeout / API error | Return hardcoded fallback (87mm rainfall, is_fallback: true) |
| Agent 1 Gemini | JSON parse error / API error | Fallback cluster score from keyword matching; empty reports list |
| Checkpoint 1 Gemini | Parse error | Default to `{ "decision": "proceed" }` |
| Agent 2 Gemini | Parse error | Return `{ crisis_type: "unknown", confidence_score: 0 }` |
| Checkpoint 2 Gemini | Parse error | `proceed` if confidence >= 40, else `re-analyse` |
| Agent 3 Gemini | Parse error | Hardcoded G-10 action plan with random ticket_id |
| City Simulator | Any error | Return before_state and a minimally modified after_state |
| Firestore write | Timeout | Log error, continue pipeline — don't abort |
| Historical query | Any error | Return None — no historical context |

**Top-level try/except in /analyse:**

```python
try:
    result = agent_orchestrator(social_reports, location, session_id)
    return jsonify(result), 200
except Exception as e:
    log_step(session_id, 99, f'Pipeline error: {str(e)}')
    db.collection('crisis_sessions').document(session_id).update({'status': 'error'})
    return jsonify({
        'session_id': session_id,
        'status': 'error',
        'error': str(e)
    }), 500
```

---

## 14. File & Module Structure

```
CIRO/
├── AGENTS.md
├── README.md
├── .gitignore
├── .agents/
│   ├── rules/
│   │   └── ciro-standards.md
│   ├── skills/
│   │   ├── gemini-prompting/
│   │   │   └── SKILL.md
│   │   ├── crisis-detection/
│   │   │   └── SKILL.md
│   │   └── simulation-engine/
│   │       └── SKILL.md
│   └── workflows/
│       ├── test-pipeline.md
│       ├── demo-run.md
│       └── emergency-analysis.md
├── backend/
│   ├── app.py
│   ├── constants.py
│   ├── utils.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── agents/
│   │   ├── signal_intelligence.py
│   │   ├── crisis_analyst.py
│   │   ├── response_commander.py
│   │   └── orchestrator.py
│   ├── services/
│   │   ├── weather_service.py
│   │   ├── traffic_service.py
│   │   ├── firebase_service.py
│   │   └── gemini_service.py
│   ├── simulation/
│   │   └── city_state_simulator.py
│   ├── prompts/
│   │   ├── signal_prompt.txt
│   │   ├── analyst_prompt.txt
│   │   ├── response_prompt.txt
│   │   └── orchestrator_prompt.txt
│   └── data/
│       └── historical_incidents.json
├── mobile/
│   └── CIROApp/
│       ├── screens/
│       ├── components/
│       ├── services/
│       ├── constants/
│       └── assets/
└── docs/
    ├── architecture.md
    ├── api-flow.md
    ├── demo-script.md
    └── screenshots/
```

### constants.py

```python
# Firebase field names
COLLECTION_SESSIONS = 'crisis_sessions'
COLLECTION_HISTORICAL = 'historical_incidents'

# Agent names
AGENT_SIGNAL_INTEL = 'signal_intelligence'
AGENT_CRISIS_ANALYST = 'crisis_analyst'
AGENT_RESPONSE_COMMANDER = 'response_commander'
AGENT_ORCHESTRATOR = 'orchestrator'

# Islamabad coordinates (G-10 area)
COORDS = {
    'G-10_Markaz': {'lat': 33.6844, 'lng': 72.9857},
    'G-10/1':      {'lat': 33.6831, 'lng': 72.9812},
    'G-10/2':      {'lat': 33.6820, 'lng': 72.9778},
    'G-10/3':      {'lat': 33.6807, 'lng': 72.9741},
    'G-9_Markaz':  {'lat': 33.6910, 'lng': 72.9857},
    'G-11':        {'lat': 33.6865, 'lng': 72.9741},
}

# Anomaly baselines for Islamabad
BASELINES = {
    'rainfall_normal_mmh': 7,
    'wind_normal_kmh': 25,
    'visibility_normal_km': 5,
    'congestion_normal_pct': 30,
    'traffic_speed_normal_kmh': 45,
}

# Gemini model
GEMINI_MODEL = 'gemini-2.0-flash'
```

---

## 15. Postman Testing Guide

### Collection Setup

Create a Postman collection called **CIRO Backend**. Set a variable `BASE_URL = http://localhost:5000`.

---

### Test 1 — Health Check

```
GET {{BASE_URL}}/health
```

Expected: `200`, body contains `"status": "ok"` and all 4 agents listed.

---

### Test 2 — Seed Historical Incidents

```
POST {{BASE_URL}}/seed
```

Expected: `200`, `{"status": "seeded", "count": 3}`

Run this once after fresh deployment.

---

### Test 3 — Full Pipeline (Strong Signal, 5 Reports)

```
POST {{BASE_URL}}/analyse
Content-Type: application/json

{
  "location": "G-10",
  "social_reports": [
    "G-10 mein pani bhar gaya hai, gaariyan phans gayi hain",
    "Cars trapped near G-10 markaz, road fully blocked",
    "Severe flooding on G-10 main boulevard, avoid the area",
    "G-10 mein baarish ki wajah se traffic jam hai",
    "Water level rising fast at G-10/2, people stuck"
  ]
}
```

**Expected:**
- `200 OK`
- `situation_report.crisis_type` = `"flood"`
- `situation_report.confidence_level` = `"HIGH"`
- `situation_report.confidence_score` ≥ 70
- `action_plan` has all 3 keys: `rerouting`, `dispatch`, `alert`
- `action_plan.dispatch.ticket_id` matches `EMR-\d{4}`
- `city_state.before.congestion_pct` > `city_state.after.congestion_pct`
- `city_state.after.severity_level` ∈ `["CRITICAL", "HIGH", "MEDIUM"]`
- `orchestrator_evaluations.signal_checkpoint.decision` present
- `orchestrator_evaluations.analysis_checkpoint.decision` present

---

### Test 4 — Feedback Loop Trigger (1 Vague Report)

```json
{
  "location": "G-10",
  "social_reports": [
    "kuch ho raha hai"
  ]
}
```

**Expected:**
- `200 OK` (pipeline must not crash)
- `situation_report.confidence_score` < 50
- One or both checkpoint decisions = `"reprocess"` or `"re-analyse"`
- In `/logs/{session_id}`: `step_log` contains a step 2.6 or 5.5 (re-analysis triggered)

---

### Test 5 — Multi-Language Input

```json
{
  "location": "G-10",
  "social_reports": [
    "G-10 mein pani bhar gaya hai",
    "flooding in G-10 sector, multiple cars stuck",
    "جی ٹین میں سیلاب آ گیا ہے"
  ]
}
```

**Expected:**
- Each processed_report in `signal_bundle.social_reports` has `language` ∈ `["roman_urdu", "urdu", "english", "mixed"]`
- Roman Urdu correctly classified

---

### Test 6 — Fetch Session Logs

After Test 3 completes, copy `session_id` from response:

```
GET {{BASE_URL}}/logs/sess_20260514_212345
```

**Expected:**
- Full Firestore document
- `agent_trace` has ≥ 5 entries (one per agent + orchestrator checkpoints)
- `step_log` has ≥ 9 entries
- `city_state` present with before/after fields

---

### Test 7 — Validation: Missing Location

```json
{
  "social_reports": ["flooding in G-10"]
}
```

**Expected:** `400`, `{"error": "Location is required"}`

---

### Test 8 — Validation: Empty Reports

```json
{
  "location": "G-10",
  "social_reports": ["   ", "", " "]
}
```

**Expected:** `400`, `{"error": "At least 1 report required"}`

---

### Test 9 — Historical Incidents List

```
GET {{BASE_URL}}/historical
```

**Expected:** `200`, `{"incidents": [...]}` with ≥ 1 incident

---

### Test 10 — GeoTemporal Correlation Verification

Send 8+ reports all mentioning G-10:

```json
{
  "location": "G-10",
  "social_reports": [
    "G-10 mein baarish, sarak band", "G-10 main road blocked",
    "G-10 mein pani", "G-10/2 mein gaariyan phansi hain",
    "Heavy rain G-10", "Flood G-10 markaz", "G-10 traffic jaam",
    "G-10 emergency hai"
  ]
}
```

**Expected:**
- `signal_bundle_summary.cluster_score` = `"HIGH"`
- `signal_bundle.geo_correlation.escalated_severity` = `"CRITICAL"` or `"HIGH"`
- `signal_bundle.geo_correlation.confidence_boost` ≥ 25

---

## 16. Backend Build Plan (Day-by-Day)

### Day 2 — May 14 (Foundation)

- [ ] Create project folder structure (see Section 14)
- [ ] Create `constants.py` — coordinates, baselines, field names
- [ ] Create `.env` with all 4 API keys
- [ ] Verify API keys: run OWM curl, test Gemini in AI Studio, test Firebase
- [ ] Implement `weather.py` — `fetch_weather()`, `classify_rain()`
- [ ] Implement `traffic.py` — `generate_traffic_data()` with randomization
- [ ] Implement `utils.py` — `create_session()`, `log_step()`, `log_agent_trace()`, `write_before_state()`, `write_after_state()`
- [ ] Implement `parse_gemini_json()` — test against fenced and unfenced JSON
- [ ] Build Flask skeleton in `app.py` — CORS, Gemini init, Firebase init, /health route
- [ ] Test /health in Postman (Test 1)

---

### Day 3 — May 15 (Core Agents)

- [ ] Implement `agents.py` — Agent 1 (Signal Intelligence) with full Gemini prompt
- [ ] Test Agent 1 standalone with 3-report payload (call function directly, print output)
- [ ] Implement Agent 2 (Crisis Analyst)
- [ ] Implement Agent 3 (Response Commander)
- [ ] Implement Agent 4 (Orchestrator) with TWO checkpoints and feedback loops
- [ ] Wire all 4 agents in `POST /analyse`
- [ ] Implement `GET /logs/<session_id>`
- [ ] Test full pipeline in Postman (Test 3)
- [ ] Test feedback loop trigger (Test 4) — verify step 2.6 or 5.5 appears in step_log
- [ ] Verify all Firebase fields populated correctly via Test 6

---

### Day 4 — May 16 (New Subsystems)

- [ ] Implement `geo_temporal.py` — full correlation engine
- [ ] Integrate GeoTemporal output into Agent 1 signal_bundle
- [ ] Test GeoTemporal (Test 10)
- [ ] Implement `city_simulator.py` — before/after state simulation
- [ ] Integrate City Simulator into Orchestrator (after Agent 3)
- [ ] Verify `city_state` in /analyse response and in Firestore
- [ ] Implement `memory.py` — historical incident query + context string builder
- [ ] Add `/seed` and `/historical` endpoints
- [ ] Seed historical incidents (Test 2), verify (Test 9)
- [ ] Integrate historical context into Agent 1 and Agent 2 prompts
- [ ] Verify `historical_context` field in situation_report

---

### Day 5 — May 17 (Hardening)

- [ ] Test all 10 Postman tests — all must pass
- [ ] Test edge cases: OWM failure (pull API key temporarily), Gemini bad JSON, empty reports
- [ ] Confirm randomized traffic data looks different across 3 consecutive runs
- [ ] Add `time.sleep(0.5)` between Gemini calls to avoid rate limits
- [ ] Verify `.gitignore` covers `.env` and `firebase_credentials.json`
- [ ] Run demo flow 5 times consecutively — pipeline must complete reliably
- [ ] Create `requirements.txt` with pinned versions

---

## 17. Known Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| OWM `rain['1h']` missing on dry day | Weather fallback activates; is_fallback=true | Fallback returns 87mm SEVERE — good for demo. Note limitation in README. |
| Gemini rate limit during rapid testing | 429 error, pipeline fails | `time.sleep(0.5)` between calls; test at most 2 req/min during Postman testing |
| Gemini returns non-JSON | Agent crashes | `parse_gemini_json()` handles all fence formats; every agent has try/except with typed fallback |
| Firestore write conflict on ArrayUnion | None — ArrayUnion is atomic | No action needed; document this as a design choice |
| Traffic data looks identical across runs | Judges notice hardcoded data | `random.randint()` ranges; 3 different randomized fields per run |
| Historical incidents not seeded | `find_historical_match()` returns None | Handled gracefully; context string = "No historical incidents found" |
| Gemini confidence score conflicts with GeoTemporal boost | Inconsistent outputs | GeoTemporal boost is informational context, not a direct override; Gemini synthesizes it |
| Session ID collision | Two requests at same second get same ID | Add milliseconds: `sess_{datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")[:20]}` |

---

*This document is the single source of truth for CIRO backend development.*
*Frontend/UI phase begins after all 10 Postman tests pass reliably.*
