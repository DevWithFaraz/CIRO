import datetime

def find_historical_match(db, location: str, crisis_type: str = None) -> dict | None:
    try:
        docs = db.collection('historical_incidents').stream()
        for doc in docs:
            data = doc.to_dict()
            db_location = data.get('location', '').lower()
            
            # Check if location matches
            if location.lower() in db_location or db_location in location.lower():
                if crisis_type:
                    if data.get('crisis_type', '').lower() == crisis_type.lower():
                        return data
                else:
                    return data
        return None
    except Exception:
        return None

def build_historical_context_string(match: dict | None) -> str:
    if match is None:
        return "No historical incidents found for this location."
    
    roads = match.get('roads_affected', [])
    roads_str = ", ".join(roads) if roads else "None"
    
    return (
        f"Current pattern matches the {match.get('month')} {match.get('crisis_type')} "
        f"at {match.get('location')} (severity: {match.get('severity')}, "
        f"cause: {match.get('main_cause')}, prior response effectiveness: "
        f"{match.get('response_effectiveness')}%). Roads previously affected: {roads_str}."
    )

def seed_historical_incidents(db) -> int:
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
    
    count = 0
    for incident in incidents:
        incident['created_at'] = datetime.datetime.utcnow().isoformat()
        db.collection('historical_incidents').document(incident['incident_id']).set(incident)
        count += 1
        
    return count
