# Director Studio v3: React UI Redesign

## 1. Problem Statement

The current Director Studio admin UI is a single-file vanilla HTML/CSS/JS application (~740 lines). A recent refactor degraded the experience, and the feature set needs significant expansion: live run monitoring with per-block I/O inspection, non-technical content formatting, experience preview ("uber-view"), and improved pipeline management. The vanilla approach won't scale to these requirements or future plans (multi-user, pipeline categories, user management).

## 2. Solution Overview

Replace the vanilla admin UI with a **Vite + React + TypeScript** application using **Tailwind CSS** and **Zustand** for state management. The new UI uses a **hybrid layout**: a persistent collapsible sidebar for pipeline structure/navigation, with a tab-routed main content area that switches between three top-level views: **Pipeline Editor**, **Runs**, and **Compare**.

FastAPI continues to serve the built UI as static files. Build and install scripts are updated so setup remains single-click.

## 3. Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Build tool | Vite | Fast HMR, zero-config React/TS support |
| UI framework | React 18 + TypeScript | Component model, type safety matching Pydantic models |
| Styling | Tailwind CSS | Rapid utility-first styling, easy custom dark theme |
| State | Zustand | Lightweight, no boilerplate, supports selectors |
| Routing | React Router v6 | URL-driven view switching, bookmarkable states |
| HTTP | fetch (built-in) | No axios needed for this scope |

No additional UI component libraries. All components are custom-built to match the existing glassmorphic dark aesthetic.

## 4. Layout Architecture

```
┌──────────────────────────────────────────────────────────────┐
│ TopBar                                                        │
│ Brand: "Director Studio"                                      │
│ Nav: [Pipeline Editor] [Runs] [Compare]                       │
│ Right: [● Running...] [Settings] [Dry Run]                    │
├──────────────┬───────────────────────────────────────────────┤
│ Sidebar      │  Main Content Area                             │
│ (collapsible)│  (route-dependent)                             │
│              │                                                │
│ ┌──────────┐ │                                                │
│ │ Pipeline │ │                                                │
│ │ Meta     │ │                                                │
│ │ Name,    │ │                                                │
│ │ Desc,    │ │                                                │
│ │ Defaults │ │                                                │
│ ├──────────┤ │                                                │
│ │ Saved    │ │                                                │
│ │ Pipelines│ │                                                │
│ │ Load/Save│ │                                                │
│ ├──────────┤ │                                                │
│ │ Block    │ │                                                │
│ │ List     │ │                                                │
│ │ (status  │ │                                                │
│ │  dots)   │ │                                                │
│ ├──────────┤ │                                                │
│ │ Templates│ │                                                │
│ │ Rail     │ │                                                │
│ ├──────────┤ │                                                │
│ │ Actions  │ │                                                │
│ │ Save,    │ │                                                │
│ │ Snapshot,│ │                                                │
│ │ Reset    │ │                                                │
│ └──────────┘ │                                                │
├──────────────┴───────────────────────────────────────────────┤
│ Toast Notifications                                           │
└──────────────────────────────────────────────────────────────┘
```

The sidebar is visible in all views. It shows the pipeline block list with real-time status dots during runs. A collapse toggle reduces it to an icon rail.

## 5. Polling & Live Run Monitoring

The UI polls `GET /api/runs/{run_id}/status` for live run updates.

- **Interval**: 1.5 seconds while a run is active
- **Backoff**: If a poll request fails (network error or 5xx), double the interval up to a max of 10 seconds. Reset to 1.5s on next successful poll.
- **Termination**: Stop polling when `status` is `succeeded` or `failed`. Refresh the run list on termination.
- **QUEUED state**: Between `/api/runs/start` returning and the background task beginning, the run has `status: "queued"` with no block traces. The UI shows a "Starting..." state with an indeterminate spinner.
- **Cleanup**: The backend removes entries from the in-memory `active_runs` dict 60 seconds after the run reaches a terminal status (`succeeded` or `failed`). After removal, the polling endpoint falls back to on-disk data seamlessly.

## 6. Views

### 6.1 Pipeline Editor (`/editor`)

The default view. Selecting a block in the sidebar opens its inspector in the main area.

**Block Inspector sections (all collapsible):**

