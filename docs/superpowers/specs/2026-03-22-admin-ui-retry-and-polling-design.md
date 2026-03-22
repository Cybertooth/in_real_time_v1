# Admin UI: Retry Modes & Polling Decoupling

**Date:** 2026-03-22
**Status:** Approved

---

## Overview

Two targeted fixes to the Director Studio admin UI:

1. **Retry modes** — When retrying a run, give users two distinct modes: reuse the same seed prompt, or start fresh with a new one.
2. **Polling decoupling** — Stop active-run polling from causing full UI re-renders and forced navigation when the user is viewing a different run.

---

## Fix 1: Retry Modes

### Problem

The current retry flow has a single button that opens `RunDialog` pre-populated with the existing run's `seed_prompt` and `tags`. There is no way to signal intent — the user must manually clear the seed field to start fresh. This is error-prone and unintuitive.

### Design

Add a mode toggle to the top of `RunDialog`: two pill-style buttons — **"Same Seed"** and **"New Seed"**. Controlled by `useState<'same' | 'new'>` inside the dialog, initialised from the `initialMode` prop.

**Same Seed mode:**
- Seed prompt and tags pre-populated from the source run
- Fields are fully editable — user can still tweak before submitting

**New Seed mode:**
- Seed prompt field cleared and auto-focused
- Tags optionally retained (user can clear manually)

The mode toggle is only shown when `initialSeedPrompt` is provided (i.e. this is a retry, not a fresh run). Fresh-start dialogs open without the toggle.

### Scope

- `RunDialog.tsx`:
  - Add `initialMode?: 'same' | 'new'` prop. Defaults to `'same'` when `initialSeedPrompt` is provided, otherwise irrelevant (toggle hidden).
  - Render mode toggle only when `initialSeedPrompt` is non-empty
  - In "New Seed" mode, clear the seed prompt field and auto-focus it on mount

- `RunList.tsx`: pass `initialMode="same"` when opening the retry dialog (explicit, no behaviour change)

- `RunDetail.tsx`: also has a "Re-run" button (line ~232) that opens `RunDialog` pre-populated with `storedSeed`/`storedTags` — pass `initialMode="same"` here as well. User-triggered `navigate('/runs')` after re-run submission is **not** changed.

- No changes to `store.ts` — `rerunFromRun` already accepts whatever seed/tags come from the form

---

## Fix 2: Polling Decoupling

### Problem

Three separate poll loops (`startRun`, `rerunFromRun`, `retryBlock`) each run every 1500ms and write to `activeRunProgress`. `RunDetail` subscribes to this value directly, causing the entire component tree to re-render 40+ times per minute — even when the user is viewing a *different* run's artifacts. On run completion, each loop calls `loadStudio()` which reloads all run summaries and can trigger automatic navigation, yanking the user away from what they were reading. A `loadRunProgress` action also writes `activeRunId` and `activeRunProgress` directly and must be migrated.

### Design

**New `liveRun` slice in the store:**

```ts
liveRun: {
  id: string
  status: string
  progress: number          // 0–1, derived from completed block count
  blockStatuses: Record<string, BlockStatus>
} | null
```

All three poll loops (`startRun`, `rerunFromRun`, `retryBlock`) and the `loadRunProgress` action write *only* to `liveRun`. They never mutate `runSummaries` mid-run.

**`activeRunProgress` field is removed** from the store. All consumers are migrated to `liveRun`.

**`RunDetail` subscription change:**

`RunDetail` reads from `runSummaries` filtered by its own `runId`. This value changes only once — when the run completes and its summary is patched. It no longer subscribes to `activeRunProgress` at all.

For the blocks-progress view when the user *is* viewing the active run: reads from `liveRun.blockStatuses` only when `liveRun?.id === runId`. This gives live block progress without polluting unrelated views.

**`RunList` subscription change:**

`RunList` currently reads `activeRunProgress` to render the active-run card's progress bar (bar width derived from `block_traces`). This migrates to `liveRun`: the progress bar uses `liveRun.progress` (0–1) and per-block status from `liveRun.blockStatuses`. The running badge/indicator uses `liveRun?.id` comparison.

**Completion handling (all three poll loops + `loadRunProgress`):**

When any poll loop detects run completion:
1. Fetch the final run data for that `runId`
2. Patch only that entry in `runSummaries` (replace by ID)
3. Clear `liveRun` (set to `null`)
4. **Do not call `loadStudio()`**
5. **Do not call `navigate()`** — this applies only to polling-completion-triggered navigation; user-action-triggered navigation (e.g. `navigate('/runs')` after form submit) is unchanged

### Scope

- `store.ts`:
  - Add `liveRun` slice and `setLiveRun()` setter
  - Migrate all three poll loops (`startRun`, `rerunFromRun`, `retryBlock`) to write to `liveRun`
  - Migrate `loadRunProgress` action to write to `liveRun`
  - On completion in all three loops: patch `runSummaries`, clear `liveRun`, remove `loadStudio()` call, remove polling-driven `navigate()` call
  - Remove `activeRunProgress` field entirely

- `RunDetail.tsx`:
  - Remove subscription to `activeRunProgress`
  - Subscribe to `runSummaries` by `runId` for stable run data
  - Subscribe to `liveRun` only for the blocks-progress view, guarded by `liveRun?.id === runId`

- `RunList.tsx`:
  - Migrate progress bar rendering from `activeRunProgress.block_traces` to `liveRun.progress` and `liveRun.blockStatuses`
  - Show running badge using `liveRun?.id` comparison
  - Remove polling-completion-triggered `navigate()` calls

---

## Non-Goals

- No changes to the pipeline execution logic or backend
- No changes to how runs are stored or fetched on initial load
- No redesign of the RunDialog layout beyond the mode toggle
