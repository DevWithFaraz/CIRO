import json
from google import genai
from services.firebase_service import find_historical_match, build_historical_context_string
from services.gemini_service import parse_gemini_json, get_client
from utils import log_step, log_agent_trace
from constants import GEMINI_MODEL

SYSTEM_INSTRUCTION = (
    "You are the Crisis Analysis Agent in CIRO (Crisis Intelligence & "
    "Response Orchestrator). You MUST connect ALL signal sources — social "
    "reports, weather data, traffic data, and government alerts — in your "
    "reasoning. Return ONLY valid JSON. No markdown. No backticks. "
    "If a field is unknown use null. Never omit a required field."
)


def agent_crisis_analyst(signal_bundle, session_id,
                         reanalysis_note=None) -> dict:
    client = get_client()
    log_step(session_id, 3, "Agent 2: Crisis Analyst started")

    # Extract data from signal_bundle
    location = signal_bundle.get("location", "Unknown")
    processed_reports = signal_bundle.get("social_reports", [])
    weather = signal_bundle.get("weather", {})
    traffic = signal_bundle.get("traffic", {})
    gov_reports = signal_bundle.get("gov_reports", [])
    cluster_score = signal_bundle.get("cluster_score", "LOW")
    anomalies = signal_bundle.get("anomalies", [])
    geo_correlation = signal_bundle.get("geo_correlation", {})

    # Query historical incidents
    match = find_historical_match(location)
    historical_context = build_historical_context_string(match)

    # Build Gemini prompt
    prompt = f"""
You are analyzing a crisis situation in {location}, Islamabad, Pakistan.
Your job is to synthesize ALL signal sources into a unified situation report.

PROCESSED SOCIAL REPORTS ({len(processed_reports)} reports):
{json.dumps(processed_reports, indent=2)}

WEATHER DATA:
{json.dumps(weather, indent=2)}

TRAFFIC DATA:
{json.dumps(traffic, indent=2)}

GOVERNMENT REPORTS:
{chr(10).join(f'- [{r.get("source", "Unknown")}] {r.get("text", "")}' for r in gov_reports)}

SIGNAL CLUSTER SCORE: {cluster_score}
ANOMALIES DETECTED: {json.dumps(anomalies, indent=2)}

GEOTEMPORAL CORRELATION:
{json.dumps(geo_correlation, indent=2)}

HISTORICAL CONTEXT:
{historical_context}

{f"RE-ANALYSIS GUIDANCE: {reanalysis_note}" if reanalysis_note else ""}

CRITICAL INSTRUCTION: Your reasoning MUST explicitly reference ALL 4 signal
sources (social reports, weather, traffic, government alerts). If you skip
any source, your analysis is INVALID.

Return this exact JSON structure:
{{
  "crisis_type": "flood|heatwave|accident|road_blockage|infrastructure_failure|unknown",
  "location": "{location}",
  "confidence_level": "HIGH|MEDIUM|LOW",
  "confidence_score": 0-100,
  "reasoning": "Multi-paragraph explanation connecting ALL 4 sources",
  "severity": {{
    "people_affected": 0,
    "km_affected": 0.0
  }},
  "impact": [
    "Impact statement 1",
    "Impact statement 2"
  ],
  "cluster_evidence": "Evidence from report clustering and geotemporal analysis",
  "anomalies_found": [
    "Quantified anomaly string"
  ],
  "historical_context": "{historical_context}"
}}
"""

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

        # Build situation_report from parsed response
        situation_report = {
            "crisis_type": parsed.get("crisis_type", "unknown"),
            "location": parsed.get("location", location),
            "confidence_level": parsed.get("confidence_level", "LOW"),
            "confidence_score": parsed.get("confidence_score", 0),
            "reasoning": parsed.get("reasoning", ""),
            "severity": parsed.get("severity", {"people_affected": 0, "km_affected": 0.0}),
            "impact": parsed.get("impact", []),
            "cluster_evidence": parsed.get("cluster_evidence", ""),
            "anomalies_found": parsed.get("anomalies_found", []),
            "historical_context": parsed.get("historical_context", historical_context)
        }

        crisis_type = situation_report["crisis_type"]
        confidence = situation_report["confidence_score"]

        # Apply GeoTemporal confidence boost
        geo_boost = geo_correlation.get("confidence_boost", 0)
        situation_report["confidence_score"] = min(100, confidence + geo_boost)
        situation_report["geo_temporal_boost_applied"] = geo_boost

        # Log completion
        log_step(session_id, 4,
                 f"Agent 2 complete: crisis_type={crisis_type}, confidence={situation_report['confidence_score']}")
        log_agent_trace(
            session_id=session_id,
            agent_name="crisis_analyst",
            input_summary=f"signal_bundle for {location}, cluster={cluster_score}",
            output_summary=f"crisis_type={crisis_type}, confidence={situation_report['confidence_score']}, severity={situation_report['severity']}",
            gemini_prompt=prompt[:500],
            gemini_response=response.text[:500],
            decision=f"Crisis: {crisis_type} at confidence {situation_report['confidence_score']}",
            status="success"
        )

        return situation_report

    except Exception as e:
        # Fallback — Gemini call or parsing failed
        situation_report = {
            "crisis_type": "unknown",
            "location": location,
            "confidence_level": "LOW",
            "confidence_score": 0,
            "reasoning": f"Analysis error: {str(e)}",
            "severity": {"people_affected": 0, "km_affected": 0.0},
            "impact": [],
            "cluster_evidence": "",
            "anomalies_found": [],
            "historical_context": historical_context
        }

        log_step(session_id, 4,
                 f"Agent 2 error fallback: crisis_type=unknown, error={str(e)[:100]}")
        log_agent_trace(
            session_id=session_id,
            agent_name="crisis_analyst",
            input_summary=f"signal_bundle for {location}",
            output_summary="Fallback: crisis_type=unknown, confidence=0",
            gemini_prompt=prompt[:500] if prompt else "",
            gemini_response="",
            decision=f"error: {str(e)[:200]}",
            status="error"
        )

        return situation_report
