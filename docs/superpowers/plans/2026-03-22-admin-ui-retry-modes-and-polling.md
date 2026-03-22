# Admin UI: Retry Modes & Polling Decoupling — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix two UI bugs in the Director Studio admin UI: add "same seed / new seed" retry mode toggle to RunDialog, and stop active-run polling from re-rendering or navigating unrelated run views.

**Architecture:** (1) Add an `initialMode` prop to `RunDialog` that controls a seed-mode toggle, shown only for retries. (2) Rename `activeRunProgress` → `liveRun` in the store; extract a shared `_startPolling` helper for the three duplicated poll loops; on completion patch `runSummaries` in-place instead of calling `loadStudio()`; in `RunDetail` subscribe to `liveRun` via a selective selector that only returns non-null when `liveRun.run_id === runId`, so non-active runs never re-render mid-poll.

**Tech Stack:** React 18, Zustand, React Router v6, TypeScript — all in `python_director/admin_ui_v3/src/`.

---

## File Map

| File | Change |
|------|--------|
| `src/components/shared/RunDialog.tsx` | Add `initialMode` prop + seed-mode toggle UI |
| `src/store.ts` | Add `liveRun`, extract `_startPolling` helper, fix all 3 poll loops + `loadRunProgress`, patch completion, remove `activeRunProgress` |
| `src/components/runs/RunList.tsx` | Subscribe to `liveRun`, pass `initialMode="same"`, fix broken `navigate` in `handleRerun`, fix empty-state guard |
| `src/components/runs/RunDetail.tsx` | Subscribe to `liveRun` via selective selector, pass `initialMode="same"` |
| `src/components/pipeline/BlockList.tsx` | Migrate `activeRunProgress` → `liveRun` (one-line change to avoid compile error) |
| `src/components/layout/TopBar.tsx` | No change — subscribes to `activeRunId` which is kept in store |

No new files. No backend changes.

---

## Task 1: RunDialog — seed-mode toggle

**Files:**
- Modify: `src/components/shared/RunDialog.tsx`

- [ ] **Step 1: Add `initialMode` prop to `RunDialogProps`**

```tsx
interface RunDialogProps {
  open: boolean
  onClose: () => void
  onStart: (seedPrompt: string, tags: string[]) => void
  initialSeedPrompt?: string
  initialTags?: string[]
  initialMode?: 'same' | 'new'   // NEW
  title?: string
  submitLabel?: string
}
```

And accept it in the function signature:
```tsx
export default function RunDialog({
  open,
  onClose,
  onStart,
  initialSeedPrompt = '',
  initialTags = [],
  initialMode,            // NEW
  title = 'Start Dry Run',
  submitLabel = 'Start Run',
}: RunDialogProps) {
```

- [ ] **Step 2: Add `mode` state and derive initial seed from it**

Add inside the component body (after the existing `useState` calls):
```tsx
const [mode, setMode] = useState<'same' | 'new'>(initialMode ?? 'same')
const isRetry = Boolean(initialSeedPrompt)
```

- [ ] **Step 3: Reset mode and seed on open**

Replace the existing `useEffect` body so it also resets `mode` and clears seed when opening in "new" mode:

```tsx
useEffect(() => {
  if (open) {
    const openMode = initialMode ?? 'same'
    setMode(openMode)
    setSeedPrompt(openMode === 'new' ? '' : initialSeedPrompt)
    setTags(initialTags)
    setTagInput('')
    dialogRef.current?.showModal()
  } else {
    dialogRef.current?.close()
  }
}, [open]) // eslint-disable-line react-hooks/exhaustive-deps
```

- [ ] **Step 4: Render mode toggle above seed field (only for retries)**

Insert between the `<div>` header and the seed `<label>`:

```tsx
{isRetry && (
  <div className="flex gap-1 p-1 bg-surface rounded-xl border border-border w-fit">
    {(['same', 'new'] as const).map((m) => (
      <button
        key={m}
        type="button"
        onClick={() => {
          setMode(m)
          setSeedPrompt(m === 'new' ? '' : initialSeedPrompt)
        }}
        className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
          mode === m
            ? 'bg-mint text-black'
            : 'text-text-dim hover:text-text'
        }`}
      >
        {m === 'same' ? 'Same Seed' : 'New Seed'}
      </button>
    ))}
  </div>
)}
```

- [ ] **Step 5: Auto-focus textarea when opening in "new" mode**

Add a `textareaRef` and auto-focus when mode is 'new':

```tsx
const textareaRef = useRef<HTMLTextAreaElement>(null)

