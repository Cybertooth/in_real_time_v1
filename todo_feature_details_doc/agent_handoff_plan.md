# Agent Handoff Plan: Wave 1 Acquisition + Quality Features

## Goal
This handoff splits the first six highest-value features across three coding agents. The split is optimized for:
- minimal file overlap
- low dependency deadlock
- maximum impact on user acquisition and first-session hook

These are the six selected features:
1. `admin_hook_first_story_packaging.md`
2. `flutter_cold_open_onboarding.md`
3. `flutter_binge_to_live_entry.md`
4. `flutter_catch_up_capsule.md`
5. `admin_tension_simulator.md`
6. `admin_story_quality_qa_layer.md`

## Global Working Rules
- Do not edit unrelated files outside your assigned scope unless absolutely necessary.
- Do not overwrite another agent's work.
- If you need a shared model/type changed, do it minimally and document it in your final summary.
- Keep all new UI production-ready enough to compile and be reviewed, but do not gold-plate.
- Prefer incremental, testable implementation over broad refactors.
- If you add new docs/comments, keep them concise.

## Shared Integration Assumptions
- Flutter app root: `lib/`
- Director Studio backend: `python_director/`
- Director Studio admin UI: `python_director/admin_ui_v3/src/`
- Existing feature specs live in `todo_feature_details_doc/`

---

## Agent 1
### Assignment
1. `admin_hook_first_story_packaging.md`
2. `flutter_cold_open_onboarding.md`

### Why This Pair
This is the "front door" track. Story packaging defines how stories are sold; cold open onboarding is how the app demonstrates value instantly.

### Primary Objective
Make the app emotionally legible in the first 90 seconds and make each story feel attractive before the user reads deeply.

### Scope
Backend/admin:
- Add story packaging metadata generation and editing support
- Ensure story packaging is stored on the story document
- Add admin UI for editing/previewing packaging before/around publish

Flutter:
- Add first-run cold open flow
- Route users into a strong story-selection/follow path
- Use packaging metadata where helpful in the cold open decision surface

### Suggested File Targets
Backend/admin likely files:
- `python_director/api.py`
- `python_director/logic.py`
- `python_director/models.py`
- `python_director/admin_ui_v3/src/types.ts`
- `python_director/admin_ui_v3/src/components/runs/RunDetail.tsx`
- `python_director/admin_ui_v3/src/views/DeploymentsView.tsx`

Flutter likely files:
- `lib/main.dart`
- `lib/models/story_summary.dart`
- `lib/screens/story_gallery_screen.dart`
- `lib/screens/main_navigation.dart`
- new onboarding files under `lib/screens/` and `lib/services/`

### Expected Deliverables
- Story document supports packaging fields such as `hookLine`, `promiseLine`, `heroArtifactType`, and `toneTags`
- Admin can edit/view packaging
- Flutter cold open is first-run gated and skippable
- Cold open routes into a real story follow/explore path

### Non-Goals
- Do not implement catch-up
- Do not implement binge-to-live gating
- Do not build the evaluation/critic infrastructure

### Dependency Notes
- If a Flutter display needs packaging fields, add them to `StorySummary` cleanly and make sure missing fields degrade gracefully.
- Do not wait for Agent 3. Packaging can ship without evaluator data.

### Prompt To Give Agent 1
Implement the features described in `todo_feature_details_doc/admin_hook_first_story_packaging.md` and `todo_feature_details_doc/flutter_cold_open_onboarding.md`.

Constraints:
- Keep your work focused on story packaging plus first-run onboarding.
- Avoid touching unrelated Flutter timeline logic or the admin evaluation stack.
- Reuse existing app visual language.
- Make all new metadata optional-safe so old stories still render.

Success criteria:
- story packaging can be generated/edited/stored
- Flutter first launch enters a cold open flow
- the cold open ends with a strong CTA into a real story
- project builds cleanly for the parts you touched

In your final summary, list:
- files changed
- what remains stubbed or approximate
- any schema/API assumptions you introduced

---

## Agent 2
### Assignment
1. `flutter_binge_to_live_entry.md`
2. `flutter_catch_up_capsule.md`

### Why This Pair
These are both timeline/state-management features for the Flutter client and share the same local per-story user-state infrastructure.

### Primary Objective
Make the app easier to love on day 1 and easier to return to after a gap.

### Scope
- Implement onboarding binge logic for opening story artifacts
- Implement the catch-up capsule for returning users
- Add the local story resume/checkpoint service
- Add UI surfaces in the timeline for binge progress/live wall/catch-up

### Suggested File Targets
- `lib/providers/story_provider.dart`
- `lib/screens/timeline_screen.dart`
- `lib/models/story_summary.dart`
- `lib/models/story_item.dart` only if absolutely necessary
- new files under:
  - `lib/models/`
  - `lib/services/`
  - `lib/widgets/`

