# Director Studio v3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the vanilla JS admin UI with a React + Vite + TypeScript application, adding live run monitoring, experience preview, content formatting, and run comparison.

**Architecture:** Two-phase build: (1) Backend API changes — `/api/` prefix, new endpoints, timeline enrichment, active_runs cleanup; (2) React SPA — Zustand store, React Router views (Editor, Runs, Compare), Tailwind glassmorphic theme. FastAPI serves the built React app with SPA fallback.

**Tech Stack:** Python/FastAPI (backend), React 18 + TypeScript + Vite (frontend), Tailwind CSS (styling), Zustand (state), React Router v6 (routing)

**Spec:** `docs/superpowers/specs/2026-03-20-director-studio-v3-design.md`

---

## File Map

### Backend Changes (Python)
| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `python_director/api.py` | Move routes to APIRouter with `/api/` prefix, add SPA fallback, new endpoints |
| Modify | `python_director/models.py` | Add `content` field to `RunTimelineEntry` |
| Modify | `python_director/logic.py` | Fix `derive_story_timeline()` to extract all artifact types with content |
| Modify | `python_director/storage.py` | Add `delete_named_pipeline()` function |
| Modify | `python_director/test_director.py` | Tests for new/changed endpoints and logic |
| Modify | `.gitignore` | Add admin_ui_v3/node_modules/, admin_ui_v3/dist/ |

### Frontend (React/TypeScript) — all under `python_director/admin_ui_v3/`
| Action | File | Responsibility |
|--------|------|----------------|
| Create | `package.json` | Dependencies and scripts |
| Create | `tsconfig.json` | TypeScript config |
| Create | `vite.config.ts` | Vite build + dev proxy config |
| Create | `tailwind.config.ts` | Custom dark glassmorphic theme tokens |
| Create | `postcss.config.js` | PostCSS + Tailwind plugin |
| Create | `index.html` | SPA entry HTML |
| Create | `src/main.tsx` | React DOM entry point |
| Create | `src/index.css` | Tailwind directives + base styles |
| Create | `src/types.ts` | TypeScript interfaces matching Pydantic models |
| Create | `src/api.ts` | Typed fetch wrappers for all `/api/` endpoints |
| Create | `src/store.ts` | Zustand store: pipeline, runs, settings, UI state |
| Create | `src/App.tsx` | Router + layout shell (TopBar + Sidebar + Outlet) |
| Create | `src/components/layout/TopBar.tsx` | Brand, nav tabs, run indicator, settings/dry-run buttons |
| Create | `src/components/layout/Sidebar.tsx` | Collapsible sidebar with all pipeline sections |
| Create | `src/components/layout/Toast.tsx` | Toast notification system |
| Create | `src/components/pipeline/PipelineMeta.tsx` | Pipeline name, description, default model selectors |
| Create | `src/components/pipeline/PipelineLibrary.tsx` | Save/load/delete named pipelines |
| Create | `src/components/pipeline/BlockList.tsx` | Sidebar block navigation with status dots |
| Create | `src/components/pipeline/TemplateRail.tsx` | Add-block template buttons |
| Create | `src/components/pipeline/BlockInspector.tsx` | Block editor: identity, config, prompts, deps, actions |
| Create | `src/components/runs/RunList.tsx` | Active + historical run cards |
| Create | `src/components/runs/RunDetail.tsx` | Selected run container with sub-tabs |
| Create | `src/components/runs/BlockAccordion.tsx` | Expandable block I/O viewer |
| Create | `src/components/runs/TimelineView.tsx` | Chronological story timeline |
| Create | `src/components/runs/ExperiencePreview.tsx` | Uber-view: simulated reader experience |
| Create | `src/components/compare/CompareView.tsx` | Run selector + comparison results |
| Create | `src/components/compare/MetricDeltas.tsx` | Delta metric cards grid |
| Create | `src/components/compare/SideBySide.tsx` | Dual experience preview |
| Create | `src/components/formatting/ContentRenderer.tsx` | Smart output formatter (dispatches by schema type) |
| Create | `src/components/formatting/StoryPlanCard.tsx` | StoryPlan structured rendering |
| Create | `src/components/formatting/CritiqueCard.tsx` | BrainstormCritique + StoryCritique rendering |
| Create | `src/components/formatting/JournalCard.tsx` | Journal entry card |
| Create | `src/components/formatting/ChatBubble.tsx` | Chat message bubble |
| Create | `src/components/formatting/EmailCard.tsx` | Email card |
| Create | `src/components/formatting/ReceiptCard.tsx` | Receipt/transaction card |
| Create | `src/components/formatting/VoiceNoteCard.tsx` | Voice note card |
| Create | `src/components/formatting/RawJsonViewer.tsx` | Collapsible raw JSON viewer |
| Create | `src/components/shared/StatusDot.tsx` | Animated status indicator dot |
| Create | `src/components/shared/CollapsibleSection.tsx` | Collapsible panel wrapper |
| Create | `src/components/shared/Badge.tsx` | Status/type badge |
| Create | `src/components/shared/SettingsDialog.tsx` | Settings modal dialog |
| Create | `src/views/EditorView.tsx` | Pipeline editor main content |
| Create | `src/views/RunsView.tsx` | Runs list + detail view |
| Create | `src/views/CompareView.tsx` | Compare wrapper view |

### Scripts
| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `script/director-install.ps1` | Add Node.js check + npm install + npm build |
| Modify | `script/director-admin.ps1` | Auto-build if dist/ missing |
| Create | `script/director-ui-dev.ps1` | Start Vite dev server |
| Create | `script/director-ui-dev.cmd` | CMD wrapper for ui-dev |

---

## Task 1: Backend — API Route Prefix + New Endpoints

**Files:**
- Modify: `python_director/api.py`
- Modify: `python_director/storage.py`
- Modify: `python_director/models.py`
- Modify: `python_director/test_director.py`

- [ ] **Step 1: Add `content` field to `RunTimelineEntry` in models.py**

In `python_director/models.py`, add to `RunTimelineEntry`:
```python
class RunTimelineEntry(BaseModel):
    block_id: str
    event_type: str = "artifact_drop"
    story_day: int = 1
    story_time: str = "09:00 AM"
    title: str = ""
    content: Optional[dict[str, Any]] = None  # ADD THIS
```

- [ ] **Step 2: Add `delete_named_pipeline()` to storage.py**

In `python_director/storage.py`, add:
```python
def delete_named_pipeline(key: str) -> bool:
    path = _pipeline_path_by_key(key)
    if not path.exists():
        return False
    path.unlink()
    logger.info("Deleted named pipeline key=%s path=%s", key, path)
    return True
```

- [ ] **Step 3: Refactor api.py to use APIRouter with `/api/` prefix**

Replace the current flat route definitions with an `APIRouter`:
```python
from fastapi import APIRouter

router = APIRouter(prefix="/api")

# Move ALL existing @app.get/post/put routes to @router.get/post/put
# Example: @app.get("/studio") becomes @router.get("/studio")
# Do NOT move: admin_home, admin_alias, health check, static mounts

# After all route definitions:
app.include_router(router)
```

Keep `@app.get("/health")` on the app directly (no prefix).
Remove `@app.get("/")` and `@app.get("/admin")` — these will be replaced by SPA fallback.

- [ ] **Step 4: Add new endpoints to the router**

Add `DELETE /pipelines/{key}`:
```python
@router.delete("/pipelines/{key}")
async def delete_named_pipeline_endpoint(key: str):
    if not delete_named_pipeline(key):
        raise HTTPException(status_code=404, detail=f"Pipeline '{key}' not found")
    return {"status": "ok", "pipeline_catalog": list_named_pipelines()}
```