- **Identity**: Block ID (editable, auto-cascades renames), Block Name, Block Type (read-only badge)
- **Execution Config**: Enabled toggle, Provider (Gemini/OpenAI), Model Source (Pipeline Default / Custom Override), Model selector, Temperature slider, Response Schema dropdown
- **System Instruction**: Monospace textarea with syntax-aware styling
- **Prompt Template**: Larger monospace textarea. Dependency placeholders (`{{block_id}}`) are highlighted inline
- **Dependencies**: Checkbox list of other blocks
- **Actions**: Move Up/Down, Duplicate, Delete

When no block is selected, the main area shows a welcome state: pipeline overview stats (block count, provider breakdown) and a textual dependency summary listing each block and its inputs.

Block ID rename is a frontend-only operation: when the user changes a block ID, the UI updates all `input_blocks` arrays and `{{old_id}}` references in prompt templates across the in-memory pipeline before saving.

### 6.2 Runs View (`/runs` and `/runs/:runId`)

**Left sub-panel: Run List**
- Active runs at top with pulsing mint indicator and progress percentage
- Historical runs below, sorted newest-first
- Each card shows: timestamp, pipeline name, status badge (succeeded/failed), quality proxy score (from `final_metrics.quality_proxy_score`), word count
- Click to select → loads into main area

**Main area for selected run — 3 sub-tabs:**

The 3 sub-tabs are rendered as nested tabs within the main content area (not top-level nav). URL routing: `/runs/:runId/blocks`, `/runs/:runId/timeline`, `/runs/:runId/experience`. Default sub-tab is `blocks`. Back button navigates between sub-tabs, then back to the run list.

#### 6.2.1 Blocks Tab
Vertical accordion of pipeline blocks in execution order:
- Each block header shows: name, type badge, provider badge, status dot, elapsed time
- Expanding a block reveals:
  - **Input section**: The resolved prompt rendered as formatted text (not raw). Dependency inputs shown as labeled cards.
  - **Output section**: Rendered contextually based on content type (see Section 7: Content Formatting)
  - **Error section** (if failed): Clear error message banner + collapsible "Technical Details" with full traceback
- For a live-running pipeline: completed blocks are expandable, the currently running block shows a skeleton/spinner, pending blocks are grayed out

#### 6.2.2 Timeline Tab
Chronological vertical timeline of all story artifacts extracted from the run's final output:
- Each entry: time marker (Day X, HH:MM AM/PM), type icon (journal/chat/email/receipt/voice), title, content preview (first ~100 chars)
- Entries are color-coded by type
- Clicking an entry expands to show full content in a formatted card

#### 6.2.3 Experience Preview Tab ("Uber-View")
Simulates the reader's experience as a vertical feed of artifact cards, grouped by delivery time:

```
── Day 1 ──────────────────────────────
  09:00 AM
  ┌─ NOTIFICATION ─────────────────┐
  │ 🔔 New journal entry available  │
  └─────────────────────────────────┘
  ┌─ JOURNAL ───────────────────────┐
  │ "The Morning After"             │
  │ I woke up to three missed       │
  │ calls from a number I don't...  │
  └─────────────────────────────────┘

  10:30 AM
  ┌─ CHAT ──────────────────────────┐
  │ Alex: Hey, are you okay?        │
  │ You: Yeah, what happened?       │
  │ Alex: Check your email. Now.    │
  └─────────────────────────────────┘

  11:00 AM
  ┌─ EMAIL ─────────────────────────┐
  │ From: noreply@firstbank.com     │
  │ Subject: Unusual Activity Alert │
  │ Dear Customer, we detected...   │
  └─────────────────────────────────┘
```

Each artifact type has its own card style:
- **Journal**: Paper/note aesthetic, title + body
- **Chat**: Bubble layout with sender alignment (protagonist right, others left)
- **Email**: Email card with From/Subject/Body
- **Receipt**: Transaction card with merchant, amount, description
- **Voice Note**: Audio-note style with speaker + transcript

#### 6.2.4 Upload to Firestore
For succeeded runs, a "Upload to Firestore" button appears in the run detail header. It calls `POST /api/upload/{run_id}`. The button is disabled if Google credentials are not configured (checked via settings status). Shows a confirmation dialog before uploading. On success, shows a toast with the `story_id`.

