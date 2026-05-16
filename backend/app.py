import os
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()

if not firebase_admin._apps:
    cred = credentials.Certificate(os.getenv('FIREBASE_CRED_PATH'))
    firebase_admin.initialize_app(cred)

db = firestore.client()
app = Flask(__name__)
CORS(app)

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

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    app.run(debug=True, port=port)
