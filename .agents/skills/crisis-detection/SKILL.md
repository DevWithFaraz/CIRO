---
name: Crisis Detection Domain Knowledge
description: Domain expertise for crisis signals and Islamabad geography
---

# Crisis Detection Domain Knowledge

## Signal Sources

CIRO ingests 4 signal sources for every analysis:

| Source | Provider | Data Shape |
|--------|----------|------------|
| Social Reports | User input (Roman Urdu, Urdu, English, mixed) | `list[str]` |
| Weather | OpenWeatherMap API (`rain['1h']`) | `WeatherData` dict |
| Traffic | TomTom / Google Maps / simulated fallback | `TrafficData` dict |
| Government | Hardcoded NDMA + Dawn News mocks | `list[GovReport]` |

### WeatherData Fields
```
location, rainfall_mm_1h, alert_level, wind_kmh, visibility_km,
description, humidity_pct, is_fallback
```

### TrafficData Fields
```
location, congestion_pct, avg_speed_kmh, normal_speed_kmh,
incidents, data_source
```

### GovReport Fields
```
source, text, severity
```

## Anomaly Baselines (Islamabad Normal Conditions)

| Metric | Normal Range | Anomaly Threshold | Crisis Threshold |
|--------|-------------|-------------------|-----------------|
| Rainfall | < 7 mm/h | ≥ 7 mm/h | ≥ 50 mm/h (EXTREME) |
| Wind Speed | < 25 km/h | ≥ 25 km/h | — |
| Visibility | > 5 km | < 5 km | < 1 km |
| Congestion | < 30% | ≥ 30% | > 80% |
| Traffic Speed | 40–60 km/h | < 20 km/h | < 8 km/h |

These baselines are defined in `backend/constants.py` as `BASELINES`:
```python
BASELINES = {
    'rainfall_normal_mmh': 7,
    'wind_normal_kmh': 25,
    'visibility_normal_km': 5,
    'congestion_normal_pct': 30,
    'traffic_speed_normal_kmh': 45
}
```

## Rain Classification (`classify_rain()`)

| Threshold (mm/h) | Classification |
|-------------------|---------------|
| ≥ 50 | EXTREME |
| ≥ 20 | SEVERE |
| ≥ 7 | HEAVY |
| ≥ 2 | MODERATE |
| < 2 | LIGHT |

## GeoTemporal Correlation Engine

Located in `backend/agents/signal_intelligence.py`. Runs BEFORE the Gemini call to provide pre-computed context.

### `count_location_matches(reports, location) -> int`

Normalizes location to lowercase and checks 3 variants:
1. `loc` — original lowercase (e.g. `"g-10"`)
2. `loc.replace('-', ' ')` — hyphen to space (e.g. `"g 10"`)
3. `loc.replace(' ', '-')` — space to hyphen (e.g. `"g-10"`)

Returns the count of reports containing any variant (case-insensitive).

### Confidence Boost Rules (Additive)

| Condition | Boost | Factor String |
|-----------|-------|---------------|
| `nearby_reports >= 3` | +10 | `"{N} reports cluster near {location}"` |
| `rainfall_mm > 50` | +10 | `"Extreme rainfall ({N}mm) exceeds 50mm threshold"` |
| `congestion_pct > 80` | +5 | `"Severe congestion ({N}%) exceeds 80% threshold"` |
| `traffic_speed_drop > 70%` | +5 | `"Traffic speed drop ({N}%) exceeds 70% threshold"` |
| `gov_alert_exists` | +10 | `"Government alert/advisory active"` |

**Maximum confidence_boost: 40** (capped after all rules + escalation bonus)

### Traffic Speed Drop Calculation
```python
traffic_speed_drop = ((normal_speed - avg_speed) / normal_speed) * 100
```

### Severity Escalation Table (First Match Wins)

| Priority | Conditions | Severity | Extra Boost |
|----------|-----------|----------|-------------|
| 1 | reports ≥ 12 AND rainfall > 50 AND gov_alert | CRITICAL | +5 |
| 2 | reports ≥ 8 AND rainfall > 50 AND congestion > 80 AND gov_alert | CRITICAL | — |
| 3 | reports ≥ 8 AND rainfall > 50 AND congestion > 80 | HIGH | — |
| 4 | reports ≥ 5 AND rainfall > 50 AND gov_alert | HIGH | — |
| 5 | reports ≥ 5 AND rainfall > 50 | MEDIUM | — |
| 6 | reports ≥ 3 | MEDIUM | — |
| 7 | (default) | LOW | — |

### GeoCorrelation Output
```python
{
    "report_cluster_count": int,
    "time_window_minutes": 15,   # fixed
    "confidence_boost": int,      # 0–40
    "escalated_severity": "CRITICAL|HIGH|MEDIUM|LOW",
    "correlation_factors": ["list of factor strings"]
}
```

## Cluster Scoring

The Gemini-derived `cluster_score` and the fallback keyword-based scoring:

| Match Count | Fallback Score |
|-------------|---------------|
| ≥ 3 reports | HIGH |
| ≥ 1 report | MEDIUM |
| 0 reports | LOW |

## G-10 Area Coordinates

All 6 reference points from `backend/constants.py`:

| Location | Latitude | Longitude |
|----------|----------|-----------|
| G-10 Markaz | 33.6844 | 72.9857 |
| G-10/1 | 33.6831 | 72.9812 |
| G-10/2 | 33.6820 | 72.9778 |
| G-10/3 | 33.6807 | 72.9741 |
| G-9 Markaz | 33.6910 | 72.9857 |
| G-11 | 33.6865 | 72.9741 |

## Islamabad Resources

From `backend/constants.py` `RESOURCES`:

| Category | Locations |
|----------|-----------|
| Fire Stations | F-8, G-9, I-8 |
| Hospitals | PIMS G-8, Shifa H-8 |
| Police Stations | Kohsar F-6, Margalla E-7 |
| Alert Channels | SMS, push notification, loudspeaker, radio |

## Historical Incident Memory

### Seeded Incidents (from `firebase_service.seed_historical_incidents()`)

| ID | Location | Crisis Type | Month | Severity | Cause | Effectiveness |
|----|----------|-------------|-------|----------|-------|---------------|
| INC_2025_G10_001 | G-10 | flood | July | HIGH | drainage overflow | 72% |
| INC_2025_I8_001 | I-8 | road_blockage | March | MEDIUM | accident on expressway | 85% |
| INC_2024_F6_001 | F-6 | heatwave | June | HIGH | prolonged heat spell | 61% |

### How Matching Works
`find_historical_match(db, location, crisis_type=None)`:
- Streams all docs from `historical_incidents` collection
- Checks if `location.lower()` is contained in doc's location (or vice versa)
- Optionally filters by `crisis_type`
- Returns first match as dict, or `None`
- Entire function wrapped in `try/except` → returns `None` on any error

### Context String Format
```
Current pattern matches the {month} {crisis_type} at {location}
(severity: {severity}, cause: {main_cause}, prior response
effectiveness: {response_effectiveness}%). Roads previously
affected: {roads_affected}.
```

## Crisis Types

The 6 allowed values for `crisis_type` in `situation_report`:

| Type | Description |
|------|-------------|
| `flood` | Urban flooding, waterlogging, drainage overflow |
| `heatwave` | Prolonged extreme heat |
| `accident` | Vehicle accidents, pile-ups |
| `road_blockage` | Roads blocked by debris, construction, protest |
| `infrastructure_failure` | Bridge collapse, power grid failure, pipe burst |
| `unknown` | Cannot determine crisis type (used in fallback) |
