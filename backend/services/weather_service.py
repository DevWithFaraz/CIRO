import os
import requests

def classify_rain(mm: float) -> str:
    """Classifies rainfall based on mm value."""
    if mm >= 50:
        return 'EXTREME'
    elif mm >= 20:
        return 'SEVERE'
    elif mm >= 7:
        return 'HEAVY'
    elif mm >= 2:
        return 'MODERATE'
    else:
        return 'LIGHT'

def fetch_weather(location: str) -> dict:
    """Fetches real weather data from OpenWeatherMap."""
    fallback_dict = {
        'location': location,
        'rainfall_mm_1h': 87.0,
        'alert_level': 'SEVERE',
        'wind_kmh': 45.0,
        'visibility_km': 0.8,
        'description': 'heavy rain (simulated fallback)',
        'humidity_pct': 92,
        'is_fallback': True
    }
    
    api_key = os.getenv('OPENWEATHER_KEY')
    if not api_key:
        return fallback_dict

    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': f"{location},PK",
            'units': 'metric',
            'appid': api_key
        }
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # Safely extract values with correct defaults
        # CRITICAL: OWM puts rain in a 'rain' object with '1h' key
        rain_data = data.get('rain', {})
        rainfall_mm_1h = float(rain_data.get('1h', 0.0))
        
        alert_level = classify_rain(rainfall_mm_1h)
        
        wind_speed_ms = float(data.get('wind', {}).get('speed', 0.0))
        wind_kmh = wind_speed_ms * 3.6
        
        visibility_m = float(data.get('visibility', 10000))
        visibility_km = visibility_m / 1000.0
        
        description = data.get('weather', [{}])[0].get('description', 'unknown')
        humidity_pct = int(data.get('main', {}).get('humidity', 0))
        
        return {
            'location': location,
            'rainfall_mm_1h': rainfall_mm_1h,
            'alert_level': alert_level,
            'wind_kmh': wind_kmh,
            'visibility_km': visibility_km,
            'description': description,
            'humidity_pct': humidity_pct,
            'is_fallback': False
        }
        
    except Exception:
        # The fallback must never raise — pipeline cannot break on weather failure
        return fallback_dict