### 6.3 Compare View (`/compare`)

- Two run selectors (dropdowns)
- **Metrics panel**: Grid of delta cards showing baseline vs candidate for all story metrics (total artifacts, word counts by type, quality proxy score). Green/red color coding for improvements/regressions.
- **Quality Notes**: Auto-generated summary bullets (from existing `compare_final_outputs` API)
- **Side-by-side Experience Preview**: Both runs' uber-views rendered side-by-side with synchronized scrolling
- **Block-by-block diff** (optional expandable section): For each block, show output from both runs side-by-side

## 7. Run-in-Progress Indicator

Regardless of which view is active, the top bar shows:
- A pulsing mint dot + "Running: {pipeline_name}..." text
- A mini progress bar (percentage)
- Clicking it navigates to `/runs/{active_run_id}`

The sidebar block list always shows live status dots during a run (pending/running/succeeded/failed). The "Dry Run" button in the top bar is disabled while a run is active.

## 8. Settings Dialog

Accessed via the "Settings" button in the top bar. Opens as a modal dialog.

**Contents:**
- Gemini API Key (password input)
- OpenAI API Key (password input)
- Google Credentials Path (text input)
- Status badges showing which providers are configured (green READY / red MISSING)
- "Save Changes" button → calls `PUT /api/settings`
- "Cancel" button → closes without saving
- "Fresh Start" button (danger) → clears localStorage, resets pipeline to default, reloads studio

Settings values sync to the backend on save and are cached in `localStorage` to survive refreshes. The dialog pre-fills from the backend response (settings payload from the `/api/studio` bootstrap).

## 9. Content Formatting (Non-Technical Users)

All block outputs are rendered through a formatting layer:

| Content Type | Rendering |
|---|---|
| `StoryPlan` | Labeled sections: Title, Characters (as cards with name/background/arc), Core Conflict, Act summaries |
| `BrainstormCritique` | Strengths/weaknesses as green/red bullet lists, actionable items as a checklist |
| `StoryCritique` | Similar to BrainstormCritique with pacing/character sections |
| `SceneList` | Visual timeline of scenes with time ranges and expected artifacts |
| `ContinuityAudit` | Score badge, contradictions as warning cards, release recommendation as a status banner |
| `DropPlan` | Event timeline with intensity badges, quiet windows shown as gaps |
| `StoryGenerated` | Full experience preview (same as uber-view) |
| Plain text | Formatted prose with paragraph breaks |
| Unknown JSON | Formatted JSON with syntax highlighting + "View Raw" toggle |

A "View Raw JSON" toggle is available on every output card for power users.

## 10. Error & Empty States

| State | Behavior |
|---|---|
| Backend unreachable | Full-screen error overlay: "Cannot reach Director Studio backend. Is the server running on port 8001?" with a "Retry" button |
| No API keys configured | Banner at top of editor view: "Configure API keys in Settings before running a pipeline" |
| No runs exist | Runs view shows empty state: "No runs yet. Start a dry run from the Pipeline Editor." |
| No saved pipelines | Pipeline library dropdown shows "No saved pipelines" with save button still enabled |
| No blocks in pipeline | Block list shows "Add blocks using the template rail below" |
| Poll returns 404 | Stop polling, show toast: "Run no longer available", refresh run list |
| Run started without keys | Show the API error from the backend as a toast (the backend already validates this) |

## 11. API Changes

### 11.1 API Route Prefix

All backend API endpoints move under the `/api/` prefix to cleanly separate API routes from SPA routes. For example:
- `GET /studio` → `GET /api/studio`
- `PUT /pipeline` → `PUT /api/pipeline`
- `POST /runs/start` → `POST /api/runs/start`
- `GET /runs/{run_id}/status` → `GET /api/runs/{run_id}/status`
- `POST /compare` → `POST /api/compare`
- `PUT /settings` → `PUT /api/settings`
- etc.

Implementation: wrap all existing routes in an `APIRouter(prefix="/api")` and mount it on the app.

