# Director Studio Run Monitor Upgrade

## Summary
Fix the immediate run-detail UI bug, then upgrade the admin UI into a single-page workflow with:
- a closable Block Inspector
- persistent historical dry-run browsing
- a dedicated Run Center for block-by-block inspection
- live dry-run progress via polling, with per-block status, inputs, outputs, and failure reasons

This plan keeps the current backend/admin architecture, leaves the user-facing Flutter app untouched, and preserves existing completed-run storage on disk.

## Key Changes

### 1. Immediate bug fix and UI structure
- Fix the current run-detail crash by replacing `state.runStatusLabel` / `state.qualityScoreLabel` writes with the DOM refs from `els`.
- Make the Block Inspector closed by default unless explicitly opened from a block card.
- Add an explicit close control to the inspector and keep the selected block state separate from inspector visibility.
- Keep the admin as a single-page layout:
  - left: pipeline canvas
  - middle: collapsible inspector drawer
  - right: Run Center
- Rework the right panel from “Run Lab” into a Run Center with 3 sections:
  - `Active Run`
  - `Run History`
  - `Compare`
- Keep compare in the same page, but visually subordinate it to the new run workflow.

### 2. Historical runs and run-detail screen
- Keep using filesystem-backed historical runs from `python_director/temp_artifacts/<run_id>/`.
- Expand the Run Center so selecting any prior run shows a structured per-block execution view instead of only raw collapsible JSON.
- For each block in a completed or failed run, show:
  - block name / id / type
  - status
  - provider / effective model / duration
  - resolved prompt
  - derived inputs (from dependent block outputs)
  - output
  - error, if failed
- Keep raw JSON available in collapsible sections, but default the screen to a more readable step-by-step presentation.
- Historical run list should load from existing run summaries on page load and remain sorted newest first.

### 3. Backend run-state model for live progress
- Preserve the existing final `RunResult` concept, but extend run persistence with an in-progress execution state.
- Add a new persisted live-state artifact per run, stored in the run folder, for example:
  - `run_progress.json`
- Introduce explicit run/block execution state types:
  - run status: `queued`, `running`, `succeeded`, `failed`
  - block status: `pending`, `running`, `succeeded`, `failed`, `skipped`
- Extend runtime state to capture:
  - run id
  - started / completed timestamps
  - current block id
  - per-block status entries
  - per-block input snapshot
  - per-block output snapshot
  - per-block error message / traceback summary
  - final error summary for failed runs
- Keep `run_result.json` for completed/finalized runs, but allow failed runs to persist partial execution detail so they still appear in history and can be inspected.
- Extend `RunSummary` / `RunResult` to include terminal status and optional error text so failed runs are first-class in the UI.

### 4. Backend API changes for live runs
- Keep the current `POST /run` endpoint for backward compatibility with existing scripts/CLI behavior.
- Add a new async-start endpoint for the admin UI, e.g. `POST /runs/start`, that:
  - creates a run id
  - writes initial progress state
  - launches execution in a background thread/task
  - immediately returns the initial run-progress payload
- Add a polling endpoint, e.g. `GET /runs/{run_id}/status`, that returns the current live progress snapshot.
- Keep `GET /runs/{run_id}` as the full finalized/detail endpoint, but make it work for both succeeded and failed runs.
- Update `PipelineRunner` to emit lifecycle callbacks before block start, on block success, and on block failure.
- On block failure:
  - persist the failing block’s error
  - mark the run as failed
  - preserve prior successful block outputs/traces
  - stop execution cleanly

### 5. Live dry-run UX behavior
- Change the UI’s dry-run action to use the new async start endpoint.
- As soon as a run starts:
  - switch the Run Center to `Active Run`
  - start polling every 1 second
  - visually update the pipeline canvas in place
- Pipeline canvas status colors:
  - pending: default
  - running: yellow
  - succeeded: green
  - failed: red
  - skipped/disabled: muted gray
- While a run is in progress, the Active Run screen should stream block progression:
  - current block highlighted
  - completed blocks filled/marked success
  - failed block marked with visible reason
- For a running block, show:
  - its resolved prompt
  - resolved inputs known at that moment
  - output area as “waiting” until block completion
- For completed blocks, show input/output immediately as polling updates arrive.
- On terminal state:
  - stop polling
  - move the run into Run History
  - keep it selected in Active Run for inspection

## Public Interfaces / Data Shape Changes
- `PipelineDefinition`
  - no new product behavior here beyond existing pipeline defaults
- `RunSummary`
  - add `status`
  - add optional `error_message`
- `RunResult`
  - add terminal `status`
  - add optional `error_message`
  - include block-level failure detail for failed runs
- New live-run payload type
  - run metadata
  - current block id
  - overall status
  - ordered block progress entries with prompt/input/output/error fields
- New API endpoints
  - `POST /runs/start`
  - `GET /runs/{run_id}/status`

## Test Plan
- UI bug regression:
  - selecting a historical run no longer throws when updating run status labels
- Inspector behavior:
  - inspector is hidden by default
  - clicking edit opens it
  - close control hides it without losing selected block
- Historical runs:
  - prior successful runs appear after reload
  - failed runs also appear with failure status
- Live run progression:
  - async run start returns immediately with run id
  - polling endpoint advances block states in order
  - running block is highlighted, then transitions to success/failure
- Failure handling:
  - if a block raises, run status becomes `failed`
  - failed block error is visible in history/detail view
  - prior successful blocks still show their inputs/outputs
- Persistence:
  - `run_progress.json` exists during execution
  - final run data remains inspectable after refresh
- Backward compatibility:
  - existing synchronous `POST /run` still works for non-UI callers

## Assumptions and Defaults
- Chosen UI shape: single-page admin with a collapsible inspector and expanded Run Center.
- Chosen live transport: polling, not WebSockets/SSE.
- History retention: keep all filesystem runs by default; no auto-pruning in this change.
- Compare stays in the admin page and continues to operate on completed runs only.
- Flutter frontend is out of scope.
