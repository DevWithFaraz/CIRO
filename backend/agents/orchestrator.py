import os
import json
import time
from datetime import datetime
from constants import (AGENT_ORCHESTRATOR, COLLECTION_SESSIONS,
                       AGENT_SIGNAL_INTEL, AGENT_CRISIS_ANALYST)
from services.gemini_service import generate_content, parse_gemini_json
from services.firebase_service import get_db
from utils import log_step, log_agent_trace
from agents.signal_intelligence import agent_signal_intelligence
from agents.crisis_analyst import agent_crisis_analyst
from agents.response_commander import agent_response_commander
from simulation.city_state_simulator import run_city_simulation

def agent_orchestrator(social_reports: list, location: str, session_id: str) -> dict:
    try:
        # STEP 0 — Start
        log_step(session_id, 0, f'Orchestrator: received {len(social_reports)} reports for {location}. Starting pipeline.')
        log_agent_trace(
            session_id=session_id,
            agent_name=AGENT_ORCHESTRATOR,
            input_summary=f'{len(social_reports)} reports, location={location}',
            output_summary='Pipeline starting',
            gemini_prompt='',
            gemini_response='',
            decision='Invoking Signal Intelligence Agent',
            status='starting'
        )

        # STEP 1 — Call Signal Intelligence
        signal_bundle = agent_signal_intelligence(social_reports, location, session_id)
        time.sleep(0.5)

        # CHECKPOINT 1 — Evaluate signal quality
        log_step(session_id, 2.5, 'Orchestrator: evaluating signal quality...')
        
        prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'orchestrator_prompt.txt')
        with open(prompt_path, 'r') as f:
            content = f.read()
        
        eval1_start = content.find('---SIGNAL_EVAL_START---') + len('---SIGNAL_EVAL_START---')
        eval1_end = content.find('---SIGNAL_EVAL_END---')
        eval1_template = content[eval1_start:eval1_end].strip()

        processed = signal_bundle.get('processed_signals', {})
        eval1_prompt = eval1_template
        eval1_prompt = eval1_prompt.replace('{cluster_score}', str(signal_bundle.get('cluster_score', 'LOW')))
        eval1_prompt = eval1_prompt.replace('{cluster_reasoning}', str(processed.get('cluster_analysis', {}).get('cluster_reasoning', 'N/A')))
        eval1_prompt = eval1_prompt.replace('{signal_quality}', str(processed.get('signal_quality', 'N/A')))
        eval1_prompt = eval1_prompt.replace('{quality_reasoning}', str(processed.get('quality_reasoning', 'N/A')))
        eval1_prompt = eval1_prompt.replace('{num_processed}', str(len(processed.get('processed_reports', []))))
        eval1_prompt = eval1_prompt.replace('{num_raw_reports}', str(len(social_reports)))
        eval1_prompt = eval1_prompt.replace('{num_anomalies}', str(len(signal_bundle.get('anomalies', []))))
        eval1_prompt = eval1_prompt.replace('{weather_alert}', str(signal_bundle.get('weather', {}).get('alert_level', 'None')))

        eval1_response = generate_content(eval1_prompt) or ''
        try:
            eval1 = parse_gemini_json(eval1_response)
        except Exception:
            eval1 = {'decision': 'proceed', 'reasoning': 'Fallback: parse error — defaulting to proceed', 'guidance': ''}

        log_agent_trace(
            session_id=session_id,
            agent_name=AGENT_ORCHESTRATOR,
            input_summary='Signal bundle evaluation',
            output_summary=json.dumps(eval1)[:500],
            gemini_prompt=eval1_prompt[:500],
            gemini_response=eval1_response[:500],
            decision=f"Checkpoint 1 decision: {eval1.get('decision')}",
            status=eval1.get('decision', 'proceed')
        )

        if eval1.get('decision') == 'reprocess':
            log_step(session_id, 2.6, f'Orchestrator: requesting reprocessing — {eval1.get("reasoning","")}')
            signal_bundle = agent_signal_intelligence(
                social_reports, location, session_id,
                reprocessing_note=eval1.get('guidance', '')
            )
            log_step(session_id, 2.7, 'Reprocessing complete')

        time.sleep(0.5)

        # STEP 2 — Call Crisis Analyst
        situation_report = agent_crisis_analyst(signal_bundle, session_id)
        time.sleep(0.5)

        # CHECKPOINT 2 — Evaluate analysis quality
        log_step(session_id, 5, 'Orchestrator: evaluating analysis quality...')
        
        eval2_start = content.find('---ANALYSIS_EVAL_START---') + len('---ANALYSIS_EVAL_START---')
        eval2_end = content.find('---ANALYSIS_EVAL_END---')
        eval2_template = content[eval2_start:eval2_end].strip()

        eval2_prompt = eval2_template
        eval2_prompt = eval2_prompt.replace('{crisis_type}', str(situation_report.get('crisis_type', '?')))
        eval2_prompt = eval2_prompt.replace('{confidence_level}', str(situation_report.get('confidence_level', '?')))
        eval2_prompt = eval2_prompt.replace('{confidence_score}', str(situation_report.get('confidence_score', 0)))
        eval2_prompt = eval2_prompt.replace('{reasoning}', str(situation_report.get('reasoning', '')))
        eval2_prompt = eval2_prompt.replace('{anomalies_found}', str(situation_report.get('anomalies_found', [])))
        eval2_prompt = eval2_prompt.replace('{cluster_evidence}', str(situation_report.get('cluster_evidence', '')))
        eval2_prompt = eval2_prompt.replace('{cluster_score}', str(signal_bundle.get('cluster_score', 'LOW')))
        eval2_prompt = eval2_prompt.replace('{num_reports}', str(len(social_reports)))
        eval2_prompt = eval2_prompt.replace('{weather_alert}', str(signal_bundle.get('weather', {}).get('alert_level', 'None')))

        eval2_response = generate_content(eval2_prompt) or ''
        try:
            eval2 = parse_gemini_json(eval2_response)
        except Exception:
            conf = situation_report.get('confidence_score', 0)
            eval2 = {
                'decision': 'proceed' if conf >= 40 else 're-analyse',
                'reasoning': f'Fallback: confidence={conf} — defaulting to {"proceed" if conf >= 40 else "re-analyse"}',
                'guidance': 'Focus on weather as primary signal'
            }

        log_agent_trace(
            session_id=session_id,
            agent_name=AGENT_ORCHESTRATOR,
            input_summary='Situation report evaluation',
            output_summary=json.dumps(eval2)[:500],
            gemini_prompt=eval2_prompt[:500],
            gemini_response=eval2_response[:500],
            decision=f"Checkpoint 2 decision: {eval2.get('decision')}",
            status=eval2.get('decision', 'proceed')
        )

        if eval2.get('decision') == 're-analyse':
            log_step(session_id, 5.5, f'Orchestrator: requesting re-analysis — {eval2.get("reasoning","")}')
            situation_report = agent_crisis_analyst(
                signal_bundle, session_id,
                reanalysis_note=eval2.get('guidance', '')
            )
            log_step(session_id, 5.6, f'Re-analysis complete: confidence now {situation_report.get("confidence_score")}%')

        time.sleep(0.5)

        # STEP 3 — Call Response Commander
        action_plan = agent_response_commander(situation_report, session_id)
        time.sleep(0.5)

        # STEP 4 — Run City Simulation
        log_step(session_id, 8, 'Orchestrator: running city-state simulation...')
        city_state = run_city_simulation(signal_bundle.get('traffic', {}), action_plan)

        # Write to Firebase
        db = get_db()
        db.collection(COLLECTION_SESSIONS).document(session_id).update({
            'signal_bundle': signal_bundle,
            'situation_report': situation_report,
            'action_plan': action_plan,
            'city_state': city_state,
            'before_state': city_state.get('before', {}),
            'after_state': city_state.get('after', {}),
        })

        log_step(session_id, 9, 'Orchestrator: pipeline complete. All agents ran successfully.')

        log_agent_trace(
            session_id=session_id,
            agent_name=AGENT_ORCHESTRATOR,
            input_summary=f'Full pipeline: {len(social_reports)} reports → 4 agents → simulation',
            output_summary=f'{situation_report.get("crisis_type")} detected, {len(action_plan.get("actions", {}).get("rerouting", [])) + len(action_plan.get("actions", {}).get("dispatch", [])) + len(action_plan.get("actions", {}).get("alert", []))} actions, city_state written',
            gemini_prompt='',
            gemini_response='',
            decision='Pipeline complete',
            status='success'
        )

        # STEP 5 — Return
        return {
            'session_id': session_id,
            'situation_report': situation_report,
            'action_plan': action_plan,
            'city_state': city_state,
            'simulated_outcome': city_state.get('after', {}),
            'orchestrator_evaluations': {
                'signal_checkpoint': eval1,
                'analysis_checkpoint': eval2,
            },
            'signal_bundle_summary': {
                'cluster_score': signal_bundle.get('cluster_score', 'LOW'),
                'anomalies_count': len(signal_bundle.get('anomalies', [])),
                'signal_quality': signal_bundle.get('processed_signals', {})
                                .get('signal_quality', 'unknown'),
                'geo_correlation': signal_bundle.get('geo_correlation', {})
            }
        }

    except Exception as e:
        log_step(session_id, 99, f'Pipeline error: {str(e)}')
        raise e