### 11.2 Fix `derive_story_timeline()` (logic.py)
Currently only extracts journals and chats. Must also extract:
- Emails: `event_type="email"`, `title=subject`, `block_id=f"email_{i}"`
- Receipts: `event_type="receipt"`, `title=merchantName`, `block_id=f"receipt_{i}"`
- Voice notes: `event_type="voice_note"`, `title=speaker`, `block_id=f"voice_note_{i}"`

### 11.3 Enrich `RunTimelineEntry` with content

Add an optional `content: dict[str, Any] | None` field to `RunTimelineEntry`. The `derive_story_timeline()` function populates it with the full artifact data (e.g., the journal's title+body, the chat message, the email fields). This allows the Timeline and Experience Preview tabs to render content directly from the timeline entries without cross-referencing back to `final_output`.

### 11.4 New Endpoint: `DELETE /api/pipelines/{key}`
Delete a saved pipeline from the library.

```python
@router.delete("/pipelines/{key}")
async def delete_named_pipeline(key: str):
    # Delete the file at PIPELINES_DIR / f"{key}.json"
    # Return 404 if not found
    # Return {"status": "ok"}
```

### 11.5 New Endpoint: `GET /api/runs/{run_id}/pipeline`
Return the pipeline snapshot used for a specific run. Returns 404 if the snapshot does not exist (pre-snapshot-era runs).

```python
@router.get("/runs/{run_id}/pipeline")
async def get_run_pipeline(run_id: str):
    # Read RUNS_DIR / run_id / "pipeline_snapshot.json"
    # Return as PipelineDefinition, or 404
```

### 11.6 `active_runs` Cleanup

Add a cleanup mechanism: after a run reaches terminal status (`succeeded` or `failed`), a background task waits 60 seconds and then removes the entry from `active_runs`. This prevents unbounded memory growth while giving the polling client time to observe the final state.

### 11.7 Serve React Build (SPA Fallback)

With the `/api/` prefix in place, the SPA fallback is safe:

```python
REACT_BUILD_DIR = BASE_DIR / "admin_ui_v3" / "dist"

# Serve built React assets
if REACT_BUILD_DIR.exists():
    app.mount("/assets", StaticFiles(directory=REACT_BUILD_DIR / "assets"), name="assets")

# SPA fallback: serve index.html for all non-API routes
# This is registered AFTER the /api router and /assets mount
@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    index = REACT_BUILD_DIR / "index.html"
    if not index.exists():
        raise HTTPException(404, "UI not built. Run: npm run build in admin_ui_v3/")
    return FileResponse(index)
```

During migration: if `admin_ui_v3/dist/` does not exist, fall back to serving the old `admin_ui/` directory at `/admin-static` as before.

## 12. Project Structure

```
python_director/
├── admin_ui/          # OLD - kept temporarily for reference, then deleted
├── admin_ui_v3/       # NEW React application
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx           # Entry point
│   │   ├── App.tsx            # Router + layout shell
│   │   ├── store.ts           # Zustand store (pipeline, runs, settings, UI state)
│   │   ├── api.ts             # API client (typed fetch wrappers)
│   │   ├── types.ts           # TypeScript interfaces matching Pydantic models
│   │   ├── theme.ts           # Tailwind theme tokens / shared constants
│   │   │
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── TopBar.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── Toast.tsx
│   │   │   ├── pipeline/
│   │   │   │   ├── BlockList.tsx        # Sidebar block nav
│   │   │   │   ├── BlockInspector.tsx   # Editor main content
│   │   │   │   ├── PipelineMeta.tsx     # Name, desc, defaults
│   │   │   │   ├── PipelineLibrary.tsx  # Save/load pipelines
│   │   │   │   └── TemplateRail.tsx     # Add block templates
│   │   │   ├── runs/
│   │   │   │   ├── RunList.tsx          # Active + historical runs
│   │   │   │   ├── RunDetail.tsx        # Selected run container
│   │   │   │   ├── BlockAccordion.tsx   # Expandable block I/O
│   │   │   │   ├── TimelineView.tsx     # Chronological timeline
│   │   │   │   └── ExperiencePreview.tsx# Uber-view
│   │   │   ├── compare/
│   │   │   │   ├── CompareView.tsx      # Run selector + results
│   │   │   │   ├── MetricDeltas.tsx     # Delta cards grid
│   │   │   │   └── SideBySide.tsx       # Dual experience preview
│   │   │   ├── formatting/
│   │   │   │   ├── ContentRenderer.tsx  # Smart output formatter
│   │   │   │   ├── StoryPlanCard.tsx
│   │   │   │   ├── CritiqueCard.tsx
│   │   │   │   ├── JournalCard.tsx
│   │   │   │   ├── ChatBubble.tsx
│   │   │   │   ├── EmailCard.tsx
│   │   │   │   ├── ReceiptCard.tsx
│   │   │   │   ├── VoiceNoteCard.tsx
│   │   │   │   └── RawJsonViewer.tsx
│   │   │   └── shared/
│   │   │       ├── StatusDot.tsx
│   │   │       ├── CollapsibleSection.tsx
│   │   │       ├── Badge.tsx
│   │   │       └── SettingsDialog.tsx
│   │   │
│   │   └── views/
│   │       ├── EditorView.tsx
│   │       ├── RunsView.tsx
│   │       └── CompareView.tsx
│   │
│   └── dist/                  # Built output (gitignored, generated by npm run build)
```

## 13. Zustand Store Shape

```typescript
interface StudioStore {
  // Bootstrap data
  studio: StudioBootstrap | null;
  pipeline: PipelineDefinition | null;
  pipelineCatalog: PipelineCatalogItem[];
  runs: RunSummary[];

  // UI state
  selectedBlockId: string | null;
  sidebarCollapsed: boolean;
  activeRunId: string | null;
  activeRunProgress: RunProgress | null;
  pollTimer: number | null;

  // Actions
  loadStudio: () => Promise<void>;
  savePipeline: () => Promise<void>;
  selectBlock: (id: string | null) => void;
  startRun: () => Promise<void>;
  loadRun: (runId: string) => Promise<RunProgress>;
  // ... etc
}
```

## 14. Tailwind Theme Configuration

Custom theme extending Tailwind defaults to match the glassmorphic dark aesthetic:

```javascript
// Key design tokens
colors: {
  bg: '#0a0a0a',
  surface: 'rgba(255, 255, 255, 0.05)',
  'surface-raised': 'rgba(255, 255, 255, 0.08)',
  border: 'rgba(255, 255, 255, 0.1)',
  mint: '#0fe6b0',
  'mint-soft': 'rgba(15, 230, 176, 0.15)',
  amber: '#ffb74d',
  'amber-soft': 'rgba(255, 183, 77, 0.15)',
  danger: '#ff5252',
}
fontFamily: {
  sans: ['Inter', ...],
  mono: ['JetBrains Mono', ...],
}
```

Glassmorphic panels use `backdrop-blur-xl bg-surface border border-border rounded-2xl`.

## 15. Vite Dev Proxy Configuration

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
  },
});
```

## 16. Build & Deployment Scripts

### Updated `script/director-install.ps1`
```
1. Create Python venv if needed
2. pip install -r requirements.txt
3. Check for Node.js (error with install instructions if missing)
4. cd admin_ui_v3 && npm install && npm run build
5. Print success
```

### Updated `script/director-admin.ps1`
```
1. Check if admin_ui_v3/dist exists; if not, run npm build
2. Start uvicorn as before
```

### New `script/director-ui-dev.ps1`
```
1. Start Vite dev server (port 5173) with proxy to FastAPI (port 8001)
2. For hot-reload during UI development
```

All `.cmd` wrappers remain unchanged (they just invoke the `.ps1` files).

## 17. Migration Plan

1. Create `admin_ui_v3/` as a new React project alongside the existing `admin_ui/`
2. FastAPI serves whichever exists (prefer `admin_ui_v3/dist/` if present, fall back to `admin_ui/`)
3. Once v3 is complete and validated, remove the old `admin_ui/` directory
4. Update `.gitignore` to exclude `admin_ui_v3/node_modules/` and `admin_ui_v3/dist/`

## 18. Out of Scope (Future)

- Multi-user support / authentication
- Pipeline categories and tagging
- WebSocket-based live updates (polling is sufficient for single-user)
- Drag-and-drop block reordering (move up/down buttons are sufficient)
- Visual dependency graph editor