// Inside the useEffect, after showModal():
if (openMode === 'new') {
  setTimeout(() => textareaRef.current?.focus(), 50)
}
```

Add `ref={textareaRef}` to the `<textarea>` element.

- [ ] **Step 6: Start dev server and manually verify**

```bash
cd python_director/admin_ui_v3 && npm run dev
```

Open the runs view. Hover a run, click ↺. Confirm: toggle appears, "Same Seed" pre-fills, "New Seed" clears and focuses the textarea. Fresh-run dialog (from pipeline editor) has no toggle.

- [ ] **Step 7: Commit**

```bash
git add python_director/admin_ui_v3/src/components/shared/RunDialog.tsx
git commit -m "feat: add same/new seed mode toggle to RunDialog"
```

---

## Task 2: Wire initialMode in RunList and RunDetail, fix navigate bug

**Files:**
- Modify: `src/components/runs/RunList.tsx` (lines 34-38, 159-167)
- Modify: `src/components/runs/RunDetail.tsx` (lines 105-110, 232-240)

- [ ] **Step 1: Pass `initialMode="same"` in RunList's RunDialog**

`RunList.tsx` line 159-167 — add `initialMode="same"`:

```tsx
<RunDialog
  open={rerunTarget !== null}
  onClose={() => setRerunTarget(null)}
  onStart={handleRerun}
  initialSeedPrompt={rerunTarget?.seed_prompt ?? ''}
  initialTags={rerunTarget?.tags ?? []}
  initialMode="same"
  title="Re-run Pipeline"
  submitLabel="Start Re-run"
/>
```

- [ ] **Step 2: Fix the broken `navigate` in RunList's `handleRerun`**

`RunList.tsx` lines 34-38. The current `navigate('/runs/${activeRunId ?? ''}')` uses the old `activeRunId` before the new run has started. Remove the navigate entirely — the user stays in the sidebar and the new active run card will appear:

```tsx
const handleRerun = (seedPrompt: string, tags: string[]) => {
  if (!rerunTarget) return
  setRerunTarget(null)
  rerunFromRun(rerunTarget.run_id, seedPrompt || null, tags)
  // No navigate — active run card appears in sidebar automatically
}
```

Also remove the `activeRunId` selector since it's no longer needed in this component (it will be replaced in Task 3 anyway).

- [ ] **Step 3: Pass `initialMode="same"` in RunDetail's RunDialog**

`RunDetail.tsx` lines 232-240:

```tsx
<RunDialog
  open={rerunDialogOpen}
  onClose={() => setRerunDialogOpen(false)}
  onStart={handleRerun}
  initialSeedPrompt={storedSeed ?? ''}
  initialTags={storedTags ?? []}
  initialMode="same"
  title="Re-run Pipeline"
  submitLabel="Start Re-run"
/>
```

- [ ] **Step 4: Commit**

```bash
git add python_director/admin_ui_v3/src/components/runs/RunList.tsx \
        python_director/admin_ui_v3/src/components/runs/RunDetail.tsx
