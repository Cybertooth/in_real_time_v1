# Feature Implementation Spec: Cold Open Onboarding

## 1. Feature Overview
**Target Application:** Flutter Client (`lib/`)  
**Objective:** Replace passive first-launch browsing with a guided, emotionally strong "cold open" that demonstrates the app's storytelling promise in the first 90 seconds.

The first session should feel like entering a live thriller, not configuring a content library.

## 2. Why This Matters
- The current app opens into navigation and content structures that reward existing context.
- New users do not yet understand why this product is special.
- We need a first-run experience that delivers the fantasy immediately:
  - voyeurism
  - urgency
  - artifact variety
  - cliffhanger

## 3. Product Principle
Do not explain first. Seduce first.

The user should feel:
- "This is different"
- "I want to know what happened"
- "I should come back"

## 4. Experience Summary
On first launch:
1. Show a branded cold open screen with a strong intercepted-signal mood.
2. Auto-play a scripted mini-sequence using real in-app artifact UI:
   - one chat
   - one image or receipt
   - one journal/voice-note beat
3. End on a cliffhanger.
4. CTA options:
   - `Start This Story`
   - `Explore Stories`

## 5. Scope Choice
Phase 1 should be fully deterministic and local-client driven.

Do not depend on:
- push notifications
- backend experimentation infra
- account creation

## 6. Architecture Context
- Existing screens already render real artifact types:
  - timeline
  - chat thread
  - journals
  - gallery
- We should reuse those UI components or mimic their visual language.

## 7. Required Behavior
- First-run only by default.
- Re-enterable from settings later as `Replay Intro`.
- Must complete in under 90 seconds without user input.
- Must be skippable within 3 seconds.
- Must work offline if the needed assets are bundled or cached.

## 8. Content Design
The cold open should be a curated "best of" sample, not randomly generated.

Suggested script:
1. Black screen + intercepted signal copy.
2. Chat appears:
   - one normal message
   - one suspicious reply
3. Cut to receipt/photo:
   - something concrete and intriguing
4. Journal snippet or voice note:
   - emotional or confessional line
5. Cliffhanger text:
   - "New entry unlocks tonight."

## 9. UX Details
Suggested screen flow:
- `ColdOpenIntroScreen`
- `ColdOpenSequenceScreen`
- `ColdOpenDecisionScreen`

Suggested CTA copy:
- primary: `Follow The Story`
- secondary: `Browse The Archive`

## 10. Data Model
Use local state for first-run gating:
- `has_seen_cold_open`
- `cold_open_completed_at`
- `cold_open_skipped`

Optional future remote-config fields:
- `coldOpenVariantId`
- `coldOpenStoryId`

## 11. Implementation Files
- `lib/screens/cold_open_intro_screen.dart`
- `lib/screens/cold_open_sequence_screen.dart`
- `lib/models/cold_open_step.dart`
- `lib/services/onboarding_service.dart`
- `lib/main.dart`
- `lib/screens/main_navigation.dart`

## 12. Technical Implementation Steps
1. Create onboarding service with first-run read/write methods.
2. In [main.dart](G:/code/gen-ai/in_real_time_v1/lib/main.dart), gate initial route:
   - if first run and not completed -> open cold open
   - else -> open main navigation
3. Define a `ColdOpenStep` model:
```dart
enum ColdOpenStepType { text, chat, receipt, image, journal, cliffhanger }
```
4. Build a timed sequence controller using `PageView`, `AnimatedSwitcher`, or `AnimationController`.
5. Reuse existing card styles where possible.
6. Persist completion/skipped state when flow exits.
7. Route chosen story into the story gallery / activate story id directly.

## 13. Motion Guidelines
- Use only 2-3 animation patterns:
  - fade in
  - typing reveal
  - subtle pan/zoom on image
- Respect reduced motion in future.
- Avoid flashy tutorial energy.

## 14. Visual Guidelines
- Maintain the app's "intercepted terminal" tone.
- Lean into tension, not cheerful onboarding.
- Keep copy minimal.
- Prefer strong pacing over detailed explanation.

## 15. Analytics Events
- cold_open_seen
- cold_open_skipped
- cold_open_completed
- cold_open_story_followed
- cold_open_browse_clicked

## 16. Acceptance Criteria
- First launch routes into cold open.
- User can skip at any point after the opening moment.
- Completion routes to a meaningful next destination.
- Replay is accessible after onboarding.
- Repeat launches do not show cold open again unless replayed.

## 17. Testing & Verification
- Clean-install emulator test.
- Verify skip, complete, replay paths.
- Verify state persistence after app restart.
- Verify layout on narrow/mobile and tablet widths.

## 18. Future Enhancements
- A/B variants per story genre
- voiceover version
- live content injected from a top-performing story
- deep link campaigns that land directly into the cold open
