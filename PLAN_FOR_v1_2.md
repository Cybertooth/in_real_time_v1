## Story Lifecycle + Media Pipeline Upgrade Plan

### Summary
- Add three story lifecycles end-to-end: `live`, `scheduled`, and `subscription`.
- Make upload explicit and configurable from admin Run Detail (mode, schedule time, TTS tier), instead of implicit “go live now”.
- Keep current provider flexibility globally, but add backend-defined reset templates for cost/perf profiles.
- Ensure generated images/audio are both visible in Director Studio and consumable in Flutter.
- Introduce per-story theme color and dynamic app theming so switching stories changes app accent consistently.

### Key Changes
- **Backend API and models**
  - Extend `POST /api/upload/{run_id}` to accept request body:
    - `story_mode`: `live | scheduled | subscription`
    - `scheduled_start_at` (required when `scheduled`)
    - `tts_tier`: `premium | cheap`
  - Extend story metadata written to Firestore:
    - `storyMode`, `storyStartAt`, `storyEndAt`, `storyDurationMinutes`, `themeColorHex`, `ttsTier`, `voiceMap`
  - Persist `timeOffsetMinutes` for all artifact docs (not only absolute unlock timestamps) so subscription mode can compute per-device unlocks.
  - Add `audioUrl` and `voiceId` fields for `voice_notes` docs.
  - Add reset-template support:
    - `POST /api/pipeline/reset` accepts `template_key` (`full_fledged`, `cheap_full`, `cheap_short`)
    - Studio bootstrap includes reset template catalog for UI picker.

- **Pipeline templates and cost profiles**
  - Keep Anthropic support available in advanced editing/provider lists.
  - Define backend reset templates:
    - `full_fledged`: current high-quality graph (with current improvements retained).
    - `cheap_full`: same block structure, cheaper models (OpenAI mini/nano, Gemini lite/flash-lite, OpenRouter council replacements including requested families), OpenRouter Seedream for image generation.
    - `cheap_short`: reduced council and one critique loop, still image/TTS-capable.
  - Keep prompt/block-template semantics aligned across templates; change model routing and graph length only.

- **Image and TTS generation**
  - Fix Director Studio run detail data source to include full run result payload (`final_output`, headline/local media fields), so generated images reliably appear in UI.
  - Add TTS generation pipeline stage for voice notes with two profiles (`premium`, `cheap`) and deterministic speaker-to-voice mapping per story.
  - Upload generated audio files to Cloud Storage and attach `audioUrl` to Firestore `voice_notes`.
  - Preserve existing image generation/regeneration flow and make sure both image and audio paths survive save/load/retry flows.

- **Admin UI (Director Studio)**
  - Replace upload confirm dialog with upload modal:
    - Story mode selector
    - Scheduled datetime picker (for scheduled)
    - TTS tier selector
    - Read-only theme color preview (auto-assigned)
  - Replace “Reset Default” confirm with template picker modal backed by API template catalog.
  - Keep named pipelines and manual block editing unchanged.

- **Flutter app behavior**
  - Story gallery sections:
    - `Live` (global live now)
    - `Upcoming` (scheduled future start, selectable with countdown)
    - `Subscription` (start-on-follow stories)
  - Live badge + `% completion` for live stories:
    - Time-based: `(now - storyStartAt) / storyDurationMinutes`, clamped `0..100`.
  - Subscription anchor:
    - Per-device local start timestamp on Follow/Start, stored by `storyId`.
    - Unlock computation for subscription stories uses `subscriptionStart + timeOffsetMinutes`.
  - Add full audio playback for voice notes (play/pause/progress) from `audioUrl`.
  - Add story theme runtime palette:
    - Use `themeColorHex` from story metadata to drive active accent when switching active story.
    - Apply to app-level theme and key shared UI accents for consistent cross-screen cueing.

### Test Plan
- **Backend unit/integration**
  - Upload API validation by mode (`live`, `scheduled`, `subscription`) and schedule requirements.
  - Firestore payload assertions for new story/doc fields and backward compatibility defaults.
  - Reset template endpoint returns expected block graph/model profiles per template key.
  - TTS generation tests:
    - deterministic voice map by speaker
    - premium/cheap profile routing
    - persisted `audioUrl` + `voiceId`.
  - Regression: existing image generation/upload and retry-block flows remain functional.

- **Admin UI**
  - Run Detail loads full run result and shows generated images.
  - Upload modal submits correct payload and handles validation/errors.
  - Reset template modal updates pipeline correctly for each template.

- **Flutter**
  - Gallery renders `Live`, `Upcoming`, `Subscription` sections with correct grouping.
  - Live completion percent formula correctness and edge clamping.
  - Subscription unlock timing based on local follow start.
  - Voice note playback works with streamed `audioUrl`.
  - Story switch updates theme accent consistently across main navigation and core screens.
  - Backward compatibility: old stories with missing metadata still render as live with safe defaults.

### Assumptions and Defaults
- Scheduled datetime is entered in admin local timezone and stored as UTC timestamp.
- Subscription mode is per-device (local storage), with no auth-backed cross-device sync.
- Existing stories are not backfilled; missing metadata defaults to live-compatible behavior.
- Theme color is auto-assigned deterministically from story id/title (no manual picker in this phase).
- Anthropic remains available globally but is not required by new cheap templates.
