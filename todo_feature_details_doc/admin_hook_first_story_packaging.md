# Feature Implementation Spec: Hook-First Story Packaging

## 1. Feature Overview
**Target Application:** Director Studio (`python_director/`, `admin_ui_v3/`) and Flutter Client display surfaces  
**Objective:** Package every story with a clear, irresistible hook so users understand the premise instantly in the gallery, onboarding, and catch-up surfaces.

This is a packaging system, not just a design tweak. The story needs a marketable promise before the user reads a single artifact.

## 2. Why This Matters
- Users decide whether to continue based on premise clarity and emotional intrigue.
- Current story metadata is not sufficient for conversion-oriented presentation.
- Story quality alone is not enough if the app cannot present why a story is worth starting.

## 3. Core Principle
Every story needs:
- one sentence hook
- one emotional promise
- one strongest artifact preview
- one clear reason to tap now

## 4. Required New Metadata
Add packaging fields to the story object persisted in Firestore and available in Director Studio.

Suggested fields:
```json
{
  "hookLine": "A newly engaged woman begins documenting the week she decides to kill her fiance.",
  "promiseLine": "You will uncover whether she is delusional, lying, or absolutely right.",
  "heroArtifactType": "chat",
  "heroArtifactPreview": {
    "title": "You need to see this",
    "body": "Don't call me again. They already know."
  },
  "toneTags": ["obsessive", "romantic", "dangerous"],
  "audienceHookType": "twisted-romance"
}
```

## 5. Places This Metadata Must Be Used
- Flutter story gallery cards
- cold open onboarding
- binge-to-live entry
- catch-up capsule headline fallback
- deployment preview in Director Studio

## 6. Admin UI Requirements
Add a `Story Packaging` section in the run upload/publish flow and deployment view.

Fields:
- Hook line
- Promise line
- Tone tags
- Hero artifact selector
- Hero artifact preview editor
- Thumbnail/headline image preview

The UI should preview:
- gallery card
- cold open card
- "continue story" card

## 7. Backend Requirements
- Extend upload pipeline so story packaging is:
  - generated automatically if missing
  - editable by admin before publish
  - stored on the story document

Suggested location for generation:
- post-run finalization step after `final_output` is assembled

## 8. ML Generation Strategy
Use a cheap structured LLM pass to produce packaging candidates:
- hookLine
- promiseLine
- topArtifactRecommendation
- audienceHookType

Prompt should optimize for:
- curiosity
- specificity
- emotional contradiction
- no vague genre boilerplate

Reject weak outputs such as:
- "A thrilling mystery unfolds..."
- "A suspenseful tale of secrets..."

## 9. Implementation Steps
1. Extend backend story model and upload payload shape.
2. Add packaging generation helper in `python_director/logic.py` or equivalent post-processing layer.
3. Extend `uploadRun` endpoint response/input to carry packaging fields.
4. Update admin types in [types.ts](G:/code/gen-ai/in_real_time_v1/python_director/admin_ui_v3/src/types.ts).
5. Add editor UI in run detail before/around upload flow.
6. Add gallery consumption support in Flutter story models.
7. Update story gallery card to favor `hookLine` and `promiseLine`.

## 10. Validation Rules
- `hookLine`: max 140 chars
- `promiseLine`: max 140 chars
- tone tags: 1-4 items
- hero artifact preview must point to a real artifact type and real content

## 11. Acceptance Criteria
- Every published story can surface a hook line in the client.
- Packaging is editable in admin before publish.
- Auto-generated packaging is never empty.
- The gallery no longer relies primarily on generic setup text.

## 12. Testing & Verification
- Publish a story and confirm packaging fields appear on Firestore story document.
- Verify Flutter gallery renders hook/promise lines.
- Verify admin preview matches client layout closely.
- Manual QA should reject at least 3 weak generated hook examples.

## 13. Future Enhancements
- multi-variant hooks for A/B testing
- localized hook copy
- genre-specific packaging templates
- auto-select strongest artifact thumbnail from critic scores