Add `GET /runs/{run_id}/pipeline`:
```python
@router.get("/runs/{run_id}/pipeline")
async def get_run_pipeline(run_id: str):
    snapshot_path = RUNS_DIR / run_id / "pipeline_snapshot.json"
    if not snapshot_path.exists():
        raise HTTPException(status_code=404, detail=f"Pipeline snapshot for run '{run_id}' not found")
    return PipelineDefinition.model_validate_json(snapshot_path.read_text(encoding="utf-8"))
```

- [ ] **Step 5: Add `active_runs` cleanup in `_bg_run_pipeline`**

In `api.py`, update `_bg_run_pipeline`:
```python
import asyncio
import threading

def _bg_run_pipeline(run_id: str, pipeline: PipelineDefinition, settings: AppSettings):
    runner = PipelineRunner(settings)

    def _progress_callback(p: RunProgress):
        active_runs[run_id] = p

    try:
        runner.run_pipeline(pipeline, run_id=run_id, progress_callback=_progress_callback)
    except Exception:
        pass
    finally:
        # Schedule cleanup after 60 seconds
        def _cleanup():
            import time
            time.sleep(60)
            active_runs.pop(run_id, None)
        threading.Thread(target=_cleanup, daemon=True).start()
```

- [ ] **Step 6: Add SPA fallback route**

At the bottom of `api.py`, after `app.include_router(router)`:
```python
REACT_BUILD_DIR = BASE_DIR / "admin_ui_v3" / "dist"

if REACT_BUILD_DIR.exists():
    app.mount("/assets", StaticFiles(directory=REACT_BUILD_DIR / "assets"), name="spa-assets")

# Legacy fallback for old UI during migration
elif ADMIN_UI_DIR.exists():
    app.mount("/admin-static", StaticFiles(directory=ADMIN_UI_DIR), name="admin-static")

@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    if REACT_BUILD_DIR.exists():
        index = REACT_BUILD_DIR / "index.html"
        if index.exists():
            return FileResponse(index)
    # Fallback to old admin UI
    old_index = ADMIN_UI_DIR / "index.html"
    if old_index.exists():
        return FileResponse(old_index)
    raise HTTPException(404, detail="Admin UI not found. Build the React app or ensure admin_ui/ exists.")
```

Remove the old static mount at the top of the file (the `if ADMIN_UI_DIR.exists(): app.mount(...)` block).

- [ ] **Step 7: Write tests for new/changed endpoints**

In `python_director/test_director.py`, add:
```python
def test_api_routes_have_api_prefix():
    """Verify all data routes are under /api/"""
    from python_director.api import app
    api_paths = [route.path for route in app.routes if hasattr(route, 'path')]
    # Studio endpoint should be under /api/
    assert any("/api/studio" in p for p in api_paths)
    assert any("/api/pipeline" in p for p in api_paths)

def test_delete_named_pipeline(tmp_path, monkeypatch):
    """Test deleting a named pipeline"""
    from python_director import storage
    monkeypatch.setattr(storage, "PIPELINES_DIR", tmp_path)
    # Create a fake pipeline file
    (tmp_path / "test_pipeline.json").write_text('{"name":"Test","blocks":[]}')
    assert storage.delete_named_pipeline("test_pipeline") is True
    assert not (tmp_path / "test_pipeline.json").exists()
    assert storage.delete_named_pipeline("nonexistent") is False
```

- [ ] **Step 8: Run tests**

Run: `cd G:/code/gen-ai/in_real_time_v1 && python -m pytest python_director/test_director.py -v`
Expected: All tests pass.

- [ ] **Step 9: Commit**

```bash
git add python_director/api.py python_director/models.py python_director/storage.py python_director/test_director.py
git commit -m "feat: add /api/ prefix, new endpoints, active_runs cleanup, SPA fallback"
```

---

## Task 2: Backend — Fix derive_story_timeline + Enrich Content

**Files:**
- Modify: `python_director/logic.py`
- Modify: `python_director/test_director.py`

- [ ] **Step 1: Write test for enriched timeline**

In `python_director/test_director.py`, add:
```python
def test_derive_story_timeline_all_types():
    from python_director.logic import derive_story_timeline
    final_output = {
        "story_title": "Test Story",
        "journals": [{"title": "Entry 1", "body": "Journal body", "time_offset_minutes": 0}],
        "chats": [{"senderId": "Alex", "text": "Hey", "isProtagonist": False, "time_offset_minutes": 30}],
        "emails": [{"sender": "test@example.com", "subject": "Alert", "body": "Email body", "time_offset_minutes": 60}],
        "receipts": [{"merchantName": "Coffee Shop", "amount": 4.50, "description": "Latte", "time_offset_minutes": 90}],
        "voice_notes": [{"speaker": "Unknown", "transcript": "Hello there", "time_offset_minutes": 120}],
    }
    timeline = derive_story_timeline(final_output)
    types = [e.event_type for e in timeline]
    assert "journal" in types
    assert "chat" in types
    assert "email" in types
    assert "receipt" in types
    assert "voice_note" in types
    assert len(timeline) == 5
    # Verify content is populated
    journal_entry = next(e for e in timeline if e.event_type == "journal")
    assert journal_entry.content is not None
    assert journal_entry.content["body"] == "Journal body"
    # Verify sorted by time
    times = [e.story_time for e in timeline]
    assert times == sorted(times)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd G:/code/gen-ai/in_real_time_v1 && python -m pytest python_director/test_director.py::test_derive_story_timeline_all_types -v`
Expected: FAIL (emails, receipts, voice_notes not extracted; content field missing)

- [ ] **Step 3: Update `derive_story_timeline()` in logic.py**

Replace the existing `derive_story_timeline` function in `python_director/logic.py`:
```python
def derive_story_timeline(final_output: Any) -> list[RunTimelineEntry]:
    if not isinstance(final_output, dict):
        return []

    entries: list[RunTimelineEntry] = []

    def _to_clock(total_mins: int) -> str:
        base_hour = 9
        hours = (base_hour + (total_mins // 60)) % 24
        mins = total_mins % 60
        ampm = "AM" if hours < 12 else "PM"
        display_hour = hours if hours <= 12 else hours - 12
        if display_hour == 0:
            display_hour = 12
        return f"{display_hour:02d}:{mins:02d} {ampm}"

    for i, j in enumerate(final_output.get("journals", [])):
        mins = j.get("time_offset_minutes", 0)
        entries.append(RunTimelineEntry(
            block_id=f"journal_{i}", event_type="journal",
            story_day=(mins // (24 * 60)) + 1, story_time=_to_clock(mins),
            title=j.get("title", f"Journal Entry {i+1}"),
            content=dict(j),
        ))

    for i, c in enumerate(final_output.get("chats", [])):
        mins = c.get("time_offset_minutes", 0)
        entries.append(RunTimelineEntry(
            block_id=f"chat_{i}", event_type="chat",
            story_day=(mins // (24 * 60)) + 1, story_time=_to_clock(mins),
            title=f"Chat: {c.get('senderId', 'Unknown')}",
            content=dict(c),
        ))

    for i, e in enumerate(final_output.get("emails", [])):
        mins = e.get("time_offset_minutes", 0)
        entries.append(RunTimelineEntry(
            block_id=f"email_{i}", event_type="email",
            story_day=(mins // (24 * 60)) + 1, story_time=_to_clock(mins),
            title=e.get("subject", f"Email {i+1}"),
            content=dict(e),
        ))

    for i, r in enumerate(final_output.get("receipts", [])):
        mins = r.get("time_offset_minutes", 0)
        entries.append(RunTimelineEntry(
            block_id=f"receipt_{i}", event_type="receipt",
            story_day=(mins // (24 * 60)) + 1, story_time=_to_clock(mins),
            title=r.get("merchantName", f"Receipt {i+1}"),
            content=dict(r),
        ))

    for i, v in enumerate(final_output.get("voice_notes", [])):
        mins = v.get("time_offset_minutes", 0)
        entries.append(RunTimelineEntry(
            block_id=f"voice_note_{i}", event_type="voice_note",
            story_day=(mins // (24 * 60)) + 1, story_time=_to_clock(mins),
            title=f"Voice: {v.get('speaker', 'Unknown')}",
            content=dict(v),
        ))

    entries.sort(key=lambda x: (x.story_day, x.story_time))
    return entries
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd G:/code/gen-ai/in_real_time_v1 && python -m pytest python_director/test_director.py::test_derive_story_timeline_all_types -v`
Expected: PASS

