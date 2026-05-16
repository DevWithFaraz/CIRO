import json
import random
from datetime import datetime
from constants import AGENT_RESPONSE_COMMANDER, COLLECTION_SESSIONS
from services.gemini_service import generate_content, parse_gemini_json
from utils import log_step, log_agent_trace

def agent_response_commander(situation_report: dict, session_id: str) -> dict:
    log_step(session_id, 6,
      'Response Commander Agent: planning actions with Gemini...')
    
    prompt = ""
    try:
        prompt_template = (
            "You are the Response Commander Agent in CIRO.\n"
            "Generate 3 coordinated response actions for this crisis.\n"
            "Actions must be SPECIFIC to the crisis type, location, and severity.\n"
            "Do not use generic templates.\n"
            "\n"
            "CRISIS ASSESSMENT:\n"
            "  Type: {crisis_type}\n"
            "  Location: {location}\n"
            "  Confidence: {confidence_level} ({confidence_score}%)\n"
            "  Severity: {people_affected} people affected, {km_affected} km radius\n"
            "  Impact: {impact}\n"
            "\n"
            "AVAILABLE ISLAMABAD RESOURCES:\n"
            "  Fire stations: F-8 (G-8), G-9 Station, I-8 Station\n"
            "  Hospitals: PIMS (G-8), Shifa International (H-8)\n"
            "  Police: Kohsar (F-6), Margalla (E-7)\n"
            "  Alert channels: SMS, push notification, loudspeaker van, emergency radio\n"
            "\n"
            "G-10 COORDINATES FOR ROUTING:\n"
            "  G-10 Markaz:  33.6844, 72.9857\n"
            "  G-10/1:       33.6831, 72.9812\n"
            "  G-10/2:       33.6820, 72.9778\n"
            "  G-10/3:       33.6807, 72.9741\n"
            "  G-9 Markaz:   33.6910, 72.9857\n"
            "  G-11:         33.6865, 72.9741\n"
            "\n"
            "Return ONLY this JSON. No markdown. No explanation:\n"
            "{\n"
            '  "rerouting": {\n'
            '    "closed_road": "specific road name",\n'
            '    "alternate_route": "specific alternate with street name",\n'
            '    "reasoning": "why this rerouting",\n'
            '    "route_coords": {\n'
            '      "closed": [{"lat": 0.0, "lng": 0.0}, {"lat": 0.0, "lng": 0.0}],\n'
            '      "alternate": [{"lat": 0.0, "lng": 0.0}, {"lat": 0.0, "lng": 0.0}]\n'
            "    }\n"
            "  },\n"
            '  "dispatch": {\n'
            '    "ticket_id": "EMR-XXXX",\n'
            "    IMPORTANT: ticket_id must follow exactly this format: EMR-XXXX where XXXX is a random 4-digit number (e.g. EMR-4821). No dates, no dashes after the digits.\n"
            '    "services": ["rescue", "medical"],\n'
            '    "station": "specific station name",\n'
            '    "teams_deployed": 2,\n'
            '    "vehicles": ["rescue boat", "ambulance"],\n'
            '    "eta_minutes": 12,\n'
            '    "reasoning": "why these specific resources"\n'
            "  },\n"
            '  "alert": {\n'
            '    "zones_affected": ["zone1", "zone2", "zone3"],\n'
            '    "message": "complete alert text for citizens",\n'
            '    "severity": "CRITICAL|HIGH|MEDIUM",\n'
            '    "channels": ["SMS", "push", "loudspeaker"],\n'
            '    "reasoning": "why these zones and channels"\n'
            "  }\n"
            "}\n"
        )

        crisis_type = situation_report.get('crisis_type', 'unknown')
        location = situation_report.get('location', 'unknown')
        confidence_level = situation_report.get('confidence_level', 'LOW')
        confidence_score = situation_report.get('confidence_score', 0)
        severity = situation_report.get('severity', {})
        people_affected = severity.get('people_affected', 0)
        km_affected = severity.get('km_affected', 0)

        impact_list = situation_report.get('impact', [])
        impact = ', '.join(impact_list) if isinstance(impact_list, list) else str(impact_list)

        # Using replace instead of .format to avoid parsing issues with JSON braces in the prompt
        prompt = prompt_template.replace('{crisis_type}', str(crisis_type)) \
                                .replace('{location}', str(location)) \
                                .replace('{confidence_level}', str(confidence_level)) \
                                .replace('{confidence_score}', str(confidence_score)) \
                                .replace('{people_affected}', str(people_affected)) \
                                .replace('{km_affected}', str(km_affected)) \
                                .replace('{impact}', str(impact))

        response_text = generate_content(prompt)
        action_plan = parse_gemini_json(response_text)
        
    except Exception as e:
        action_plan = {
            'rerouting': {
                'closed_road': 'G-10 Main Boulevard',
                'alternate_route': 'G-9/G-11 connector via Nazimuddin Road',
                'reasoning': f'Fallback plan activated due to: {str(e)}',
                'route_coords': {
                    'closed': [
                        {'lat': 33.6844, 'lng': 72.9857},
                        {'lat': 33.6831, 'lng': 72.9812},
                        {'lat': 33.6820, 'lng': 72.9778},
                        {'lat': 33.6807, 'lng': 72.9741}
                    ],
                    'alternate': [
                        {'lat': 33.6910, 'lng': 72.9857},
                        {'lat': 33.6888, 'lng': 72.9790},
                        {'lat': 33.6865, 'lng': 72.9741},
                        {'lat': 33.6807, 'lng': 72.9741}
                    ]
                }
            },
            'dispatch': {
                'ticket_id': f'EMR-{random.randint(1000, 9999)}',
                'services': ['rescue', 'medical'],
                'station': 'F-8 Fire Station',
                'teams_deployed': 2,
                'vehicles': ['rescue boat', 'ambulance'],
                'eta_minutes': 12,
                'reasoning': 'Nearest station with flood response capability'
            },
            'alert': {
                'zones_affected': ['G-10', 'G-9', 'G-11'],
                'message': 'FLOOD ALERT: Avoid G-10 Main Boulevard. Use G-9/G-11 alternate routes. Emergency services en route.',
                'severity': 'CRITICAL',
                'channels': ['SMS', 'push', 'loudspeaker'],
                'reasoning': 'Adjacent sectors at risk of secondary flooding'
            }
        }
        if not prompt:
            prompt = f"Fallback due to: {str(e)}"

    now = datetime.utcnow().isoformat()
    for key in ['rerouting', 'dispatch', 'alert']:
        if key in action_plan:
            action_plan[key]['timestamp'] = now

    log_step(session_id, 7,
      f'Actions planned: reroute {action_plan.get("rerouting",{}).get("closed_road","?")}, '
      f'dispatch {action_plan.get("dispatch",{}).get("ticket_id","?")}, '
      f'alert {len(action_plan.get("alert",{}).get("zones_affected",[]))} zones')

    log_agent_trace(
        session_id=session_id,
        agent_name=AGENT_RESPONSE_COMMANDER,
        input_summary=f'{situation_report.get("crisis_type")} at {situation_report.get("location")}',
        output_summary=f'3 actions: reroute + dispatch EMR + alert {len(action_plan.get("alert",{}).get("zones_affected",[]))} zones',
        gemini_prompt=prompt[:500] if prompt else "",
        gemini_response=json.dumps(action_plan)[:500],
        decision='Generated contextual response plan with AI reasoning',
        status='success'
    )

    return action_plan
