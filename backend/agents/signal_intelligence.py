import json
from google import genai
from services.weather_service import fetch_weather
from services.traffic_service import generate_traffic_data
from services.firebase_service import find_historical_match, build_historical_context_string
from services.gemini_service import parse_gemini_json, get_client
from utils import log_step, log_agent_trace
from constants import GEMINI_MODEL

# ─────────────────────────────────────────────────────────────────
# PART A — GeoTemporal Correlation Engine
# ─────────────────────────────────────────────────────────────────

def count_location_matches(reports: list, location: str) -> int:
    loc = location.lower()
    variants = {loc, loc.replace('-', ' '), loc.replace(' ', '-')}
    count = 0
    for report in reports:
        report_lower = report.lower() if isinstance(report, str) else str(report).lower()
        if any(v in report_lower for v in variants):
            count += 1
    return count


def run_geo_temporal_correlation(social_reports, location, weather,
                                 traffic, gov_alert_exists=True) -> dict:
    nearby_reports = count_location_matches(social_reports, location)
    rainfall_mm = weather.get('rainfall_mm_1h', 0)
    congestion_pct = traffic.get('congestion_pct', 0)
    normal_speed = traffic.get('normal_speed_kmh', 45)
    avg_speed = traffic.get('avg_speed_kmh', 45)
    traffic_speed_drop = ((normal_speed - avg_speed) / normal_speed) * 100 if normal_speed > 0 else 0

    # ── Confidence boost rules (additive) ──
    confidence_boost = 0
    correlation_factors = []

    if nearby_reports >= 3:
        confidence_boost += 10
        correlation_factors.append(f"{nearby_reports} reports cluster near {location}")
    if rainfall_mm > 50:
        confidence_boost += 10
        correlation_factors.append(f"Extreme rainfall ({rainfall_mm}mm) exceeds 50mm threshold")
    if congestion_pct > 80:
        confidence_boost += 5
        correlation_factors.append(f"Severe congestion ({congestion_pct}%) exceeds 80% threshold")
    if traffic_speed_drop > 70:
        confidence_boost += 5
        correlation_factors.append(f"Traffic speed drop ({traffic_speed_drop:.0f}%) exceeds 70% threshold")
    if gov_alert_exists:
        confidence_boost += 10
        correlation_factors.append("Government alert/advisory active")

    # ── Severity escalation (first match wins) ──
    escalated_severity = "LOW"

    if nearby_reports >= 12 and rainfall_mm > 50 and gov_alert_exists:
        escalated_severity = "CRITICAL"
        confidence_boost += 5
    elif nearby_reports >= 8 and rainfall_mm > 50 and congestion_pct > 80 and gov_alert_exists:
        escalated_severity = "CRITICAL"
    elif nearby_reports >= 8 and rainfall_mm > 50 and congestion_pct > 80:
        escalated_severity = "HIGH"
    elif nearby_reports >= 5 and rainfall_mm > 50 and gov_alert_exists:
        escalated_severity = "HIGH"
    elif nearby_reports >= 5 and rainfall_mm > 50:
        escalated_severity = "MEDIUM"
    elif nearby_reports >= 3:
        escalated_severity = "MEDIUM"

    # Cap at 40
    confidence_boost = min(confidence_boost, 40)

    return {
        "report_cluster_count": nearby_reports,
        "time_window_minutes": 15,
        "confidence_boost": confidence_boost,
        "escalated_severity": escalated_severity,
        "correlation_factors": correlation_factors
    }


# ─────────────────────────────────────────────────────────────────
# PART B — Agent 1: Signal Intelligence
# ─────────────────────────────────────────────────────────────────

SYSTEM_INSTRUCTION = (
    "You are the Signal Intelligence Agent in CIRO (Crisis Intelligence & "
    "Response Orchestrator). Your job is to process raw crisis signals and "
    "extract structured intelligence. Return ONLY valid JSON. No markdown. "
    "No backticks. If a field is unknown use null. Never omit a required field."
)


