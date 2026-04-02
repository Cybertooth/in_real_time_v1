# Feature Implementation Spec: Binge-to-Live Entry

## 1. Feature Overview
**Target Application:** Flutter Client with supporting story metadata in backend  
**Objective:** Let brand-new users consume an exciting opening block of content quickly, then gracefully transition them into the app's real-time pacing model.

This is the best compromise between:
- immediate hook
- enough content to care
- preserving the core real-time identity of the product

## 2. Product Principle
Give the user enough story to fall in love before asking them to wait.

## 3. User Experience
For selected stories, new users can binge:
- first `N` hours
- first `M` artifacts
- or first "Act 1"

Once they reach the binge boundary, show a strong "live wall" moment:
- recap of current state
- next unlock expectation
- invitation to return

## 4. Why This Matters
- Pure real-time pacing is elegant but hostile to first-session engagement.
- A new user who only sees one artifact may not understand the value.
- A controlled binge gives enough immersion without turning the app into a normal archive reader.

## 5. Binge Boundary Options
Add story-level configuration:
```json
{
  "onboardingBingeEnabled": true,
  "onboardingBingeArtifactCount": 12,
  "onboardingBingeUntilOffsetMinutes": 180
}
```

Phase 1 can support only one rule:
- allow first 12 unlocked artifacts instantly for brand-new users

## 6. Architecture Context
The app already has time-based unlocking via:
- `unlockTimestamp`
- `timeOffsetMinutes`
- subscription/on-demand local gating

This feature should introduce a user-specific onboarding gate without breaking live/scheduled/subscription logic.

## 7. Proposed Approach
For users in onboarding mode:
- override lock checks for the initial binge window only
- after boundary is reached, revert to normal unlock behavior

Suggested local state:
- `story_onboarding_binge_started_<storyId>`
- `story_onboarding_binge_completed_<storyId>`
- `story_onboarding_binge_last_seen_item_<storyId>`

## 8. UX Requirements
While in binge mode:
- show a subtle banner: `CATCHING UP TO LIVE`
- show progress:
  - `8 of 12 opening intercepts`

At boundary:
- show a full-screen or inline transition:
  - `YOU'RE NOW CAUGHT UP`
  - next unlock timing
  - option to enable reminders later

## 9. Rules
- Only for first-time story followers or users marked onboarding.
- Not available indefinitely.
- Once user crosses the boundary, they cannot continue bingeing for that story.
- If they uninstall/reinstall, phase 1 can remain local-only; phase 2 should persist on backend user profile.

## 10. Provider Changes
Extend lock logic in [story_provider.dart](G:/code/gen-ai/in_real_time_v1/lib/providers/story_provider.dart):
- current `_isLockedForStory(...)`
- add a user onboarding override layer before final lock decision

Suggested helper:
```dart
bool _isUnlockedByOnboardingBinge(
  StoryItem item,
  StorySummary? story,
  OnboardingBingeState? bingeState,
)
```

## 11. UI Components
New widgets:
- `lib/widgets/binge_progress_banner.dart`
- `lib/widgets/live_wall_card.dart`

Suggested placements:
- banner at top of timeline during binge mode
- live wall card in feed when binge boundary is reached

## 12. Implementation Steps
1. Create onboarding binge state service using `SharedPreferences`.
2. Add provider for current binge state.
3. Update lock logic to allow configured opening window.
4. Add banner with progress count.
5. Detect boundary completion when user opens the last binge-enabled artifact.
6. Show live wall transition card.
7. Persist completion so normal real-time gating resumes.

## 13. Edge Cases
- Story has fewer artifacts than binge limit: mark as fully caught up.
- User switches stories: keep state per story.
- Story is scheduled/upcoming: do not bypass future absolute story start rules unless product explicitly wants that.
- On-demand subscription stories: phase 1 should probably opt out to reduce complexity.

## 14. Acceptance Criteria
- New user gets immediate access to configured opening content.
- Progress banner updates correctly.
- At binge boundary, app clearly transitions to live mode.
- User cannot re-enter binge mode after completion.

## 15. Testing & Verification
- Fresh install with a story containing >12 artifacts.
- Confirm first 12 are accessible immediately.
- Confirm 13th obeys normal lock rules after boundary.
- Verify boundary UI appears exactly once.

## 16. Future Enhancements
- backend-persisted onboarding status
- story-specific binge windows chosen by Director Studio
- A/B test different boundary sizes
- couple this with Catch-Up Capsule and Cold Open entry