git commit -m "feat: wire initialMode to retry dialogs, fix RunList navigate bug"
```

---

## Task 3: store.ts — liveRun, shared poll helper, fixed completion

**Files:**
- Modify: `src/store.ts`

This is the largest task. Work through it section by section.

- [ ] **Step 1: Add `liveRun` to the state interface, remove `activeRunProgress`**

In the `StudioState` interface, replace:
```ts
activeRunProgress: RunProgress | null
```
with:
```ts
liveRun: RunProgress | null
```

- [ ] **Step 2: Update initial state**

In `create<StudioState>((set, get) => ({`, replace:
```ts
activeRunProgress: null,
```
with:
```ts
liveRun: null,
```

- [ ] **Step 3: Add `progressToSummary` helper above the `create` call**

Add this pure function above the `export const useStore = create(...)` line:

```ts
function progressToSummary(p: RunProgress): RunSummary {
  const raw = p as unknown as Record<string, unknown>
  return {
    run_id: p.run_id,
    timestamp: p.timestamp,
    pipeline_name: p.pipeline_name,
    status: p.status,
    final_title: p.final_title,
    block_count: p.block_count,
    provider_summary: (raw.provider_summary as Record<string, number>) ?? {},
    artifact_counts: (raw.artifact_counts as Record<string, number>) ?? {},
    final_metrics: p.final_metrics,
    mode: p.mode,
    error_message: p.error_message,
    seed_prompt: (raw.seed_prompt as string | null) ?? null,
    tags: (raw.tags as string[]) ?? [],
    story_id: p.story_id,
  }
}
```

- [ ] **Step 4: Extract `_startPolling` internal helper inside `create`**

Add this const just before the `startRun:` action (around line 319). This replaces the three duplicated poll loops:

```ts
const _startPolling = (
  runId: string,
  successMsg: string,
  failureMsgPrefix: string,
) => {
  let interval = 1500

  const poll = async () => {
    if (get().activeRunId !== runId) return // stopped externally
    try {
      const p = await api.getRunStatus(runId)
      set({ liveRun: p, pollInterval: 1500 })
      interval = 1500

      if (p.status === 'succeeded' || p.status === 'failed') {
        const isSuccess = p.status === 'succeeded'

        // Patch runSummaries in place
        const { runSummaries } = get()
        const summary = progressToSummary(p)
        const idx = runSummaries.findIndex((r) => r.run_id === runId)
        const updatedSummaries =
          idx >= 0
            ? runSummaries.map((r) => (r.run_id === runId ? summary : r))
            : [summary, ...runSummaries]

        set({ runSummaries: updatedSummaries, activeRunId: null, pollTimer: null })

        // Keep liveRun briefly so RunDetail can display final state, then clear
        setTimeout(() => {
          if (get().liveRun?.run_id === runId) set({ liveRun: null })
        }, 3000)

        get().showToast(
          isSuccess
            ? successMsg
            : `${failureMsgPrefix}: ${p.error_message ?? 'Unknown error'}`,
          !isSuccess,
        )
        return
      }

      const timer = setTimeout(poll, interval)
      set({ pollTimer: timer })
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        set({ activeRunId: null, liveRun: null, pollTimer: null })
        get().showToast('Run no longer available', true)
        return
      }
      interval = Math.min(interval * 2, 10000)
      set({ pollInterval: interval })
      const timer = setTimeout(poll, interval)
      set({ pollTimer: timer })
    }
  }

  const timer = setTimeout(poll, 1500)
  set({ pollTimer: timer })
}
```

- [ ] **Step 5: Rewrite `startRun` to use `_startPolling`**

Replace the entire `startRun` action:

```ts
startRun: async (seedPrompt?: string, tags?: string[]) => {
  const { pipeline } = get()
  if (!pipeline) return
  get().stopPolling()
  try {
    const progress = await api.startRun(pipeline, seedPrompt, tags)
    set({ activeRunId: progress.run_id, liveRun: progress, pollInterval: 1500 })
    _startPolling(progress.run_id, 'Run completed successfully', 'Run failed')
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to start run'
    get().showToast(msg, true)
  }
},
```

- [ ] **Step 6: Rewrite `rerunFromRun` to use `_startPolling`**

Replace the entire `rerunFromRun` action:

```ts
rerunFromRun: async (runId, seedPrompt, tags) => {
  get().stopPolling()
  try {
    const progress = await api.rerunRun(runId, seedPrompt, tags)
    set({ activeRunId: progress.run_id, liveRun: progress, pollInterval: 1500 })
    _startPolling(progress.run_id, 'Re-run completed successfully', 'Re-run failed')
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to start re-run'
    get().showToast(msg, true)
  }
},
```

- [ ] **Step 7: Rewrite `retryBlock` to use `_startPolling`**

Replace the entire `retryBlock` action:

```ts
retryBlock: async (runId, blockId) => {
  get().stopPolling()
  try {
    const progress = await api.retryBlock(runId, blockId)
    set({ activeRunId: runId, liveRun: progress, pollInterval: 1500 })
    _startPolling(runId, 'Block retry completed successfully', 'Block retry failed')
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to retry block'
    get().showToast(msg, true)
  }
},
```

- [ ] **Step 8: Rewrite `loadRunProgress` to use `liveRun`**

Replace the entire `loadRunProgress` action:

```ts
loadRunProgress: async (runId) => {
  try {
    const progress = await api.getRunStatus(runId)
    set({ activeRunId: runId, liveRun: progress })
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to load run progress'
    get().showToast(msg, true)
  }
},
```

- [ ] **Step 9: Update `stopPolling` to also clear `liveRun`**

```ts
stopPolling: () => {
  const { pollTimer } = get()
  if (pollTimer) {
    clearTimeout(pollTimer)
    set({ pollTimer: null })
  }
  set({ activeRunId: null, liveRun: null })
},
```

Wait — `stopPolling` was called by `startRun`, `rerunFromRun`, and `retryBlock` at the START of those actions (to stop any previous run's polling). It should clear the old run state. This is correct.

- [ ] **Step 10: Fix TypeScript — update `StudioState` action signatures**

The `StudioState` interface doesn't need `activeRunProgress` anymore. Also remove it from the `StudioData` interface if it appeared there (it didn't — `StudioData` only has the catalog/settings data).

- [ ] **Step 11: Commit**

```bash
git add python_director/admin_ui_v3/src/store.ts
git commit -m "refactor: replace activeRunProgress with liveRun, extract _startPolling helper"
```

---

## Task 4: RunList — subscribe to liveRun, update active run card

**Files:**
- Modify: `src/components/runs/RunList.tsx`

- [ ] **Step 1: Replace `activeRunProgress` subscription with `liveRun`**

Replace:
```ts
const activeRunId = useStore((s) => s.activeRunId)
const activeRunProgress = useStore((s) => s.activeRunProgress)
```
with:
```ts
const liveRun = useStore((s) => s.liveRun)
```

`activeRunId` is now `liveRun?.run_id` — derive it inline where needed.

- [ ] **Step 2: Update active run card rendering**

The active run card (lines 56-86) currently reads `activeRunId && activeRunProgress && (...)`. Update:

```tsx
{liveRun && (
  <button
    type="button"
    onClick={() => navigate(`/runs/${liveRun.run_id}/blocks`)}
    className="w-full text-left p-3 rounded-xl bg-mint-soft border border-mint/30 cursor-pointer transition-colors hover:brightness-110"
  >
    <div className="flex items-center gap-2 mb-2">
      <StatusDot status="running" />
      <span className="text-sm font-medium text-mint">Active Run</span>
    </div>
    <div className="text-xs text-text-dim mb-1">
      {liveRun.pipeline_name}
    </div>
    <div className="w-full h-1.5 bg-surface rounded-full overflow-hidden">
      <div
        className="h-full bg-mint rounded-full transition-all duration-500"
        style={{
          width: `${
            liveRun.block_count > 0
              ? (Object.values(liveRun.block_traces).filter(
                  (t) => t.status === 'succeeded' || t.status === 'failed',
                ).length /
                  liveRun.block_count) *
                100
              : 0
          }%`,
        }}
      />
    </div>
  </button>
)}
```

- [ ] **Step 3: Fix the empty-state guard**

`RunList.tsx` line 88 currently reads `{runSummaries.length === 0 && !activeRunId && (...)}`. After removing the `activeRunId` subscription, replace with `!liveRun`:

```tsx
{runSummaries.length === 0 && !liveRun && (
  <p className="text-text-dim text-sm p-2">
    No runs yet. Start a dry run from the Pipeline Editor.
  </p>
)}
```

- [ ] **Step 4: Update `handleRerun` (no longer needs `activeRunId`)**

Confirm the `handleRerun` function (from Task 2) no longer references `activeRunId`. It should now just be:

```tsx
const handleRerun = (seedPrompt: string, tags: string[]) => {
  if (!rerunTarget) return
  setRerunTarget(null)
  rerunFromRun(rerunTarget.run_id, seedPrompt || null, tags)
}
```

- [ ] **Step 5: Commit**

```bash
git add python_director/admin_ui_v3/src/components/runs/RunList.tsx
git commit -m "refactor: RunList subscribes to liveRun instead of activeRunProgress"
```

---

## Task 5: RunDetail — fix subscription to stop stale re-renders

**Files:**
- Modify: `src/components/runs/RunDetail.tsx`

- [ ] **Step 1: Replace `activeRunProgress` / `activeRunId` subscriptions with selective `liveRun`**

Replace:
```ts
const activeRunProgress = useStore((s) => s.activeRunProgress)
const activeRunId = useStore((s) => s.activeRunId)
```
with a single selective selector that returns non-null only when liveRun is for this run:

```ts
// Returns liveRun only when it's for THIS run — null otherwise
// This prevents re-renders when a different run is active
const liveRun = useStore((s) =>
  s.liveRun?.run_id === runId ? s.liveRun : null
)
```

- [ ] **Step 2: Replace the two useEffects with a single clean one**

Delete the existing two useEffects (lines 30-57). Replace with:

```ts
// Load run data on mount (by runId navigation)
useEffect(() => {
  if (!runId) return
  if (liveRun) {
    // This is the active run — use live data
    setRunData(liveRun)
    setLoading(false)
    return
  }
  setLoading(true)
  api
    .getRunStatus(runId)
    .then((data) => {
      setRunData(data)
      setLoading(false)
    })
    .catch((err) => {
      const msg = err instanceof Error ? err.message : 'Failed to load run'
      showToast(msg, true)
      setLoading(false)
    })
}, [runId]) // eslint-disable-line react-hooks/exhaustive-deps

// Sync live progress into local state when this is the active run
useEffect(() => {
  if (liveRun) {
    setRunData(liveRun)
    setLoading(false)
  }
}, [liveRun])
```

The key difference: `liveRun` is null for non-active runs (the selective selector above), so the second effect is effectively a no-op for those runs. Only the active run triggers `setRunData` every poll tick.

- [ ] **Step 3: Update `isActive` derivation**

The existing `const isActive = runId === activeRunId` now becomes:

```ts
const isActive = liveRun !== null
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd python_director/admin_ui_v3 && npx tsc --noEmit
```

Expected: 0 errors. Fix any type issues.

- [ ] **Step 5: Commit**

```bash
git add python_director/admin_ui_v3/src/components/runs/RunDetail.tsx
git commit -m "fix: RunDetail uses selective liveRun selector to stop spurious re-renders"
```

---

## Task 6: BlockList — migrate activeRunProgress → liveRun

**Files:**
- Modify: `src/components/pipeline/BlockList.tsx`

`BlockList` shows a `StatusDot` next to each block in the pipeline editor, lit up during an active run. It reads `activeRunProgress` to get per-block traces.

- [ ] **Step 1: Replace the subscription**

`BlockList.tsx` line 8 — change:
```ts
const activeRunProgress = useStore((s) => s.activeRunProgress)
```
to:
```ts
const liveRun = useStore((s) => s.liveRun)
```

- [ ] **Step 2: Update the trace lookup**

`BlockList.tsx` line 33 — change:
```ts
const trace = activeRunProgress?.block_traces?.[block.id]
```
to:
```ts
const trace = liveRun?.block_traces?.[block.id]
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd python_director/admin_ui_v3 && npx tsc --noEmit
```

Expected: 0 errors.

- [ ] **Step 4: Commit**

```bash
git add python_director/admin_ui_v3/src/components/pipeline/BlockList.tsx
git commit -m "refactor: BlockList subscribes to liveRun instead of activeRunProgress"
```

---

## Task 7: End-to-end manual verification

- [ ] **Step 1: Start the API server and admin UI**

```bash
# Terminal 1 — Python API
python -m uvicorn python_director.api:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2 — Admin UI dev server
cd python_director/admin_ui_v3 && npm run dev
```

- [ ] **Step 2: Verify retry mode toggle**

1. Open the runs list
2. Hover any completed run → click ↺
3. Confirm "Same Seed" is selected, seed prompt is pre-filled
4. Click "New Seed" → confirm seed prompt clears and textarea is focused
5. Switch back to "Same Seed" → confirm seed re-populates
6. From RunDetail of a finished run → click "Re-run" → confirm same toggle behaviour

- [ ] **Step 3: Verify polling doesn't cause jarring navigation**

1. Navigate to an older run's Timeline tab
2. Start a new dry-run from the pipeline editor
3. Confirm: you stay on the old run's Timeline — no navigation jump, no scroll reset
4. The active run badge appears in the sidebar
5. Click the active run badge → go to its Blocks view
6. Confirm block statuses update live without full-page refreshes

- [ ] **Step 4: Verify completion handling**

1. Wait for the active run to complete (or run a minimal pipeline)
2. Confirm: toast appears ("Run completed successfully")
3. Confirm: the new run appears in the sidebar run list without reloading the page
4. Confirm: you are NOT navigated away from whatever you were viewing

- [ ] **Step 5: Final commit (if any cleanup needed)**

```bash
git add -p   # review any remaining changes
git commit -m "chore: admin UI polish after polling refactor"
```
