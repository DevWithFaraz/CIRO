# Database Collections
COLLECTION_SESSIONS = 'crisis_sessions'
COLLECTION_HISTORICAL = 'historical_incidents'

# Agent Names
AGENT_SIGNAL_INTEL = 'signal_intelligence'
AGENT_CRISIS_ANALYST = 'crisis_analyst'
AGENT_RESPONSE_COMMANDER = 'response_commander'
AGENT_ORCHESTRATOR = 'orchestrator'

# Models
GEMINI_MODEL = 'gemini-2.5-flash'

# Coordinates
COORDS = {
    'G-10_Markaz': {'lat': 33.6844, 'lng': 72.9857},
    'G-10/1': {'lat': 33.6831, 'lng': 72.9812},
    'G-10/2': {'lat': 33.6820, 'lng': 72.9778},
    'G-10/3': {'lat': 33.6807, 'lng': 72.9741},
    'G-9_Markaz': {'lat': 33.6910, 'lng': 72.9857},
    'G-11': {'lat': 33.6865, 'lng': 72.9741}
}

# Baselines
BASELINES = {
    'rainfall_normal_mmh': 7,
    'wind_normal_kmh': 25,
    'visibility_normal_km': 5,
    'congestion_normal_pct': 30,
    'traffic_speed_normal_kmh': 45
}

# Resources
RESOURCES = {
    'fire_stations': ['F-8', 'G-9', 'I-8'],
    'hospitals': ['PIMS G-8', 'Shifa H-8'],
    'police_stations': ['Kohsar F-6', 'Margalla E-7'],
    'alert_channels': ['SMS', 'push notification', 'loudspeaker', 'radio']
}
