import os
import traceback
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials

from constants import COLLECTION_SESSIONS
from services.firebase_service import get_db, seed_historical_incidents

load_dotenv()

if not firebase_admin._apps:
    cred = credentials.Certificate(os.getenv('FIREBASE_CRED_PATH'))
    firebase_admin.initialize_app(cred)

app = Flask(__name__)
CORS(app)

try:
    from agents.orchestrator import agent_orchestrator
except ImportError:
    agent_orchestrator = None


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
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
    }), 200


@app.route('/analyse', methods=['POST'])
def analyse():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'No JSON body'}), 400

    location = data.get('location', '').strip()
    if not location:
        return jsonify({'error': 'Location is required'}), 400

    raw_reports = data.get('social_reports')
    if not isinstance(raw_reports, list):
        return jsonify({'error': 'social_reports must be a list'}), 400

    social_reports = [r.strip() for r in raw_reports if isinstance(r, str) and r.strip()]
    if not social_reports:
        return jsonify({'error': 'At least 1 report required'}), 400

    session_id = f"sess_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
    db = get_db()
    db.collection(COLLECTION_SESSIONS).document(session_id).set({
        'created_at': datetime.utcnow().isoformat(),
        'location': location,
        'status': 'processing',
        'agent_trace': [],
        'step_log': []
    })

    try:
        result = agent_orchestrator(social_reports, location, session_id)
        db.collection(COLLECTION_SESSIONS).document(session_id).update({'status': 'complete'})
        return jsonify(result), 200
    except Exception as e:
        traceback.print_exc()
        db.collection(COLLECTION_SESSIONS).document(session_id).update({'status': 'error'})
        return jsonify({
            'session_id': session_id,
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/logs/<session_id>', methods=['GET'])
def get_logs(session_id):
    try:
        db = get_db()
        doc = db.collection(COLLECTION_SESSIONS).document(session_id).get()
        if not doc.exists:
            return jsonify({'error': 'Session not found'}), 404
        return jsonify(doc.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/historical', methods=['GET'])
def get_historical():
    try:
        db = get_db()
        docs = db.collection('historical_incidents').stream()
        incidents = [doc.to_dict() for doc in docs]
        return jsonify({'incidents': incidents}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/seed', methods=['POST'])
def seed():
    try:
        count = seed_historical_incidents()
        return jsonify({'status': 'seeded', 'count': count}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    app.run(debug=True, port=port)
