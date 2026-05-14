---
name: Emergency Analysis
description: Quick crisis analysis for any Pakistan location
---

# Emergency Analysis

Replace LOCATION, REPORT1, REPORT2 with real values.

curl -X POST http://localhost:5000/analyse -H "Content-Type: application/json" -d "{\"location\":\"LOCATION\",\"social_reports\":[\"REPORT1\",\"REPORT2\"]}"

Test locations: G-10, F-8, G-9, I-8, E-7
Roman Urdu phrases: pani bhar gaya (flooding), gaariyan phans gayi (vehicles stuck), rasta band hai (road blocked)
