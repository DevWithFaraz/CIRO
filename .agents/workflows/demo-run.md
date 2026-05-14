---
name: Demo Run
description: Trigger a full HIGH confidence demo scenario
---

# Demo Run

curl -X POST http://localhost:5000/analyse -H "Content-Type: application/json" -d "{\"location\":\"G-10\",\"social_reports\":[\"G-10 mein pani bhar gaya hai, gaariyan phans gayi hain\",\"Heavy flooding near G-10 markaz, roads completely blocked\",\"G-10 ka main boulevard band hai, emergency situation hai\"]}"

After running: open Firebase Console, crisis_sessions collection, verify:
- agent_trace has 5+ entries
- before_state and after_state both populated with 8 numeric fields
- action_plan has rerouting + dispatch + alert
- step_log has 9+ steps