def agent_signal_intelligence(social_reports, location, session_id,
                              reprocessing_note=None) -> dict:
    client = get_client()
    log_step(session_id, 1, "Agent 1: Signal Intelligence started")

    # Step 2 — fetch weather
    weather = fetch_weather(location)

    # Step 3 — fetch traffic
    traffic = generate_traffic_data(location)

    # Step 4 — government reports (realistic mocks)
    gov_reports = [
        {
            "source": "NDMA Advisory",
            "text": f"NDMA has issued flood warning for {location} sector. Residents advised to avoid low-lying areas.",
            "severity": "HIGH"
        },
        {
            "source": "Dawn News",
            "text": f"Severe waterlogging reported in {location}, multiple roads blocked according to local authorities.",
            "severity": "HIGH"
        }
    ]

    # Step 5 — GeoTemporal Correlation
    geo_correlation = run_geo_temporal_correlation(
        social_reports, location, weather, traffic, gov_alert_exists=True
    )

    # Step 6 — Historical incident lookup
    match = find_historical_match(location)
    historical_context = build_historical_context_string(match)

    # Step 7 — Build Gemini prompt
    prompt = f"""
Analyze these crisis signals for {location}, Islamabad, Pakistan.

SOCIAL REPORTS ({len(social_reports)} reports):
{chr(10).join(f'{i+1}. {r}' for i, r in enumerate(social_reports))}

WEATHER DATA:
{json.dumps(weather, indent=2)}

TRAFFIC DATA:
{json.dumps(traffic, indent=2)}

GOVERNMENT REPORTS:
{chr(10).join(f'- [{r["source"]}] {r["text"]}' for r in gov_reports)}

ANOMALY BASELINES (Islamabad normal conditions):
- Rainfall normal: <7mm/h | Anomaly threshold: >=7mm/h
- Wind normal: <25km/h | Anomaly threshold: >=25km/h
- Visibility normal: >5km | Anomaly threshold: <5km
- Congestion normal: <30% | Anomaly threshold: >=30%
- Traffic speed normal: 40-60km/h | Anomaly threshold: <20km/h

GEOTEMPORAL ANALYSIS:
{json.dumps(geo_correlation, indent=2)}

HISTORICAL CONTEXT:
{historical_context}

{f"REPROCESSING GUIDANCE: {reprocessing_note}" if reprocessing_note else ""}

Return this exact JSON structure:
{{
  "processed_reports": [
    {{
      "original_text": "exact report text",
      "language": "roman_urdu|urdu|english|mixed",
      "location_mentioned": "location string or null",
      "crisis_indicators": ["list", "of", "indicators"],
      "urgency": "HIGH|MEDIUM|LOW",
      "entities": ["people", "vehicles", "infrastructure"],
      "timestamp_indicator": "time reference or null"
    }}
  ],
  "cluster_analysis": {{
    "primary_location": "location name",
    "location_matches": {geo_correlation["report_cluster_count"]},
    "temporal_cluster": true,
    "cluster_score": "HIGH|MEDIUM|LOW",
    "cluster_reasoning": "explanation"
  }},
  "anomalies_detected": [
    "Rainfall Xmm is Yx above baseline of Zmm"
  ],
  "signal_quality": "HIGH|MEDIUM|LOW",
  "quality_reasoning": "explanation"
}}
"""

    # Step 8 — Call Gemini, parse response
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.3
            )
        )
        parsed = parse_gemini_json(response.text)

        # Step 9 — Build signal_bundle
        cluster_score = parsed.get("cluster_analysis", {}).get("cluster_score", "LOW")
        anomalies = parsed.get("anomalies_detected", [])

        signal_bundle = {
            "location": location,
            "social_reports": parsed.get("processed_reports", []),
            "weather": weather,
            "traffic": traffic,
            "gov_reports": gov_reports,
            "processed_signals": parsed,
            "cluster_score": cluster_score,
            "anomalies": anomalies,
            "geo_correlation": geo_correlation,
            "historical_match": match
        }

        # Log completion
        log_step(session_id, 2,
                 f"Agent 1 complete: cluster={cluster_score}, anomalies={len(anomalies)}")
        log_agent_trace(
            session_id=session_id,
            agent_name="signal_intelligence",
            input_summary=f"{len(social_reports)} reports for {location}",
            output_summary=f"cluster={cluster_score}, anomalies={len(anomalies)}, geo_severity={geo_correlation['escalated_severity']}",
            gemini_prompt=prompt[:500],
            gemini_response=response.text[:500],
            decision=f"Signal quality: {parsed.get('signal_quality', 'N/A')}",
            status="success"
        )

        return signal_bundle

    except Exception as e:
        # Fallback — Gemini call or parsing failed
        match_count = count_location_matches(social_reports, location)
        if match_count >= 3:
            keyword_score = "HIGH"
        elif match_count >= 1:
            keyword_score = "MEDIUM"
        else:
            keyword_score = "LOW"

        signal_bundle = {
            "location": location,
            "social_reports": [],
            "weather": weather,
            "traffic": traffic,
            "gov_reports": gov_reports,
            "processed_signals": {},
            "cluster_score": keyword_score,
            "anomalies": [],
            "signal_quality": "LOW",
            "quality_reasoning": f"Gemini error: {str(e)}",
            "geo_correlation": geo_correlation,
            "historical_match": match
        }

        log_step(session_id, 2,
                 f"Agent 1 error fallback: cluster={keyword_score}, error={str(e)[:100]}")
        log_agent_trace(
            session_id=session_id,
            agent_name="signal_intelligence",
            input_summary=f"{len(social_reports)} reports for {location}",
            output_summary=f"Fallback: cluster={keyword_score}",
            gemini_prompt=prompt[:500] if prompt else "",
            gemini_response="",
            decision=f"error: {str(e)[:200]}",
            status="error"
        )

        return signal_bundle