- [ ] **Step 5: Run all tests**

Run: `cd G:/code/gen-ai/in_real_time_v1 && python -m pytest python_director/test_director.py -v`
Expected: All tests pass.

- [ ] **Step 6: Commit**

```bash
git add python_director/logic.py python_director/models.py python_director/test_director.py
git commit -m "feat: enrich story timeline with all artifact types and content"
```

---

## Task 3: React Project Scaffold + Tailwind Theme

**Files:**
- Create: `python_director/admin_ui_v3/package.json`
- Create: `python_director/admin_ui_v3/tsconfig.json`
- Create: `python_director/admin_ui_v3/vite.config.ts`
- Create: `python_director/admin_ui_v3/tailwind.config.ts`
- Create: `python_director/admin_ui_v3/postcss.config.js`
- Create: `python_director/admin_ui_v3/index.html`
- Create: `python_director/admin_ui_v3/src/main.tsx`
- Create: `python_director/admin_ui_v3/src/index.css`
- Modify: `.gitignore`

- [ ] **Step 1: Initialize the Vite React TypeScript project**

Run from repo root:
```bash
cd G:/code/gen-ai/in_real_time_v1/python_director
npm create vite@latest admin_ui_v3 -- --template react-ts
```

- [ ] **Step 2: Install dependencies**

```bash
cd G:/code/gen-ai/in_real_time_v1/python_director/admin_ui_v3
npm install
npm install -D tailwindcss @tailwindcss/vite
npm install zustand react-router-dom
```

- [ ] **Step 3: Configure vite.config.ts**

Replace `python_director/admin_ui_v3/vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
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
    emptyOutDir: true,
  },
})
```

- [ ] **Step 4: Create src/index.css with Tailwind directives and base styles**

Replace `python_director/admin_ui_v3/src/index.css`:
```css
@import "tailwindcss";

@theme {
  --color-bg: #0a0a0a;
  --color-surface: rgba(255, 255, 255, 0.05);
  --color-surface-raised: rgba(255, 255, 255, 0.08);
  --color-border: rgba(255, 255, 255, 0.1);
  --color-text: #f0f0f0;
  --color-text-dim: #999;
  --color-mint: #0fe6b0;
  --color-mint-soft: rgba(15, 230, 176, 0.15);
  --color-amber: #ffb74d;
  --color-amber-soft: rgba(255, 183, 77, 0.15);
  --color-danger: #ff5252;
  --color-danger-soft: rgba(255, 82, 82, 0.15);
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
}

html, body, #root {
  margin: 0;
  height: 100%;
  background: var(--color-bg);
  color: var(--color-text);
  font-family: var(--font-sans);
  overflow: hidden;
}

/* Glassmorphic panel utility */
.glass-panel {
  background: var(--color-surface);
  backdrop-filter: blur(20px);
  border: 1px solid var(--color-border);
  border-radius: 16px;
}

/* Scrollbar styling */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.2); }

/* Background glow */
.bg-glow {
  position: fixed;
  inset: 0;
  z-index: -1;
  background:
    radial-gradient(circle at 0% 0%, rgba(15, 230, 176, 0.05) 0%, transparent 50%),
    radial-gradient(circle at 100% 100%, rgba(255, 183, 77, 0.05) 0%, transparent 50%);
}
```

- [ ] **Step 5: Update index.html**

Replace `python_director/admin_ui_v3/index.html`:
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Director Studio</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono&display=swap" rel="stylesheet">
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 6: Create minimal main.tsx and App.tsx**

`python_director/admin_ui_v3/src/main.tsx`:
```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)
```

`python_director/admin_ui_v3/src/App.tsx`:
```tsx
import { Routes, Route, Navigate } from 'react-router-dom'

export default function App() {
  return (
    <div className="h-full flex flex-col">
      <div className="bg-glow" />
      <header className="flex justify-between items-center px-6 py-4 bg-[rgba(10,10,10,0.8)] backdrop-blur-xl border-b border-border z-50">
        <h1 className="text-xl font-semibold tracking-tight">Director Studio</h1>
        <span className="text-text-dim text-sm">v3</span>
      </header>
      <main className="flex-1 flex items-center justify-center text-text-dim">
        <p>Scaffold loaded. Views coming next.</p>
      </main>
    </div>
  )
}
```

- [ ] **Step 7: Clean up Vite boilerplate**

Delete the generated `src/App.css`, `src/assets/`, and update `src/main.tsx` if needed.

- [ ] **Step 8: Update .gitignore**

Add to the root `.gitignore`:
```
python_director/admin_ui_v3/node_modules/
python_director/admin_ui_v3/dist/
```

- [ ] **Step 9: Verify the dev server starts**

```bash
cd G:/code/gen-ai/in_real_time_v1/python_director/admin_ui_v3
npm run dev
```
Expected: Vite dev server starts on http://localhost:5173, shows "Director Studio" header and scaffold message.

- [ ] **Step 10: Verify production build**

```bash
cd G:/code/gen-ai/in_real_time_v1/python_director/admin_ui_v3
npm run build
```
Expected: Build completes, `dist/` directory created with `index.html` and `assets/`.

- [ ] **Step 11: Commit**

```bash
git add python_director/admin_ui_v3/ .gitignore
git commit -m "feat: scaffold React + Vite + Tailwind project for Director Studio v3"
```

---

## Task 4: TypeScript Types + API Client + Zustand Store

**Files:**
- Create: `python_director/admin_ui_v3/src/types.ts`
- Create: `python_director/admin_ui_v3/src/api.ts`
- Create: `python_director/admin_ui_v3/src/store.ts`

- [ ] **Step 1: Create types.ts matching Pydantic models**

