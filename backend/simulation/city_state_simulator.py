import random
from datetime import datetime

def build_before_state(traffic: dict) -> dict:
    return {
        'congestion_pct': traffic['congestion_pct'],
        'avg_speed_kmh': traffic['avg_speed_kmh'],
        'vehicles_stranded': 42,
        'ambulance_eta_minutes': 31,
        'ambulance_eta': 31,
        'citizens_at_risk': 1200,
        'severity_level': 'CRITICAL',
        'roads_blocked': 3,
        'emergency_teams': 0,
        'alerts_sent': 0,
        'response_status': 'none',
        'timestamp': datetime.utcnow().isoformat()
    }

def simulate_after_state(before: dict, action_plan: dict) -> dict:
    after = before.copy()

    if 'rerouting' in action_plan:
        after['congestion_pct'] -= random.randint(20, 36)
        after['avg_speed_kmh'] += random.randint(8, 18)
        after['roads_blocked'] = 1

    if 'dispatch' in action_plan:
        after['vehicles_stranded'] -= random.randint(15, 30)
        after['ambulance_eta_minutes'] = action_plan['dispatch'].get('eta_minutes', 12)
        after['ambulance_eta'] = after['ambulance_eta_minutes']
        after['emergency_teams'] = action_plan['dispatch'].get('teams_deployed', 2)

    if 'alert' in action_plan:
        after['citizens_at_risk'] -= random.randint(400, 900)
        after['alerts_sent'] = len(action_plan['alert'].get('zones_affected', []))

    after['congestion_pct'] = max(25, min(after['congestion_pct'], 95))
    after['avg_speed_kmh'] = max(8, min(after['avg_speed_kmh'], 35))
    after['vehicles_stranded'] = max(3, after['vehicles_stranded'])
    after['ambulance_eta_minutes'] = max(5, after['ambulance_eta_minutes'])
    after['citizens_at_risk'] = max(100, after['citizens_at_risk'])

    if after['congestion_pct'] > 60:
        after['severity_level'] = 'CRITICAL'
    elif after['congestion_pct'] > 35:
        after['severity_level'] = 'HIGH'
    else:
        after['severity_level'] = 'MEDIUM'

    after['response_status'] = 'active_response'
    after['timestamp'] = datetime.utcnow().isoformat()

    return after

def run_city_simulation(traffic: dict, action_plan: dict) -> dict:
    try:
        before = build_before_state(traffic)
        after = simulate_after_state(before, action_plan)
        return {'before': before, 'after': after}
    except Exception:
        return {'before': {}, 'after': {}}
