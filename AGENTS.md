# CIRO — Agent Guidelines

## Project Overview
Crisis Intelligence & Response Orchestrator. 4 Gemini-powered runtime agents
that ingest multi-source crisis signals, detect emergencies, and simulate
coordinated response actions with measurable before/after city-state metrics.

## Runtime Agent Architecture
Located in backend/agents/:
- signal_intelligence.py — processes raw multi-language signals, clusters, anomalies
- crisis_analyst.py — infers crisis type, severity, confidence from all 4 sources
- response_commander.py — generates rerouting, dispatch, alert actions with AI reasoning
- orchestrator.py — coordinates agents with 2 evaluation checkpoints and re-analysis loops

## Services (backend/services/)
- weather_service.py — OpenWeatherMap, field is rain['1h'] NOT rainfall_mm_last_hour
- traffic_service.py — dynamic simulated traffic with randomization per session
- firebase_service.py — all Firestore read/write, log_step, log_agent_trace
- gemini_service.py — Gemini client, shared model instance, parse_gemini_json()

## Simulation (backend/simulation/)
- city_state_simulator.py — computes before/after numeric city-state metrics

## Prompts (backend/prompts/)
All Gemini prompts as .txt files, loaded at runtime by each agent

## Coding Standards
- ALL agents use Gemini API — no hardcoded logic pretending to be agents
- Every agent logs to Firebase via firebase_service.log_agent_trace()
- Firebase field names imported from constants.py — never typed freehand
- All external calls have try/except with meaningful fallback data
- API keys from backend/.env via python-dotenv — never hardcoded anywhere
- Flask routes validate input before calling any agent
- All Gemini responses parsed via gemini_service.parse_gemini_json()

## React Native Rules
- Use firebase npm SDK NOT @react-native-firebase (breaks Expo Go)
- Use react-native-webview for maps NOT react-native-maps
- All colors from mobile/CIROApp/constants/colors.js

## Absolute Rules
- Never hardcode traffic — use traffic_service.generate()
- Never use rain['rainfall_mm_last_hour'] — correct field is rain['1h']
- Never skip CORS on Flask
- Never put secrets in source files