`python_director/admin_ui_v3/src/types.ts`:
```typescript
// Enums
export type ProviderType = 'GEMINI' | 'OPENAI'
export type RunStatus = 'queued' | 'running' | 'succeeded' | 'failed'
export type BlockExecutionStatus = 'pending' | 'running' | 'succeeded' | 'failed' | 'skipped'
export type BlockType =
  | 'creative_outliner' | 'brainstorm_critic' | 'brainstorm_rewriter'
  | 'planner' | 'critic' | 'reviser' | 'continuity_auditor'
  | 'decomposer' | 'drop_director' | 'generator'

// Pipeline
export interface BlockConfig {
  provider: ProviderType
  model_name: string | null
  use_pipeline_default_model: boolean
  temperature: number
  system_instruction: string
  prompt_template: string
  response_mime_type: string | null
  response_schema_name: string | null
}

export interface PipelineBlock {
  id: string
  name: string
  description: string
  type: BlockType
  enabled: boolean
  config: BlockConfig
  input_blocks: string[]
}

export interface PipelineDefinition {
  name: string
  description: string
  updated_at: string | null
  default_models: Record<string, string>
  blocks: PipelineBlock[]
}

export interface PipelineCatalogItem {
  key: string
  name: string
  description: string
  updated_at: string | null
  block_count: number
}

// Settings
export interface AppSettings {
  gemini_api_key: string | null
  openai_api_key: string | null
  google_application_credentials: string | null
}

export interface SettingsStatus {
  gemini_configured: boolean
  openai_configured: boolean
  google_credentials_configured: boolean
}

export interface SettingsPayload {
  settings: AppSettings
  status: SettingsStatus
}

// Runs
export interface BlockTrace {
  block_id: string
  block_name: string
  block_type: BlockType
  provider: ProviderType
  model_name: string
  status: BlockExecutionStatus
  response_schema_name: string | null
  temperature: number
  input_blocks: string[]
  resolved_prompt: string
  resolved_inputs: Record<string, unknown>
  output: unknown
  error_message: string | null
  error_traceback: string | null
  started_at: string | null
  completed_at: string | null
  elapsed_ms: number | null
}

export interface RunTimelineEntry {
  block_id: string
  event_type: string
  story_day: number
  story_time: string
  title: string
  content: Record<string, unknown> | null
}

export interface RunStats {
  total_words: number
  total_tokens: number
  estimated_cost_usd: number
  block_count: number
  success_rate: number
  average_tension_score: number | null
  character_mentions: Record<string, number>
}

export interface RunSummary {
  run_id: string
  timestamp: string
  pipeline_name: string
  status: RunStatus
  final_title: string | null
  block_count: number
  provider_summary: Record<string, number>
  artifact_counts: Record<string, number>
  final_metrics: Record<string, number>
  mode: string
  error_message: string | null
}

export interface RunProgress {
  run_id: string
  timestamp: string
  pipeline_name: string
  status: RunStatus
  mode: string
  block_count: number
  current_block_id: string | null
  started_at: string | null
  completed_at: string | null
  error_message: string | null
  final_title: string | null
  final_metrics: Record<string, number>
  block_sequence: string[]
  block_traces: Record<string, BlockTrace>
  timeline: RunTimelineEntry[]
  stats: RunStats
}

export interface RunResult extends RunSummary {
  current_block_id: string | null
  outputs: Record<string, unknown>
  final_output: unknown
  block_sequence: string[]
  block_traces: Record<string, BlockTrace>
  artifacts: { name: string; relative_path: string; size_bytes: number; content_type: string }[]
  timeline: RunTimelineEntry[]
  stats: RunStats
}

// Comparison
export interface MetricDelta {
  label: string
  baseline: number
  candidate: number
  delta: number
}

export interface RunComparison {
  baseline_run_id: string
  candidate_run_id: string
  baseline_title: string | null
  candidate_title: string | null
  metrics: MetricDelta[]
  quality_notes: string[]
  baseline_output: unknown
  candidate_output: unknown
}

// Block templates
export interface BlockTemplate {
  type: BlockType
  name: string
  description: string
  config: BlockConfig
}

// Studio bootstrap
export interface StudioBootstrap {
  pipeline: PipelineDefinition
  pipeline_catalog: PipelineCatalogItem[]
  settings: SettingsPayload
  run_summaries: RunSummary[]
  schemas: string[]
  block_types: BlockType[]
  block_templates: BlockTemplate[]
  provider_models: Record<string, string[]>
}
```

- [ ] **Step 2: Create api.ts with typed fetch wrappers**

`python_director/admin_ui_v3/src/api.ts`:
```typescript
import type {
  PipelineDefinition, StudioBootstrap, SettingsPayload,
  AppSettings, RunProgress, RunResult, RunComparison,
  PipelineCatalogItem,
} from './types'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...options.headers as Record<string, string> },
    ...options,
  })
  const text = await res.text()
  let data: T
  try { data = JSON.parse(text) } catch { data = text as unknown as T }
  if (!res.ok) {
    throw new Error((data as Record<string, string>)?.detail || text || `Request failed: ${res.status}`)
  }
  return data
}

export const api = {
  getStudio: () => request<StudioBootstrap>('/api/studio'),

  // Pipeline
  savePipeline: (pipeline: PipelineDefinition) =>
    request<PipelineDefinition>('/api/pipeline', { method: 'PUT', body: JSON.stringify(pipeline) }),
  resetPipeline: () =>
    request<PipelineDefinition>('/api/pipeline/reset', { method: 'POST', body: '{}' }),
  snapshotPipeline: (pipeline: PipelineDefinition, label?: string) =>
    request<{ status: string; path: string }>('/api/pipeline/snapshot', {
      method: 'POST', body: JSON.stringify({ pipeline, label }),
    }),

  // Named pipelines
  saveNamedPipeline: (name: string, pipeline: PipelineDefinition, set_active = true) =>
    request<{ pipeline: PipelineDefinition; catalog_item: PipelineCatalogItem; pipeline_catalog: PipelineCatalogItem[] }>(
      '/api/pipelines/save', { method: 'POST', body: JSON.stringify({ name, pipeline, set_active }) },
    ),
  loadNamedPipeline: (name: string, set_active = true) =>
    request<{ pipeline: PipelineDefinition; pipeline_catalog: PipelineCatalogItem[] }>(
      '/api/pipelines/load', { method: 'POST', body: JSON.stringify({ name, set_active }) },
    ),
  deleteNamedPipeline: (key: string) =>
    request<{ status: string; pipeline_catalog: PipelineCatalogItem[] }>(`/api/pipelines/${key}`, { method: 'DELETE' }),

  // Settings
  saveSettings: (settings: AppSettings) =>
    request<SettingsPayload>('/api/settings', { method: 'PUT', body: JSON.stringify(settings) }),

  // Runs
  startRun: (pipeline: PipelineDefinition) =>
    request<RunProgress>('/api/runs/start', {
      method: 'POST', body: JSON.stringify({ pipeline, persist_pipeline: true }),
    }),
  getRunStatus: (runId: string) =>
    request<RunProgress>(`/api/runs/${runId}/status`),
  getRun: (runId: string) =>
    request<RunResult>(`/api/runs/${runId}`),
  getRunPipeline: (runId: string) =>
    request<PipelineDefinition>(`/api/runs/${runId}/pipeline`),

  // Compare
  compareRuns: (baselineRunId: string, candidateRunId: string) =>
    request<RunComparison>('/api/compare', {
      method: 'POST', body: JSON.stringify({ baseline_run_id: baselineRunId, candidate_run_id: candidateRunId }),
    }),

  // Upload
  uploadRun: (runId: string) =>
    request<{ status: string; story_id: string }>(`/api/upload/${runId}`, { method: 'POST' }),
}
```

- [ ] **Step 3: Create store.ts with Zustand**

