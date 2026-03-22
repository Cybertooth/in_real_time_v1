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

Add a mode toggle to the top of `RunDialog`: two pill-style buttons — **"Same Seed"** and **"New Seed"**. Controlled by `useState<'same' | 'new'>('same')` inside the dialog. The mode is set automatically based on context (retry always opens in "same" mode; new run opens in "new" mode).

**Same Seed mode:**
- Seed prompt and tags pre-populated from the source run
- Fields are fully editable — user can still tweak before submitting

**New Seed mode:**
- Seed prompt field cleared and auto-focused
- Tags optionally retained (user can clear manually)

### Scope

- `RunDialog.tsx`: add `initialMode?: 'same' | 'new'` prop (defaults to `'same'`); render mode toggle; conditionally pre-populate seed field
- `RunList.tsx`: pass `initialMode="same"` when opening retry dialog (explicit, no behaviour change)
- No changes to `store.ts` — `rerunFromRun` already accepts whatever seed/tags come from the form

---

## Fix 2: Polling Decoupling

### Problem

The poll loop runs every 1500ms and writes `activeRunProgress` to the Zustand store. `RunDetail` subscribes to this value directly, causing the entire component tree to re-render 40+ times per minute — even when the user is viewing a *different* run's artifacts. Additionally, on run completion `loadStudio()` is called, which reloads all run summaries and can trigger automatic navigation, yanking the user away from what they were reading.

### Design

**New `liveRun` slice in the store:**

```ts
liveRun: {
  id: string | null
  status: string
  progress: number          // 0–1
  blockStatuses: Record<string, BlockStatus>
} | null
```

The poll loop writes *only* to `liveRun`. It never mutates `runSummaries` mid-run.

**`RunDetail` subscription change:**

`RunDetail` reads from `runSummaries` filtered by its own `runId`. This value changes only once — when the run completes and its summary is patched. It no longer subscribes to `activeRunProgress` at all.

For the "blocks" view when the user *is* viewing the active run: it reads from `liveRun.blockStatuses` only when `liveRun?.id === runId`. This gives live block progress without polluting unrelated views.

**Completion handling:**

When the poll loop detects run completion:
1. Fetch the final run data for that `runId`
2. Patch only that entry in `runSummaries` (replace by ID)
3. Clear `liveRun` (set to null)
4. **Do not call `loadStudio()`**
5. **Do not call `navigate()`** — user stays on whatever route they are on

**Sidebar active-run indicator:**

A small badge/dot on the active run's entry in `RunList` reads from `liveRun.id` to show running state. This is a lightweight subscription with no layout impact.

### Scope

- `store.ts`:
  - Add `liveRun` slice and setter `setLiveRun()`
  - Poll loop writes to `liveRun` instead of `activeRunProgress`
  - On completion: patch `runSummaries`, clear `liveRun`, no `loadStudio()`, no `navigate()`
  - Remove or deprecate `activeRunProgress` field
- `RunDetail.tsx`:
  - Remove subscription to `activeRunProgress`
  - Subscribe to `runSummaries` by `runId` for stable run data
  - Subscribe to `liveRun` only for the blocks-progress view, guarded by `liveRun?.id === runId`
- `RunList.tsx`:
  - Show running badge using `liveRun.id` comparison
  - Remove any `navigate()` side-effects triggered by polling

---

## Non-Goals

- No changes to the pipeline execution logic or backend
- No changes to how runs are stored or fetched on initial load
- No redesign of the RunDialog layout beyond the mode toggle
