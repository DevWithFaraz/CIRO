from datetime import datetime
from firebase_admin import firestore
from constants import COLLECTION_SESSIONS


def _get_db():
    return firestore.client()


def create_session(session_id: str, location: str) -> None:
    try:
        db = _get_db()
        db.collection(COLLECTION_SESSIONS).document(session_id).set({
            'created_at': datetime.utcnow().isoformat(),
            'location': location,
            'status': 'processing',
            'agent_trace': [],
            'step_log': []
        })
    except Exception:
        pass


def log_step(session_id: str, step: float, message: str) -> None:
    try:
        db = _get_db()
        db.collection(COLLECTION_SESSIONS).document(session_id).update({
            'step_log': firestore.ArrayUnion([{
                'step': step,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }])
        })
    except Exception:
        pass


def log_agent_trace(session_id: str, agent_name: str,
                    input_summary: str, output_summary: str,
                    gemini_prompt: str, gemini_response: str,
                    decision: str, status: str = 'success') -> None:
    try:
        db = _get_db()
        db.collection(COLLECTION_SESSIONS).document(session_id).update({
            'agent_trace': firestore.ArrayUnion([{
                'agent_name': agent_name,
                'timestamp': datetime.utcnow().isoformat(),
                'input_summary': input_summary,
                'output_summary': output_summary,
                'gemini_prompt': gemini_prompt[:500],
                'gemini_response': gemini_response[:500],
                'decision': decision,
                'status': status,
            }])
        })
    except Exception:
        pass


def write_before_state(session_id: str, state: dict) -> None:
    try:
        db = _get_db()
        db.collection(COLLECTION_SESSIONS).document(session_id).update({
            'before_state': state
        })
    except Exception:
        pass


def write_after_state(session_id: str, state: dict) -> None:
    try:
        db = _get_db()
        db.collection(COLLECTION_SESSIONS).document(session_id).update({
            'after_state': state,
            'status': 'complete'
        })
    except Exception:
        pass