`python_director/admin_ui_v3/src/store.ts`:
```typescript
import { create } from 'zustand'
import { api } from './api'
import type {
  StudioBootstrap, PipelineDefinition, PipelineCatalogItem,
  RunSummary, RunProgress, PipelineBlock, BlockConfig,
} from './types'

interface ToastState {
  message: string
  isError: boolean
  visible: boolean
}

interface StudioStore {
  // Data
  studio: StudioBootstrap | null
  pipeline: PipelineDefinition | null
  pipelineCatalog: PipelineCatalogItem[]
  runs: RunSummary[]

  // UI
  selectedBlockId: string | null
  sidebarCollapsed: boolean
  toast: ToastState
  settingsOpen: boolean
  bootstrapError: string | null

  // Run monitoring
  activeRunId: string | null
  activeRunProgress: RunProgress | null
  pollInterval: number
  pollTimer: ReturnType<typeof setInterval> | null

  // Actions
  loadStudio: () => Promise<void>
  savePipeline: () => Promise<void>
  selectBlock: (id: string | null) => void
  updateBlock: (blockId: string, updates: Partial<PipelineBlock>) => void
  updateBlockConfig: (blockId: string, updates: Partial<BlockConfig>) => void
  moveBlock: (blockId: string, offset: number) => void
  duplicateBlock: (blockId: string) => void
  deleteBlock: (blockId: string) => void
  renameBlockId: (oldId: string, newId: string) => boolean
  addBlockFromTemplate: (block: PipelineBlock) => void
  showToast: (message: string, isError?: boolean) => void
  setSidebarCollapsed: (collapsed: boolean) => void
  setSettingsOpen: (open: boolean) => void

  // Run actions
  startRun: () => Promise<void>
  stopPolling: () => void
  loadRunProgress: (runId: string) => Promise<RunProgress>
}

export const useStore = create<StudioStore>((set, get) => ({
  studio: null,
  pipeline: null,
  pipelineCatalog: [],
  runs: [],
  selectedBlockId: null,
  sidebarCollapsed: false,
  toast: { message: '', isError: false, visible: false },
  settingsOpen: false,
  bootstrapError: null,
  activeRunId: null,
  activeRunProgress: null,
  pollInterval: 1500,
  pollTimer: null,

  loadStudio: async () => {
    try {
      const studio = await api.getStudio()
      set({
        studio,
        pipeline: structuredClone(studio.pipeline),
        pipelineCatalog: studio.pipeline_catalog,
        runs: studio.run_summaries,
        bootstrapError: null,
        selectedBlockId: get().selectedBlockId || studio.pipeline.blocks[0]?.id || null,
      })
    } catch (err) {
      set({ bootstrapError: (err as Error).message })
    }
  },

  savePipeline: async () => {
    const { pipeline } = get()
    if (!pipeline) return
    try {
      const saved = await api.savePipeline(pipeline)
      set({ pipeline: structuredClone(saved) })
      get().showToast('Pipeline saved')
    } catch (err) {
      get().showToast((err as Error).message, true)
    }
  },

  selectBlock: (id) => set({ selectedBlockId: id }),

  updateBlock: (blockId, updates) => {
    const { pipeline } = get()
    if (!pipeline) return
    const blocks = pipeline.blocks.map(b => b.id === blockId ? { ...b, ...updates } : b)
    set({ pipeline: { ...pipeline, blocks } })
  },

  updateBlockConfig: (blockId, updates) => {
    const { pipeline } = get()
    if (!pipeline) return
    const blocks = pipeline.blocks.map(b =>
      b.id === blockId ? { ...b, config: { ...b.config, ...updates } } : b
    )
    set({ pipeline: { ...pipeline, blocks } })
  },

  moveBlock: (blockId, offset) => {
    const { pipeline } = get()
    if (!pipeline) return
    const blocks = [...pipeline.blocks]
    const idx = blocks.findIndex(b => b.id === blockId)
    const target = idx + offset
    if (target < 0 || target >= blocks.length) return
    ;[blocks[idx], blocks[target]] = [blocks[target], blocks[idx]]
    set({ pipeline: { ...pipeline, blocks } })
  },

  duplicateBlock: (blockId) => {
    const { pipeline } = get()
    if (!pipeline) return
    const block = pipeline.blocks.find(b => b.id === blockId)
    if (!block) return
    const ids = new Set(pipeline.blocks.map(b => b.id))
    let newId = `${block.id}_copy`
    let i = 1
    while (ids.has(newId)) { newId = `${block.id}_copy_${++i}` }
    const dup: PipelineBlock = { ...structuredClone(block), id: newId, name: `${block.name} Copy` }
    const idx = pipeline.blocks.findIndex(b => b.id === blockId)
    const blocks = [...pipeline.blocks]
    blocks.splice(idx + 1, 0, dup)
    set({ pipeline: { ...pipeline, blocks }, selectedBlockId: newId })
  },

  deleteBlock: (blockId) => {
    const { pipeline, selectedBlockId } = get()
    if (!pipeline || pipeline.blocks.length <= 1) return
    const blocks = pipeline.blocks
      .filter(b => b.id !== blockId)
      .map(b => ({ ...b, input_blocks: b.input_blocks.filter(id => id !== blockId) }))
    const newSelected = selectedBlockId === blockId ? blocks[0]?.id || null : selectedBlockId
    set({ pipeline: { ...pipeline, blocks }, selectedBlockId: newSelected })
  },

  renameBlockId: (oldId, newId) => {
    const { pipeline } = get()
    if (!pipeline) return false
    if (pipeline.blocks.some(b => b.id === newId)) return false
    const blocks = pipeline.blocks.map(b => {
      const updated = b.id === oldId ? { ...b, id: newId } : b
      return {
        ...updated,
        input_blocks: updated.input_blocks.map(id => id === oldId ? newId : id),
        config: {
          ...updated.config,
          prompt_template: updated.config.prompt_template.replaceAll(`{{${oldId}}}`, `{{${newId}}}`),
        },
      }
    })
    set({ pipeline: { ...pipeline, blocks }, selectedBlockId: newId })
    return true
  },

  addBlockFromTemplate: (block) => {
    const { pipeline, selectedBlockId } = get()
    if (!pipeline) return
    const blocks = [...pipeline.blocks]
    const idx = blocks.findIndex(b => b.id === selectedBlockId)
    blocks.splice(idx >= 0 ? idx + 1 : blocks.length, 0, block)
    set({ pipeline: { ...pipeline, blocks }, selectedBlockId: block.id })
  },

  showToast: (message, isError = false) => {
    set({ toast: { message, isError, visible: true } })
    setTimeout(() => set(s => ({ toast: { ...s.toast, visible: false } })), 3000)
  },

  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
  setSettingsOpen: (open) => set({ settingsOpen: open }),

  startRun: async () => {
    const { pipeline, stopPolling } = get()
    if (!pipeline) return
    stopPolling()
    try {
      const initial = await api.startRun(pipeline)
      set({ activeRunId: initial.run_id, activeRunProgress: initial, pollInterval: 1500 })

      const timer = setInterval(async () => {
        const { activeRunId, pollInterval } = get()
        if (!activeRunId) return
        try {
          const progress = await api.getRunStatus(activeRunId)
          set({ activeRunProgress: progress, pollInterval: 1500 })
          if (progress.status === 'succeeded' || progress.status === 'failed') {
            get().stopPolling()
            get().showToast(
              progress.status === 'succeeded' ? 'Run complete' : 'Run failed',
              progress.status === 'failed',
            )
            get().loadStudio()
          }
        } catch {
          // Backoff on failure
          const newInterval = Math.min(pollInterval * 2, 10000)
          set({ pollInterval: newInterval })
        }
      }, 1500)
      set({ pollTimer: timer })
    } catch (err) {
      get().showToast((err as Error).message, true)
    }
  },

  stopPolling: () => {
    const { pollTimer } = get()
    if (pollTimer) clearInterval(pollTimer)
    set({ pollTimer: null })
  },

  loadRunProgress: async (runId: string) => {
    const progress = await api.getRunStatus(runId)
    set({ activeRunProgress: progress })
    return progress
  },
}))
```

- [ ] **Step 4: Verify the app still builds**

```bash
cd G:/code/gen-ai/in_real_time_v1/python_director/admin_ui_v3
npm run build
```
Expected: Build succeeds with no type errors.

- [ ] **Step 5: Commit**

```bash
git add python_director/admin_ui_v3/src/types.ts python_director/admin_ui_v3/src/api.ts python_director/admin_ui_v3/src/store.ts
git commit -m "feat: add TypeScript types, API client, and Zustand store"
```

---

## Task 5: Layout Shell — TopBar + Sidebar + Toast + Router

**Files:**
- Create: `python_director/admin_ui_v3/src/components/layout/TopBar.tsx`
- Create: `python_director/admin_ui_v3/src/components/layout/Sidebar.tsx`
- Create: `python_director/admin_ui_v3/src/components/layout/Toast.tsx`
- Create: `python_director/admin_ui_v3/src/components/shared/StatusDot.tsx`
- Create: `python_director/admin_ui_v3/src/components/shared/CollapsibleSection.tsx`
- Create: `python_director/admin_ui_v3/src/components/shared/Badge.tsx`
- Create: `python_director/admin_ui_v3/src/components/pipeline/BlockList.tsx`
- Create: `python_director/admin_ui_v3/src/components/pipeline/PipelineMeta.tsx`
- Create: `python_director/admin_ui_v3/src/components/pipeline/PipelineLibrary.tsx`
- Create: `python_director/admin_ui_v3/src/components/pipeline/TemplateRail.tsx`
- Create: `python_director/admin_ui_v3/src/components/shared/SettingsDialog.tsx`
- Create: `python_director/admin_ui_v3/src/views/EditorView.tsx` (placeholder)
- Create: `python_director/admin_ui_v3/src/views/RunsView.tsx` (placeholder)
- Create: `python_director/admin_ui_v3/src/views/CompareView.tsx` (placeholder)
- Modify: `python_director/admin_ui_v3/src/App.tsx`

