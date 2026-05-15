from datetime import datetime
from google.cloud.firestore import ArrayUnion

def create_session(db, location: str) -> str:
    session_id = f"sess_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
    try:
        db.collection('crisis_sessions').document(session_id).set({
            'created_at': datetime.utcnow().isoformat(),
            'location': location,
            'status': 'processing',
            'agent_trace': [],
            'step_log': []
        })
    except Exception as e:
        # Silent try/except — never raises, as requested
        print(f"[Error] create_session failed: {e}")
    return session_id

def log_step(db, session_id: str, step: float, message: str) -> None:
    try:
        db.collection('crisis_sessions').document(session_id).update({
            'step_log': ArrayUnion([{
                'step': step,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }])
        })
    except Exception as e:
        print(f"[Error] log_step failed: {e}")

def log_agent_trace(db, session_id: str, entry: dict) -> None:
    try:
        db.collection('crisis_sessions').document(session_id).update({
            'agent_trace': ArrayUnion([entry])
        })
    except Exception as e:
        print(f"[Error] log_agent_trace failed: {e}")

def write_before_state(db, session_id: str, state: dict) -> None:
    try:
        db.collection('crisis_sessions').document(session_id).update({
            'before_state': state
        })
    except Exception as e:
        print(f"[Error] write_before_state failed: {e}")

def write_after_state(db, session_id: str, state: dict) -> None:
    try:
        db.collection('crisis_sessions').document(session_id).update({
            'after_state': state
        })
    except Exception as e:
        print(f"[Error] write_after_state failed: {e}")

def update_session(db, session_id: str, fields: dict) -> None:
    try:
        db.collection('crisis_sessions').document(session_id).update(fields)
    except Exception as e:
        print(f"[Error] update_session failed: {e}")
