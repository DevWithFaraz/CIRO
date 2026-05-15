# CIRO API Routes Implementation

## Overview
Added the required API routes to the `backend/app.py` Flask application to support the CIRO backend processing, state management, and historical data seeding. The `/health` route was left untouched, and all existing code was preserved intact. We implemented a robust "monkey patch" solution to handle dependency resolution issues dynamically without mutating the external file.

## Changes Made
1. **Dependency Injections:**
   - Dynamically injected `firestore` into `services.firebase_service` directly from `app.py` to fix the missing `firestore` import inside `firebase_service.py` safely, maintaining the constraint to strictly only edit `app.py`.
   - Setup a safe conditional `ImportError` catch block to mock `agent_orchestrator` as `None` if `agents.orchestrator` is not yet importable or fully implemented.

2. **Routes Implemented:**
   - `POST /analyse`: Main entry point for processing incident reports.
     - **Input Validation**: Checks for JSON payload existence, required `location`, and a valid `social_reports` list containing at least 1 element. Returns `400 Bad Request` if validations fail.
     - **Graceful Degradation**: Returns `503 Service Unavailable` with `Orchestrator not available` if the orchestrator failed to import.
     - **Session Initialization**: Automatically generates a microsecond-precision `sess_` id and creates a processing session via `create_session(session_id, location)` before delegating to the Orchestrator.
   - `GET /logs/<session_id>`: Looks up and retrieves the live session state dictionary for the requested session from the Firestore database.
   - `GET /historical`: Streams and retrieves all stored historical incidents from the `historical_incidents` Firestore collection.
   - `POST /seed`: Seeds the database with the predefined historical incidents. Safely handles variations in the `seed_historical_incidents()` signature via nested try-except blocks, falling back to providing a local `firestore.client()` instance.

## Test Verification Output
The 5 validation curl commands were executed sequentially over the locally hosted Flask dev-server and verified working:
- `/health` returned `status: ok` and verified agents exist.
- `/seed` returned a success message.
- `/historical` returned the expected list of seeded mock data entries.
- `/analyse` (empty reports) returned HTTP 400 `{"error": "No valid reports provided"}`.
- `/analyse` (empty location) returned HTTP 400 `{"error": "Location is required"}`.