### Expected Deliverables
- New users can binge a configured opening window for a story
- A clear transition from binge to live exists
- Returning users who missed enough content see a catch-up capsule
- Catch-up can resume users into the right artifact

### Non-Goals
- Do not implement first-run cold open
- Do not implement story packaging authoring
- Do not work on admin evaluation/reporting

### Dependency Notes
- If packaging fields from Agent 1 are available, the catch-up headline can optionally use them.
- Your implementation must not depend on Agent 1 finishing first.
- Use graceful fallbacks when packaging fields are absent.

### Prompt To Give Agent 2
Implement the features described in `todo_feature_details_doc/flutter_binge_to_live_entry.md` and `todo_feature_details_doc/flutter_catch_up_capsule.md`.

Constraints:
- Keep the work scoped to Flutter timeline/onboarding-return state.
- Reuse existing providers and story gating logic where possible.
- Use `SharedPreferences` for phase 1 local state unless there is a strong reason not to.
- Make sure the app still behaves normally for stories/users that do not qualify for binge or catch-up.

Success criteria:
- binge-to-live works for qualifying first-time story sessions
- catch-up capsule appears for meaningful return gaps
- both features degrade gracefully
- code is analyzable/buildable for touched files

In your final summary, list:
- files changed
- new local keys/state introduced
- edge cases not fully solved

---

## Agent 3
### Assignment
1. `admin_tension_simulator.md`
2. `admin_story_quality_qa_layer.md`

### Why This Pair
These share backend evaluator/report infrastructure and the same Director Studio review surfaces.

### Primary Objective
Improve story quality before users ever see the content, especially opening-hook quality.

### Scope
Backend:
- define evaluation report models/types
- implement hook/tension simulation
- implement QA passes or a basic aggregated QA layer
- expose API endpoints and persist reports with the run

Admin UI:
- render hook-readiness and QA report panels
- show actionable warnings and recommendations

### Suggested File Targets
- `python_director/api.py`
- `python_director/logic.py`
- `python_director/models.py`
- `python_director/admin_ui_v3/src/types.ts`
- `python_director/admin_ui_v3/src/components/runs/RunDetail.tsx`
- new admin components under `src/components/`

### Expected Deliverables
- A run can generate a hook simulation report
- A run can generate a broader QA report
- Reports are visible in Director Studio
- Findings are structured and actionable

### Non-Goals
- Do not build the older `Audience Pulse` graph unless directly needed
- Do not implement prompt regression suite in this wave
- Do not touch Flutter app flows

### Dependency Notes
- This track is largely independent.
- If you find obvious overlap between tension simulation and QA report formats, share types/utilities instead of duplicating structures.

### Prompt To Give Agent 3
Implement the features described in `todo_feature_details_doc/admin_tension_simulator.md` and `todo_feature_details_doc/admin_story_quality_qa_layer.md`.

Constraints:
- Keep the work focused on evaluation/reporting of completed runs.
- Favor structured, deterministic output formats.
- Build the minimum viable but reviewable UI in Director Studio.
- Do not sprawl into unrelated admin features.

Success criteria:
- hook/tension evaluation can be triggered or fetched for a run
- QA report can be generated/fetched for a run
- admin UI renders both reports clearly
- code is clean enough for follow-up review and refinement

In your final summary, list:
- files changed
- report schemas introduced
- any prompts/evaluation heuristics used
- any performance or cost caveats

---

## Recommended Execution Order
Run all three agents in parallel, but ask each one to sequence their own work like this:

### Agent 1 order
1. story packaging
2. cold open onboarding

Reason:
- packaging metadata may improve onboarding copy and story selection UX

### Agent 2 order
1. binge-to-live entry
2. catch-up capsule

Reason:
- both require local story-session state, and binge logic lays groundwork for story resume state handling

### Agent 3 order
1. tension simulator
2. story quality QA layer

Reason:
- the QA layer can reuse report infra and some scoring patterns from the simulator

---

## Integration Milestone
After the three agents finish, the expected merged outcome should be:
- stories are packaged with clearer hooks
- first launch has a compelling cold open
- new users can binge enough to care before hitting the live wall
- returning users can quickly understand missed events
- weak openings and low-quality runs get flagged in Director Studio before publish

---

## What To Review First After Implementation
When the code comes back, prioritize review in this order:
1. Agent 2 Flutter state logic
2. Agent 1 packaging data flow
3. Agent 3 evaluator/report correctness

Reason:
- Agent 2 is most likely to introduce subtle user-state bugs
- Agent 1 may create schema mismatches between backend and Flutter
- Agent 3 is more isolated and easier to refine after the flows are stable
