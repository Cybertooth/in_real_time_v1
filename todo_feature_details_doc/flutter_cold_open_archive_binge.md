# Feature Implementation Spec: "Cold Open" Archive Binge (V2 Catch-Up Mode)

## 1. Feature Overview
**Target Application:** Flutter Client (`lib/`)
**Objective:** Replace empty "waiting" states for new users by simulating an active, ongoing story. New users are dropped into a timeline that has "already been running for 3 days," allowing them to immediately binge 30+ artifacts before hitting the real-time constraint wall.

## 2. Architecture Context
- The app relies on Firestore to fetch `StoryItem` documents.
- Currently, items have a global server timestamp.
- We need a mechanism where the "start" of the story is offset relative to the *user's first install time*, or the app pulls from a pool of "Archived" stories that fast-forward their timestamps client-side.

## 3. Detailed Requirements
- **Simulated Backlog:** When the app first bootstraps for a new user, the local timeline must populate with a block of initial artifacts (e.g., 3 days worth of story content).
- **"Unread" Avalanche:** The UI should show a badge indicating a large number of missed events (e.g., "73 Unread Intercepts").
- **Real-Time Wall:** Once the user scrolls/reads through the backlog up to the "present moment," the UI must switch back to standard real-time polling/listening for new events via the notification/polling service.

## 4. Technical Implementation Steps
1. **User Profiling (`lib/services/user_service.dart`):**
   - Create a local state (via `SharedPreferences` or local SQLite) tracking `firstInstallDate`.
   - Modify the user creation logic in the backend to tag the user as `status: 'onboarding'`.
2. **Timeline Offset Logic (`lib/screens/timeline_screen.dart`):**
   - Update the `TimelineProvider` or `TimelineBloc` to query stories where the internal "story elapsed time" is <= 72 hours.
   - For these onboarding users, override the display timestamps to be relative to `current_time - offset`. E.g., The oldest item is timestamped `3 days ago`.
3. **UI Updates (`lib/widgets/timeline_card.dart`):**
   - Ensure the `ListView.builder` handles sudden large payloads without jank. Use pagination or infinite scrolling.
   - Add a prominent sticky header in the timeline: "ARCHIVE MODE - CATCHING UP TO LIVE FEED".
4. **The Live Sync Event:**
   - Once the user reads the latest onboarding artifact, trigger a state change to `status: 'live'`.
   - Transition the sticky header to: "SYNCED WITH LIVE SATELLITE. WAITING FOR NEXT INTERCEPT."

## 5. Testing & Verification
- **Functional:** Intern agent must verify that installing the app on a clean emulator instantly populates the timeline with backlog data. 
- **State Transition:** Agent must verify that reaching the end of the backlog stops rapid-fire updates and accurately waits for a new manual push from the Director Studio.
