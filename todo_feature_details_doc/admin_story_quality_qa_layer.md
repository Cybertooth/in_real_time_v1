# Feature Implementation Spec: Story Quality QA Layer

## 1. Feature Overview
**Target Application:** Director Studio backend and admin review surfaces  
**Objective:** Add a reusable quality-assurance layer that flags weak story runs before they reach users, with special emphasis on first-session hook quality.

This feature is broader than the Tension Simulator. It is the quality gate for narrative coherence, artifact usefulness, and emotional pull.

## 2. Why This Matters
- Better story quality directly improves acquisition and first-session love.
- Intern or pipeline changes can silently degrade narrative quality.
- Human reviewers need an automated first pass that catches obvious problems early.

## 3. QA Dimensions
The QA layer should score or flag:
- premise clarity
- continuity contradictions
- character consistency
- artifact usefulness
- redundancy / exposition bloat
- weak opening
- weak closing beat for the current stage
- tone mismatch
- schema correctness
- visual/audio opportunity gaps

## 4. Output Contract
Return a structured QA report:
```json
{
  "status": "warning",
  "score": 74,
  "findings": [
    {
      "severity": "high",
      "category": "opening_hook",
      "message": "The first three artifacts explain context but do not create urgency."
    }
  ],
  "recommended_fixes": [
    "Insert a concrete suspicious artifact before the second journal",
    "Shorten the exposition in the first journal by 30%"
  ]
}
```

## 5. QA Passes
Implement as multiple passes instead of one giant evaluator.

Suggested passes:
1. `OpeningHookPass`
2. `ContinuityPass`
3. `CharacterVoicePass`
4. `ArtifactDiversityPass`
5. `RedundancyPass`
6. `SchemaPass`

Each pass should emit:
- score
- findings
- recommendations

## 6. Architecture Placement
This belongs in the backend evaluation flow after generation.

Suggested files:
- `python_director/logic.py`
- `python_director/models.py`
- `python_director/api.py`

Suggested storage:
- attach QA report to run metadata / artifact files in `temp_artifacts/<run_id>/`

## 7. Rule-Based Checks
Add deterministic checks before LLM review:
- opening artifacts count
- repeated artifact type streaks
- missing `title/body/content` fields
- empty transcripts
- identical or near-identical artifact content
- too many artifacts of one type
- no suspicious/high-signal artifact in first 5 items

## 8. LLM Review Checks
Use strict prompts for:
- opening hook quality
- character motivation clarity
- emotional texture
- whether artifacts feel diegetic vs generic
- whether the story invites curiosity

Return structured JSON only.

## 9. Admin UI Requirements
Add a `QA Review` panel in run detail.

Sections:
- overall score
- pass/fail chips by category
- high-severity findings
- click-through examples tied to exact artifacts
- suggested rewrite actions

Useful UX:
- a finding should link to the relevant block or artifact
- reviewer can mark finding as accepted / ignored later in future phases

## 10. Publish Gating Behavior
Phase 1:
- warnings only

Phase 2:
- block publish if:
  - schema pass fails
  - continuity fails critically
  - opening hook is below minimum threshold

## 11. Implementation Steps
1. Define QA report models and frontend types.
2. Implement deterministic pre-checks.
3. Implement separate evaluator prompts per pass.
4. Aggregate results into one report.
5. Save report with run metadata.
6. Add API endpoint:
   - `POST /runs/{run_id}/qa`
   - `GET /runs/{run_id}/qa`
7. Add admin UI review component.

## 12. Suggested Thresholds
- `score >= 85`: strong
- `70-84`: warning
- `< 70`: weak

Critical publish blockers:
- schema invalid
- continuity contradiction in core premise
- first-session hook score below 5/10

## 13. Acceptance Criteria
- Any completed run can generate QA findings.
- Findings are specific enough for a junior engineer or writer to act on.
- Admin UI shows exact failure reasons, not just one overall number.

## 14. Testing & Verification
- Create sample weak outputs intentionally:
  - repetitive journals
  - contradictory names
  - empty phone transcript
  - generic opening
- Confirm each pass surfaces the expected issue.

## 15. Future Enhancements
- auto-generated fix prompts
- one-click rewrite suggestions
- QA score history across pipeline versions
- use QA report during regression tests and compare view
