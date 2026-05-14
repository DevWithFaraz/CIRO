---
name: Crisis Detection Domain Knowledge
description: Domain expertise for crisis signals and Islamabad geography
---

# Crisis Detection

## Signal Sources
1. Social media — Roman Urdu, Urdu, English, mixed
2. Weather — OpenWeatherMap, field: rain['1h'] NEVER rainfall_mm_last_hour
3. Traffic — dynamic simulation from traffic_service.py
4. Government — NDMA advisories, Dawn News format

## Islamabad Baselines
- Normal rainfall: < 7 mm/h | SEVERE: > 20 | EXTREME: > 50
- Normal congestion: < 30% | Crisis: > 75%
- Normal speed: 40-60 km/h | Crisis: < 10 km/h

## G-10 Coordinates
- G-10 Markaz:  33.6844, 72.9857
- G-10/1:       33.6831, 72.9812
- G-10/3:       33.6807, 72.9741
- G-9 Markaz:   33.6910, 72.9857
- G-11:         33.6865, 72.9741

## Crisis Types
flood | heatwave | accident | road_blockage | infrastructure_failure | unknown