- [ ] **Step 1: Create shared components (StatusDot, Badge, CollapsibleSection)**

These are small reusable primitives used throughout the app. Create all three files:

`StatusDot.tsx`: Renders a colored dot with optional pulse animation. Props: `status: BlockExecutionStatus | 'idle'`.

`Badge.tsx`: Renders a small pill/tag. Props: `variant: 'success' | 'error' | 'warning' | 'default'`, `children`.

`CollapsibleSection.tsx`: Renders a section with a clickable header that toggles content visibility. Props: `title: string`, `defaultOpen?: boolean`, `children`.

- [ ] **Step 2: Create Toast component**

`Toast.tsx`: Reads `toast` state from `useStore`. Renders a fixed-position notification bar at the bottom. Hides when `toast.visible` is false. Green border for success, red for error.

- [ ] **Step 3: Create TopBar component**

`TopBar.tsx`: Contains:
- Brand: "Director Studio" h1
- Nav links using `NavLink` from react-router-dom: `/editor`, `/runs`, `/compare`
- Right section: run-in-progress indicator (pulsing dot + text + mini progress, clickable to `/runs/{activeRunId}`), Settings button, Dry Run button
- Settings button calls `useStore.setSettingsOpen(true)`
- Dry Run button calls `useStore.startRun()`, disabled when `activeRunId` is set

- [ ] **Step 4: Create Sidebar component**

`Sidebar.tsx`: Collapsible sidebar containing:
- `PipelineMeta` — name, description, default model dropdowns
- `PipelineLibrary` — saved pipelines dropdown, load/save/delete buttons
- `BlockList` — block navigation items with status dots
- `TemplateRail` — add-block template buttons
- Action buttons: Save Design, Snapshot, Reset Default
- Collapse toggle button

- [ ] **Step 5: Create PipelineMeta component**

`PipelineMeta.tsx`: Inputs for pipeline name and description. Two dropdown selects for Gemini and OpenAI default models (options from `studio.provider_models`). Updates are applied to `pipeline` in the store.

- [ ] **Step 6: Create PipelineLibrary component**

`PipelineLibrary.tsx`: Select dropdown populated from `pipelineCatalog`. Load button calls `api.loadNamedPipeline`. "Save As Named" button prompts for name then calls `api.saveNamedPipeline`. Delete button calls `api.deleteNamedPipeline`.

- [ ] **Step 7: Create BlockList component**

`BlockList.tsx`: Renders the pipeline blocks as a vertical list. Each item shows: status dot, block name, type chip, provider badge. Clicking selects the block. Active block is highlighted with mint border. Disabled blocks are dimmed. Arrow separators between blocks.

- [ ] **Step 8: Create TemplateRail component**

`TemplateRail.tsx`: Renders available block templates from `studio.block_templates`. Each template is a small card with type chip, name, and "+ Add" button. Clicking "Add" creates a new block from the template and adds it to the pipeline.

- [ ] **Step 9: Create SettingsDialog component**

`SettingsDialog.tsx`: Modal dialog (using HTML `<dialog>` element). Fields: Gemini API Key (password), OpenAI API Key (password), Google Credentials Path (text). Status badges. Save/Cancel/Fresh Start buttons. Pre-fills from `studio.settings`.

- [ ] **Step 10: Create placeholder views**

Three placeholder view components:
- `EditorView.tsx`: Shows "Select a block to edit" placeholder
- `RunsView.tsx`: Shows "Runs view coming soon" placeholder
- `CompareView.tsx`: Shows "Compare view coming soon" placeholder

- [ ] **Step 11: Wire up App.tsx with router + layout**

Update `App.tsx` to use the layout shell:
```tsx
import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useStore } from './store'
import TopBar from './components/layout/TopBar'
import Sidebar from './components/layout/Sidebar'
import Toast from './components/layout/Toast'
import SettingsDialog from './components/shared/SettingsDialog'
import EditorView from './views/EditorView'
import RunsView from './views/RunsView'
import CompareView from './views/CompareView'

export default function App() {
  const loadStudio = useStore(s => s.loadStudio)
  const bootstrapError = useStore(s => s.bootstrapError)
  const studio = useStore(s => s.studio)

  useEffect(() => { loadStudio() }, [loadStudio])

  if (bootstrapError) {
    return (
      <div className="h-full flex items-center justify-center flex-col gap-4">
        <div className="bg-glow" />
        <p className="text-danger text-lg">Cannot reach Director Studio backend.</p>
        <p className="text-text-dim">Is the server running on port 8001?</p>
        <button onClick={loadStudio} className="px-4 py-2 bg-surface border border-border rounded-lg text-text hover:bg-surface-raised">Retry</button>
      </div>
    )
  }

  if (!studio) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="bg-glow" />
        <p className="text-text-dim">Loading...</p>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      <div className="bg-glow" />
      <TopBar />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/editor" element={<EditorView />} />
            <Route path="/runs/*" element={<RunsView />} />
            <Route path="/compare" element={<CompareView />} />
            <Route path="*" element={<Navigate to="/editor" replace />} />
          </Routes>
        </main>
      </div>
      <Toast />
      <SettingsDialog />
    </div>
  )
}
```

- [ ] **Step 12: Verify dev server renders the layout**

```bash
cd G:/code/gen-ai/in_real_time_v1/python_director/admin_ui_v3
npm run dev
```
With the FastAPI backend running on 8001, verify: TopBar renders with nav links, Sidebar renders with pipeline blocks, clicking nav links switches views.

- [ ] **Step 13: Commit**

```bash
git add python_director/admin_ui_v3/src/
git commit -m "feat: add layout shell with TopBar, Sidebar, Toast, Router, and Settings"
```

---

## Task 6: Pipeline Editor View — BlockInspector

**Files:**
- Create: `python_director/admin_ui_v3/src/components/pipeline/BlockInspector.tsx`
- Modify: `python_director/admin_ui_v3/src/views/EditorView.tsx`

- [ ] **Step 1: Create BlockInspector component**

`BlockInspector.tsx`: The main editor for a selected block. Uses collapsible sections:
- **Identity**: Block ID input (with rename logic on blur), Name input, Type badge (read-only)
- **Execution Config**: Enabled toggle, Provider select, Model Source select (default/custom), Model input (datalist from provider_models), Temperature number input, Schema select
- **System Instruction**: Monospace textarea
- **Prompt Template**: Larger monospace textarea
- **Dependencies**: Checkbox list of other blocks
- **Actions**: Move Up/Down, Duplicate, Delete buttons

All changes update the store in real-time via `updateBlock`, `updateBlockConfig`, `renameBlockId`, etc.

- [ ] **Step 2: Update EditorView to render BlockInspector or welcome state**

`EditorView.tsx`: If `selectedBlockId` is set and block exists, render `<BlockInspector />`. Otherwise render the welcome state: pipeline stats summary (block count, providers breakdown) and dependency listing.

- [ ] **Step 3: Verify editor works end-to-end**

Start both FastAPI backend and Vite dev server. In the browser:
1. Select a block → inspector loads with correct values
2. Edit block name → sidebar updates in real-time
3. Change provider → model options update
4. Edit prompt template → changes persist
5. Click "Save Design" in sidebar → pipeline saves to backend
6. Click "Duplicate" → new block appears

- [ ] **Step 4: Commit**

```bash
git add python_director/admin_ui_v3/src/
git commit -m "feat: add BlockInspector and EditorView for pipeline editing"
```

