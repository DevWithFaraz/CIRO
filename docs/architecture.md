# CIRO Architecture

## Agent Pipeline
Mobile App → POST /analyse → Orchestrator → Signal Intelligence → Checkpoint 1
→ Crisis Analyst → Checkpoint 2 → Response Commander → City-State Simulator
→ Firebase → Mobile App (real-time via onSnapshot)

## Feedback Loops
- Checkpoint 1 (after Agent 1): evaluates signal quality, can reprocess
- Checkpoint 2 (after Agent 2): evaluates confidence, can re-analyse

## Data Flow
social_reports + location → signal_bundle → situation_report → action_plan → execution_log
