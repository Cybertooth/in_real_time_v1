# Director Studio UI Guide

This guide explains how to use the backend admin interface for story pipeline iteration.

## 1. Start the UI

From repo root:

```bash
script\director-admin.cmd
```

Open:
- `http://localhost:8000`
- `http://localhost:8000/admin`

## 2. Configure Providers

1. Click **Settings** (top-right).
2. Add:
   - Gemini API key
   - OpenAI API key
   - Google credentials path (optional, only for upload)
3. Click **Save**.

Settings are stored in `python_director/settings.local.json`.
They are also cached in browser `localStorage`, so keys are remembered on the same machine/browser profile.

Security note:
- Browser `localStorage` stores values as plain text for that profile.
- Use a trusted machine/profile for admin operations.

## 3. Edit the Pipeline (No Horizontal Scroll)

The pipeline canvas is now vertical. Each block is shown in sequence with downward arrows.

1. Click a block card, or click **`✎ Edit`** on a block.
2. Update any fields in **Block Inspector**:
   - block id/name
   - provider/model
   - model source: pipeline default or block override
   - temperature
   - schema
   - system instruction
   - prompt template
   - dependencies
3. Use **Move Up / Move Down** to reorder.
4. Use **Duplicate** or **Delete** as needed.
5. Use the template rail to add new blocks.

Pipeline-level defaults:
- In the pipeline header, set the default Gemini and OpenAI model once.
- For each block, choose whether it should inherit the pipeline default or use its own override model.

## 4. Save and Snapshot

- **Save Pipeline** persists current config to `python_director/pipeline.json`.
- **Save As Named** saves a reusable version in `python_director/pipelines/<name>.json`.
- **Load** (from Saved Pipelines dropdown) activates a named pipeline for editing and dry-runs.
- **Snapshot Prompts** writes a timestamped snapshot under `python_director/snapshots/`.

## 5. Dry Run and Inspect Artifacts

1. Click **Dry Run**.
2. Open a run from **Run Lab**.
3. Inspect:
   - final output artifact
   - per-block traces (resolved prompt + output)
   - saved files for that run

Artifacts are written to:
- `python_director/temp_artifacts/<run_id>/`

## 6. Compare Two Runs

1. Select a baseline and candidate run.
2. Click **Compare**.
3. Review:
   - quality notes
   - metric deltas
   - side-by-side final artifacts

## 7. Reset to Default

Use **Reset Default** if experimentation drifts too far and you want the canonical pipeline back.

For a full clean slate (pipeline + runs + snapshots + named pipelines + logs), run:

```bash
script\director-fresh-start.cmd
```

This recreates the active `pipeline.json` from the current default pipeline definition, including the brainstorm council blocks.

If you also want to wipe saved provider keys from backend file:

```bash
script\director-fresh-start.cmd -ClearSettings
```

Browser-side cache reset:
- Open **Settings** and click **Fresh Start** to clear localStorage keys and reset the active pipeline.

## 8. Troubleshooting

- If UI actions fail due missing package:
  - run `script\director-install.cmd`
- If a provider key is missing:
  - open **Settings** and save keys again
- If run fails on schema mismatch:
  - inspect block prompt + schema pair in Block Inspector and align fields

## 9. Logging and Debugging

- Backend logs:
  - Set `DIRECTOR_LOG_LEVEL=DEBUG` before starting server for verbose traces.
  - Logs include API requests, pipeline load/migration, block execution, and provider call boundaries.
  - Rotating log file path: `python_director/logs/director.log` (overridable via `DIRECTOR_LOG_FILE`).
- UI logs:
  - Use **UI Activity Log** panel in the right column.
  - It captures user actions (block edit/move/duplicate/delete), request start/success/failure, and warnings/errors.
  - Logs are also mirrored to browser devtools console.
  - Use **Copy** to copy all log lines; logs are cached in localStorage across page reloads.