---

## Task 7: Runs View — RunList + RunDetail + BlockAccordion

**Files:**
- Create: `python_director/admin_ui_v3/src/components/runs/RunList.tsx`
- Create: `python_director/admin_ui_v3/src/components/runs/RunDetail.tsx`
- Create: `python_director/admin_ui_v3/src/components/runs/BlockAccordion.tsx`
- Modify: `python_director/admin_ui_v3/src/views/RunsView.tsx`

- [ ] **Step 1: Create RunList component**

`RunList.tsx`: Renders a vertical list of run summary cards. Active runs (from `activeRunProgress`) shown at top with pulsing indicator and progress percentage. Historical runs from `runs` array below. Each card shows: timestamp (formatted), pipeline name, status badge, quality proxy score, word count, "Inspect" button.

- [ ] **Step 2: Create BlockAccordion component**

`BlockAccordion.tsx`: Renders a vertical accordion of blocks for a given run. Props: `blockSequence: string[]`, `blockTraces: Record<string, BlockTrace>`.

Each block header: name, type badge, provider badge, status dot, elapsed time.

Expanding reveals three sections:
- **Input**: Resolved prompt as formatted text. Resolved inputs as labeled cards.
- **Output**: Passed to `ContentRenderer` (Task 8). If output is null, show "No output yet."
- **Error** (if failed): Red banner with error message + collapsible traceback

For running blocks: show indeterminate spinner. For pending blocks: grayed out header, not expandable.

- [ ] **Step 3: Create RunDetail component**

`RunDetail.tsx`: Container for a selected run. Shows run header (title, status, timestamp, upload button for succeeded runs). Three sub-tabs: Blocks, Timeline, Experience.

Uses React Router nested routes:
- `/runs/:runId/blocks` → `<BlockAccordion />`
- `/runs/:runId/timeline` → placeholder (Task 9)
- `/runs/:runId/experience` → placeholder (Task 10)

Default redirect to `/runs/:runId/blocks`.

- [ ] **Step 4: Update RunsView with split layout**

`RunsView.tsx`: Split layout — left panel is `<RunList />`, main area is `<RunDetail />` when a run is selected, empty state when not. Uses nested routes: `/runs` shows list + empty state, `/runs/:runId/*` shows list + detail.

- [ ] **Step 5: Verify runs view with a real dry run**

1. Start backend + dev server
2. Click "Dry Run" in TopBar → run starts
3. Navigate to Runs view → active run appears with pulsing indicator
4. Click the run → BlockAccordion shows blocks with live status updates
5. Completed blocks are expandable → shows I/O
6. After run completes → run moves to history section

- [ ] **Step 6: Commit**

```bash
git add python_director/admin_ui_v3/src/
git commit -m "feat: add Runs view with RunList, RunDetail, and BlockAccordion"
```

---

## Task 8: Content Formatting Components

**Files:**
- Create: `python_director/admin_ui_v3/src/components/formatting/ContentRenderer.tsx`
- Create: `python_director/admin_ui_v3/src/components/formatting/StoryPlanCard.tsx`
- Create: `python_director/admin_ui_v3/src/components/formatting/CritiqueCard.tsx`
- Create: `python_director/admin_ui_v3/src/components/formatting/JournalCard.tsx`
- Create: `python_director/admin_ui_v3/src/components/formatting/ChatBubble.tsx`
- Create: `python_director/admin_ui_v3/src/components/formatting/EmailCard.tsx`
- Create: `python_director/admin_ui_v3/src/components/formatting/ReceiptCard.tsx`
- Create: `python_director/admin_ui_v3/src/components/formatting/VoiceNoteCard.tsx`
- Create: `python_director/admin_ui_v3/src/components/formatting/RawJsonViewer.tsx`

- [ ] **Step 1: Create RawJsonViewer**

`RawJsonViewer.tsx`: Renders JSON data in a collapsible `<pre>` block with monospace font. Default collapsed. Props: `data: unknown`, `label?: string`.

- [ ] **Step 2: Create ContentRenderer (dispatcher)**

`ContentRenderer.tsx`: Props: `output: unknown`, `schemaName: string | null`. Dispatches rendering based on `schemaName`:
- `"StoryPlan"` → `<StoryPlanCard />`
- `"BrainstormCritique"` or `"StoryCritique"` → `<CritiqueCard />`
- `"SceneList"` → Scene timeline (inline, simple)
- `"ContinuityAudit"` → Audit card (inline, simple)
- `"DropPlan"` → Drop plan card (inline, simple)
- `"StoryGenerated"` → inline experience preview using artifact cards
- `null` + string output → formatted prose
- `null` + object output → `<RawJsonViewer />`

Every card includes a "View Raw" toggle at the bottom.

- [ ] **Step 3: Create StoryPlanCard**

`StoryPlanCard.tsx`: Renders a `StoryPlan` object as structured sections: title heading, character cards (name, background, arc summary), core conflict paragraph, background lore, the twist, act summaries (1/2/3).

- [ ] **Step 4: Create CritiqueCard**

`CritiqueCard.tsx`: Renders critique objects (BrainstormCritique or StoryCritique). Strengths as green bullets, weaknesses/risks as red bullets, actionable items as amber bullets. Handles both schema shapes.

- [ ] **Step 5: Create artifact cards (Journal, Chat, Email, Receipt, VoiceNote)**

`JournalCard.tsx`: Paper-note aesthetic. Shows title + body text with paragraph formatting.

`ChatBubble.tsx`: Chat bubble layout. Protagonist messages aligned right (mint-tinted), others aligned left. Shows sender name above bubble.

`EmailCard.tsx`: Email card with From, Subject header, body text below.

`ReceiptCard.tsx`: Transaction card showing merchant name, amount (formatted as currency), description.

`VoiceNoteCard.tsx`: Audio-note style card with speaker label and transcript text.

- [ ] **Step 6: Verify formatting in BlockAccordion**

Run a dry run, inspect block outputs in the Runs view. Verify that structured outputs render as formatted cards (not raw JSON). Toggle "View Raw" to see JSON.

- [ ] **Step 7: Commit**

```bash
git add python_director/admin_ui_v3/src/components/formatting/
git commit -m "feat: add content formatting components for non-technical output rendering"
```

---

## Task 9: Timeline View

**Files:**
- Create: `python_director/admin_ui_v3/src/components/runs/TimelineView.tsx`
- Modify: `python_director/admin_ui_v3/src/components/runs/RunDetail.tsx` (wire up route)

- [ ] **Step 1: Create TimelineView component**

`TimelineView.tsx`: Props: `timeline: RunTimelineEntry[]`. Renders a vertical timeline:
- Left column: time marker (Day X, HH:MM AM/PM)
- Center: timeline dot (color-coded by event_type)
- Right: content card with title, type badge, content preview (first ~100 chars of relevant text field)
- Clicking expands to show full content in the appropriate artifact card (JournalCard, ChatBubble, etc.)
- Vertical connecting line between entries

