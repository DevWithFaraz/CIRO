---
name: City-State Simulation Engine
description: How CityStateSimulator computes before/after metrics
---

# Simulation Engine

## Location
backend/simulation/city_state_simulator.py

## Before State (8 metrics)
congestion_pct, avg_speed_kmh, vehicles_stranded, ambulance_eta_minutes,
citizens_at_risk, severity_level, roads_blocked, emergency_teams

## Action Impact
- rerouting:  congestion -20 to -36%, speed +8 to +18 km/h
- dispatch:   ambulance_eta -10 to -18 min, vehicles_stranded -15 to -30
- alert:      citizens_at_risk -400 to -900, congestion -5 to -12%

## Severity Rules
- congestion > 60% = CRITICAL | 35-60% = HIGH | < 35% = MEDIUM

## Clamp Rules
- congestion: max(25, min(result, 95))
- speed: max(8, min(result, 35))
- vehicles_stranded: max(3, result)
- ambulance_eta: max(5, result)
- citizens_at_risk: max(100, result)
