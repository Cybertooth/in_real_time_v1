# Feature Implementation Spec: Tension Simulator

## 1. Feature Overview
**Target Application:** Director Studio (`python_director/`, `admin_ui_v3/`)  
**Objective:** Predict whether a story's opening stretch is compelling enough to hook a first-time user before the story is published.

This should answer a practical question:
"Will the first 24 hours of this story make a new user want to keep going?"

## 2. Why This Matters
- User acquisition is constrained by story quality and opening pace.
- A story can be technically valid and still fail to hook.
- Writers/admins need a visible pre-publish warning system for weak openings.

## 3. Core Scoring Dimensions
The simulator should score the first `24 hours` and first `10 artifacts` on:
- Hook Strength
- Clarity
- Tension Ramp
- Artifact Variety
- Emotional Pull
- Cliffhanger Strength
- Dead Zone Risk

## 4. Output Format
Produce a structured report:
```json
{
  "overall_hook_score": 7.8,
  "scores": {
    "hook_strength": 8,
    "clarity": 7,
    "tension_ramp": 6,
    "artifact_variety": 8,
    "emotional_pull": 7,
    "cliffhanger_strength": 9,
    "dead_zone_risk": 4
  },
  "warnings": [
    "No meaningful twist until artifact 6",
    "Two journal entries in a row slow pacing"
  ],
  "recommended_actions": [
    "Move receipt artifact earlier",
    "Replace second journal with a short chat interruption"
  ]
}
```

## 5. Architecture Placement
This should run after timeline/final output generation and before upload/publish.

Suggested backend integration points:
- run finalization path
- compare view enrichment
- upload readiness check

## 6. Backend Components
Suggested additions:
- `HookSimulationReport` model
- scoring helper in `python_director/logic.py`
- API support in `python_director/api.py`

Suggested endpoints:
- `POST /runs/{run_id}/simulate-hook`
- `GET /runs/{run_id}/hook-simulation`

## 7. Scoring Method
Phase 1 can use an LLM evaluator with a strict rubric.

Prompt should evaluate:
- how quickly the premise becomes legible
- whether something surprising happens early
- whether the first few artifacts create unanswered questions
- whether the artifact sequence feels repetitive
- whether a new user would likely continue after 3 minutes

Use structured JSON output only.

## 8. Additional Deterministic Checks
Do not rely only on LLM scoring.
Add rule-based metrics:
- count of artifacts in first 24h
- gap between first and second high-interest artifacts
- same-type repetition streaks
- presence of at least one strong "concrete evidence" artifact:
  - receipt
  - photo
  - voice note
  - phone call

## 9. Admin UI Requirements
Add a `Hook Readiness` panel to run detail and/or compare view.

Display:
- large overall score
- sub-score grid
- warnings list
- recommendations list
- mini timeline with highlighted dead zones

Optional visual:
- tension line over first 10 artifacts
- red shaded area where hook is weak

## 10. Implementation Steps
1. Define report types in backend and frontend.
2. Implement scoring prompt plus deterministic pre-checks.
3. Store report in run artifacts or run metadata.
4. Add API retrieval endpoint.
5. Add `HookReadinessCard` component in admin UI.
6. Add warning state to upload flow:
   - do not block publish in phase 1
   - but show high-risk warning if score below threshold

## 11. Thresholds
- `>= 8.0`: ready
- `6.0 - 7.9`: caution
- `< 6.0`: high risk

## 12. Acceptance Criteria
- A completed run can generate a hook simulation report.
- Admin UI renders the report without crashes.
- Low-hook runs produce actionable warnings, not vague criticism.

## 13. Testing & Verification
- Run simulator against a deliberately boring opening and confirm low score.
- Run simulator against a high-conflict opening and confirm higher score.
- Verify the same run produces broadly stable scores across repeated evaluations.

## 14. Future Enhancements
- compare hook scores across pipelines
- suggest exact artifact reorderings
- feed results into packaging and cold open selection