Color coding by type:
- journal: mint
- chat: blue (#60a5fa)
- email: amber
- receipt: purple (#a78bfa)
- voice_note: pink (#f472b6)

Empty state: "No narrative events yet."

- [ ] **Step 2: Wire into RunDetail routes**

Update `RunDetail.tsx` to render `<TimelineView />` for the `/runs/:runId/timeline` sub-tab.

- [ ] **Step 3: Verify timeline renders for a completed run**

Navigate to Runs → select a completed run → click Timeline tab. Verify entries appear chronologically with correct types and content.

- [ ] **Step 4: Commit**

```bash
git add python_director/admin_ui_v3/src/components/runs/TimelineView.tsx python_director/admin_ui_v3/src/components/runs/RunDetail.tsx
git commit -m "feat: add Timeline view for story artifact visualization"
```

---

## Task 10: Experience Preview ("Uber-View")

**Files:**
- Create: `python_director/admin_ui_v3/src/components/runs/ExperiencePreview.tsx`
- Modify: `python_director/admin_ui_v3/src/components/runs/RunDetail.tsx` (wire up route)

- [ ] **Step 1: Create ExperiencePreview component**

`ExperiencePreview.tsx`: Props: `timeline: RunTimelineEntry[]`. Groups timeline entries by day and time. Renders:

```
── Day 1 ──────────────────────
  09:00 AM
    [Notification card: "New journal entry"]
    [JournalCard with full content]

  10:30 AM
    [Notification card: "New chat message"]
    [ChatBubble with full content]
```

For each time group:
- Show a small notification banner indicating the artifact type
- Render the full artifact card using the formatting components
- Day separators as horizontal rules with day label

Empty state: "No experience data. Run a pipeline with a generator block first."

- [ ] **Step 2: Wire into RunDetail routes**

Update `RunDetail.tsx` to render `<ExperiencePreview />` for the `/runs/:runId/experience` sub-tab.

- [ ] **Step 3: Verify experience preview**

Navigate to Runs → select a completed run → click Experience tab. Verify the simulated reader experience renders with all artifact types in chronological order.

- [ ] **Step 4: Commit**

```bash
git add python_director/admin_ui_v3/src/components/runs/ExperiencePreview.tsx python_director/admin_ui_v3/src/components/runs/RunDetail.tsx
git commit -m "feat: add Experience Preview (uber-view) for simulated reader experience"
```

---

## Task 11: Compare View

**Files:**
- Create: `python_director/admin_ui_v3/src/components/compare/MetricDeltas.tsx`
- Create: `python_director/admin_ui_v3/src/components/compare/SideBySide.tsx`
- Modify: `python_director/admin_ui_v3/src/views/CompareView.tsx`

- [ ] **Step 1: Create MetricDeltas component**

`MetricDeltas.tsx`: Props: `metrics: MetricDelta[]`. Renders a grid of delta cards. Each card: label, candidate value (large), "vs {baseline} ({delta})" with green for positive, red for negative.

- [ ] **Step 2: Create SideBySide component**

`SideBySide.tsx`: Props: `baselineTimeline: RunTimelineEntry[]`, `candidateTimeline: RunTimelineEntry[]`, `baselineTitle`, `candidateTitle`. Renders two ExperiencePreview components side-by-side with synchronized scrolling (both panels scroll together using a shared scroll handler).

- [ ] **Step 3: Update CompareView**

`CompareView.tsx`: Two run selector dropdowns (populated from `runs`). "Compare" button calls `api.compareRuns()`. On result:
- `<MetricDeltas />` with the metrics
- Quality notes as bullet list
- `<SideBySide />` with the two outputs parsed into timelines

Uses `derive_story_timeline` logic client-side to parse `baseline_output` and `candidate_output` into `RunTimelineEntry[]` arrays for the SideBySide component. (Duplicate the time-offset-to-clock logic in a utility function.)

- [ ] **Step 4: Verify comparison**

Run two dry runs. Navigate to Compare → select both runs → click Compare. Verify metrics, quality notes, and side-by-side preview all render.

- [ ] **Step 5: Commit**

```bash
git add python_director/admin_ui_v3/src/components/compare/ python_director/admin_ui_v3/src/views/CompareView.tsx
git commit -m "feat: add Compare view with metric deltas and side-by-side experience preview"
```

---

## Task 12: Build Scripts + .gitignore + Final Integration

**Files:**
- Modify: `script/director-install.ps1`
- Modify: `script/director-admin.ps1`
- Create: `script/director-ui-dev.ps1`
- Create: `script/director-ui-dev.cmd`
- Modify: `.gitignore`

- [ ] **Step 1: Update director-install.ps1**

Add Node.js check and UI build after the Python install section:
```powershell
# After pip install section, add:
$adminUiDir = Join-Path $repoRoot "python_director\admin_ui_v3"
if (Test-Path (Join-Path $adminUiDir "package.json")) {
    $nodeVersion = $null
    try { $nodeVersion = & node --version 2>&1 } catch {}
    if (-not $nodeVersion) {
        Write-Host "Node.js not found. Install it from https://nodejs.org/ to build the Admin UI." -ForegroundColor Yellow
    } else {
        Write-Host "Node.js found: $nodeVersion" -ForegroundColor Gray
        Write-Host "Installing Admin UI dependencies..." -ForegroundColor Cyan
        Push-Location $adminUiDir
        try {
            & npm install
            Write-Host "Building Admin UI..." -ForegroundColor Cyan
            & npm run build
            Write-Host "Admin UI built successfully!" -ForegroundColor Green
        } finally {
            Pop-Location
        }
    }
}
```

- [ ] **Step 2: Update director-admin.ps1**

Add auto-build check before starting uvicorn:
```powershell
# Before the uvicorn start, add:
$adminUiDist = Join-Path $repoRoot "python_director\admin_ui_v3\dist"
$adminUiPkg = Join-Path $repoRoot "python_director\admin_ui_v3\package.json"
if ((Test-Path $adminUiPkg) -and -not (Test-Path $adminUiDist)) {
    Write-Host "Admin UI not built. Building..." -ForegroundColor Yellow
    Push-Location (Join-Path $repoRoot "python_director\admin_ui_v3")
    try {
        & npm install
        & npm run build
    } finally {
        Pop-Location
    }
}
```

- [ ] **Step 3: Create director-ui-dev.ps1**

```powershell
$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$adminUiDir = Join-Path $repoRoot "python_director\admin_ui_v3"

if (-not (Test-Path (Join-Path $adminUiDir "node_modules"))) {
    Write-Host "Installing dependencies..." -ForegroundColor Cyan
    Push-Location $adminUiDir
    & npm install
    Pop-Location
}

Write-Host "Starting Vite dev server on http://localhost:5173" -ForegroundColor Cyan
Write-Host "API proxy -> http://localhost:8001" -ForegroundColor Gray
Write-Host "Make sure the FastAPI backend is running (script/director-admin)" -ForegroundColor Yellow
Push-Location $adminUiDir
try {
    & npx vite
} finally {
    Pop-Location
}
```

- [ ] **Step 4: Create director-ui-dev.cmd**

```cmd
@echo off
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0director-ui-dev.ps1" %*
```

- [ ] **Step 5: Verify .gitignore has the right entries**

Ensure `.gitignore` includes:
```
python_director/admin_ui_v3/node_modules/
python_director/admin_ui_v3/dist/
```

- [ ] **Step 6: Full integration test**

1. Run `script/director-install.cmd` → Python + Node deps install, UI builds
2. Run `script/director-admin.cmd` → FastAPI starts, serves React UI at http://localhost:8001
3. Navigate to http://localhost:8001 → React app loads
4. Edit pipeline → Save → Reload → changes persist
5. Start a dry run → watch live progress
6. Inspect completed run → blocks, timeline, experience preview
7. Compare two runs → metrics + side-by-side

- [ ] **Step 7: Build production and verify**

```bash
cd G:/code/gen-ai/in_real_time_v1/python_director/admin_ui_v3
npm run build
```
Then visit http://localhost:8001 (served by FastAPI). Verify all views work identically to dev mode.

- [ ] **Step 8: Commit**

```bash
git add script/ .gitignore
git commit -m "feat: update build scripts for React UI, add director-ui-dev script"
```

---

## Task 13: Final Cleanup

**Files:**
- Modify: `CLAUDE.md` (update commands)

- [ ] **Step 1: Update CLAUDE.md with new commands**

Add the new `director-ui-dev` script and note the `/api/` prefix change. Update the admin UI section to reference React/Vite.

- [ ] **Step 2: Verify all tests pass**

```bash
cd G:/code/gen-ai/in_real_time_v1
python -m pytest python_director/test_director.py -v
```

- [ ] **Step 3: Final commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md for Director Studio v3"
```
