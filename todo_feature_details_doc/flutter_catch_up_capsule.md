# Feature Implementation Spec: Catch-Up Capsule

## 1. Feature Overview
**Target Application:** Flutter Client (`lib/`) with minor backend/story metadata support  
**Objective:** Help returning users understand what happened since their last session in under 60 seconds, so they can resume the story without confusion or abandonment.

This is an acquisition-retention bridge feature, not a notification feature. A user should be able to disappear for 2-7 days, open the app cold, and immediately feel oriented instead of lost.

## 2. Why This Matters
- New users frequently install, browse once, and come back days later.
- The current experience assumes continuous attention and memory of prior events.
- When a user returns and sees many new artifacts with no framing, the app feels cognitively expensive.
- A strong catch-up flow makes the app feel welcoming, premium, and easy to resume.

## 3. User Experience Goals
- On app open, if the user has missed meaningful story activity, show a full-width catch-up card before the timeline.
- The card should answer:
  - What changed?
  - Why does it matter?
  - What should I read first?
- Reading the catch-up should never block access to the raw timeline.
- The catch-up should feel like an editorial "Previously on..." capsule, not a dry system summary.

## 4. Architecture Context
- Timeline data currently comes from `timelineFeedProvider` in [story_provider.dart](G:/code/gen-ai/in_real_time_v1/lib/providers/story_provider.dart).
- Story metadata comes from `StorySummary` in [story_summary.dart](G:/code/gen-ai/in_real_time_v1/lib/models/story_summary.dart).
- The Flutter app already has:
  - an active story concept
  - merged timeline sorting
  - local `SharedPreferences`
  - story item models with timestamps and content types

The missing piece is a user-specific "last seen" checkpoint plus a recap generator layer.

## 5. Core Requirements
- Track per-story `last_seen_at` and `last_seen_item_id` locally.
- Detect if the user has missed enough content to justify a catch-up.
- Generate a structured recap object with:
  - headline
  - 2-4 bullet events
  - 1 unresolved tension/question
  - recommended resume item id
  - count of missed artifacts by type
- Show the catch-up card only once per return session unless dismissed.
- Allow three actions:
  - `Read recap`
  - `Jump to key moment`
  - `Browse everything`

## 6. Trigger Rules
- Show a catch-up capsule when all are true:
  - user has previously opened this story
  - user was away for more than `6 hours`
  - there are at least `3` newly unlocked artifacts since `last_seen_at`
- Do not show for first-ever story sessions.
- Do not show if the user has already consumed all newly unlocked items in the current session.

## 7. Data Model Changes
Create a local-only model persisted in `SharedPreferences` first.

Suggested keys:
- `story_last_seen_at_<storyId>`
- `story_last_seen_item_id_<storyId>`
- `story_last_catchup_seen_at_<storyId>`
- `story_catchup_dismissed_for_session_<storyId>`

Suggested Dart model:
```dart
class StoryCatchUpSummary {
  final String storyId;
  final DateTime since;
  final DateTime until;
  final String headline;
  final List<String> bullets;
  final String unresolvedQuestion;
  final String? recommendedResumeItemId;
  final Map<String, int> missedCountsByType;
}
```

## 8. Phase 1 Scope
- Generate recap client-side using deterministic heuristics from the unlocked items already in memory.
- Do not call an LLM in phase 1.
- Prefer simple but useful summaries over perfect prose.

## 9. Phase 2 Scope
- Add backend or admin-authored recap text for premium quality.
- Allow Director Studio to preview the catch-up capsule during run review.

## 10. Heuristic Recap Generation Logic
Given all unlocked story items after `last_seen_at`:

1. Sort chronologically ascending.
2. Take up to the first 8 meaningful items.
3. Convert each item into a human-readable event line:
   - `journal`: summarize title or first sentence
   - `chat`: "X messaged about Y"
   - `email`: "Email from X: subject"
   - `receipt`: "Receipt suggests X spent money at Y"
   - `voice_note`: "Voice note from X reveals Y"
   - `social_post`: "Public post hints Y"
   - `phone_call`: "Call between X and Y"
   - `group_chat`: "Group chat escalated around Y"
4. Pick the most important 3-4 lines using weighted scoring:
   - artifact has image/audio: +2
   - password locked/decrypted artifact: +2
   - phone call / voice note / receipt: +2
   - long journal with strong title: +1
   - newest artifact: +1
5. Build unresolved question:
   - prefer latest suspicious artifact
   - fallback: "Why did this happen now?"
6. Choose `recommendedResumeItemId`:
   - latest high-weight artifact
   - fallback: first unread item

## 11. UI Requirements
Create a new widget, suggested path:
- `lib/widgets/catch_up_capsule.dart`

Visual structure:
- eyebrow: `WHILE YOU WERE AWAY`
- headline
- missed count chips: `3 Chats`, `1 Receipt`, `2 Journals`
- 3 bullets
- unresolved question in highlighted style
- CTA row:
  - `Read Recap`
  - `Jump In`
  - `Skip`

Placement:
- top of [timeline_screen.dart](G:/code/gen-ai/in_real_time_v1/lib/screens/timeline_screen.dart), above the first story card and below any burst-mode banner.

## 12. Navigation Behavior
- `Read Recap`: opens a dedicated recap detail sheet/screen.
- `Jump In`: navigates directly to the recommended item detail or chat thread.
- `Skip`: dismisses the catch-up for the current app session only.

## 13. Proposed Files
- `lib/models/story_catchup_summary.dart`
- `lib/services/story_resume_service.dart`
- `lib/providers/story_provider.dart`
- `lib/widgets/catch_up_capsule.dart`
- `lib/screens/timeline_screen.dart`

## 14. Implementation Steps
1. Create `StoryResumeService` for local checkpoint read/write.
2. Update timeline/detail/chat entry points to mark items as seen when opened.
3. Add provider:
   - `storyLastSeenProvider`
   - `catchUpSummaryProvider`
4. Add recap summary generation helper.
5. Add `CatchUpCapsule` widget.
6. Integrate widget into timeline screen with show/hide rules.
7. Add deep-link resume behavior for each supported artifact type.
8. Add analytics hooks for:
   - capsule_shown
   - capsule_opened
   - capsule_jump_clicked
   - capsule_skipped

## 15. Edge Cases
- User switches active story: keep state per story id.
- No meaningful missed content: do not show capsule.
- Recommended item is missing/deleted: fallback to first unread.
- User is in on-demand subscription mode: recap only summarize unlocked content, not future locked content.
- Very large gap: summarize only latest "chapter" and offer a "View Full Archive" secondary action later.

## 16. Acceptance Criteria
- Returning after missing 3+ artifacts shows a catch-up card.
- Card content is stable and not empty.
- `Jump In` always lands on a valid artifact.
- Dismissing the card hides it for the session.
- Switching stories produces separate catch-up state.

## 17. Testing & Verification
- Unit test recap generation from mixed artifact lists.
- Widget test the card render and CTA behavior.
- Manual QA:
  - open story
  - set last seen state artificially to 48h ago
  - add/inspect new unlocked items
  - verify catch-up appears and routes correctly

## 18. Future Enhancements
- AI-written recap text from the backend
- voice recap narration
- spoiler-safe "short recap" vs "full recap" modes
- recap image collage from missed visual artifacts
