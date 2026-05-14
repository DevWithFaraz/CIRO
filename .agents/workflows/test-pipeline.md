---
name: Test Pipeline
description: Run the full CIRO backend test suite
---

# Test Suite

## Test 1 — Health
curl http://localhost:5000/health
Expected: 200 with agent list

## Test 2 — HIGH confidence
curl -X POST http://localhost:5000/analyse -H "Content-Type: application/json" -d "{\"location\":\"G-10\",\"social_reports\":[\"G-10 mein pani bhar gaya hai\",\"Flooding near G-10 markaz\",\"G-10 ka main boulevard band hai\"]}"
Expected: confidence_level HIGH, action_plan with 3 keys

## Test 3 — LOW confidence triggers re-analysis
curl -X POST http://localhost:5000/analyse -H "Content-Type: application/json" -d "{\"location\":\"G-10\",\"social_reports\":[\"I think I saw some water near a road\"]}"
Expected: step_log contains step 5.5

## Test 4 — Empty reports
curl -X POST http://localhost:5000/analyse -H "Content-Type: application/json" -d "{\"location\":\"G-10\",\"social_reports\":[]}"
Expected: 400

## Test 5 — Missing location
curl -X POST http://localhost:5000/analyse -H "Content-Type: application/json" -d "{\"social_reports\":[\"flood\"]}"
Expected: 400
