import os
import random
import requests

def generate_traffic_data(location: str) -> dict:
    """
    Fetches traffic data using TomTom as primary, Google Maps as secondary,
    and a simulated fallback.
    """
    fallback = {
        "location": location,
        "congestion_pct": random.randint(78, 98),
        "avg_speed_kmh": random.randint(2, 8),
        "normal_speed_kmh": 45,
        "incidents": random.randint(2, 5),
        "data_source": "simulated_traffic_feed"
    }

    # 1. TOMTOM (Primary)
    tomtom_key = os.getenv("TOMTOM_KEY")
    if tomtom_key:
        try:
            lat, lng = 33.6844, 72.9857
            url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
            params = {
                "point": f"{lat},{lng}",
                "key": tomtom_key
            }
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            flow = data.get("flowSegmentData", {})
            currentSpeed = flow.get("currentSpeed")
            freeFlowSpeed = flow.get("freeFlowSpeed")
            
            if currentSpeed is not None and freeFlowSpeed is not None and freeFlowSpeed > 0:
                congestion_pct = round((1 - currentSpeed / freeFlowSpeed) * 100)
                return {
                    "location": location,
                    "congestion_pct": max(0, min(100, int(congestion_pct))),
                    "avg_speed_kmh": int(currentSpeed),
                    "normal_speed_kmh": 45,
                    "incidents": random.randint(2, 5),
                    "data_source": "simulated_traffic_feed"
                }
        except Exception:
            pass # Fall through to secondary

    # 2. GOOGLE MAPS (Secondary)
    google_maps_key = os.getenv("GOOGLE_MAPS_KEY")
    if google_maps_key:
        try:
            url = "https://maps.googleapis.com/maps/api/distancematrix/json"
            params = {
                "origins": "G-10 Markaz, Islamabad",
                "destinations": "F-8 Markaz, Islamabad",
                "departure_time": "now",
                "traffic_model": "best_guess",
                "key": google_maps_key
            }
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            rows = data.get("rows", [])
            if rows:
                elements = rows[0].get("elements", [])
                if elements:
                    element = elements[0]
                    duration = element.get("duration", {}).get("value")
                    duration_in_traffic = element.get("duration_in_traffic", {}).get("value")
                    
                    if duration is not None and duration_in_traffic is not None and duration > 0:
                        # Simple logic: if traffic duration > normal duration, calculate % extra time
                        congestion_pct = round(((duration_in_traffic - duration) / duration) * 100)
                        return {
                            "location": location,
                            "congestion_pct": max(0, min(100, int(congestion_pct))),
                            "avg_speed_kmh": random.randint(2, 8),
                            "normal_speed_kmh": 45,
                            "incidents": random.randint(2, 5),
                            "data_source": "simulated_traffic_feed"
                        }
        except Exception:
            pass # Fall through to fallback
            
    # 3. FINAL FALLBACK
    return fallback
