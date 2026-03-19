# Python Director (Admin + Story Pipeline)

`python_director` is the backend-first admin interface for instrumenting storylines that later appear in the mobile app.

It includes:
- A configurable pipeline with block-level prompts, provider/model choice, and dependencies.
- A dry-run execution engine that stores block artifacts and prompt traces in the filesystem.
- A simple browser admin UI for non-technical operators.
- Final artifact comparison between two runs for quality iteration.
- Built-in `continuity_audit` and `drop_director` stages to improve release quality and pacing strategy.

## Run the Admin API + Web UI

From repo root:

```bash
python -m uvicorn python_director.api:app --host 0.0.0.0 --port 8000 --reload
```

Open:
- [http://localhost:8000](http://localhost:8000)
- [http://localhost:8000/admin](http://localhost:8000/admin)

### Helper Scripts (Windows-friendly)

From repo root:

```bash
script\director-install.cmd
script\director-admin.cmd
script\director-dry-run.cmd
script\director-tests.cmd
```

PowerShell variants are also available:

```bash
script/director-install.ps1
script/director-admin.ps1
script/director-dry-run.ps1
script/director-tests.ps1
```

## Workflow in the Admin UI

1. Configure keys in **Settings**:
   - Gemini API key
   - OpenAI API key
2. Edit the pipeline visually:
   - Reorder or disable blocks
   - Change prompts and dependencies
   - Switch each block between Gemini/OpenAI
3. Run **Dry Run**:
   - Stores run artifacts in `python_director/temp_artifacts/<run_id>/`
4. Compare runs:
   - Side-by-side final artifacts
   - Metric deltas including `quality_proxy_score`
5. Snapshot prompts:
   - Saved in `python_director/snapshots/`

## Storage Layout

- `pipeline.json`: current working pipeline.
- `settings.local.json`: local secrets/settings (ignored by git).
- `temp_artifacts/<run_id>/`: block outputs, prompts, run manifest, pipeline snapshot.
- `snapshots/`: manually captured pipeline snapshots from UI.

## API Surface (Core)

- `GET /studio` - bootstrap payload for admin UI.
- `PUT /pipeline` - save pipeline.
- `POST /pipeline/reset` - reset to default pipeline.
- `POST /pipeline/snapshot` - write snapshot to filesystem.
- `PUT /settings` - save provider keys.
- `POST /run` - execute pipeline dry run.
- `GET /runs/{run_id}` - fetch run details with block traces.
- `POST /compare` - compare two run outputs.
- `POST /upload/{run_id}` - upload final output to Firestore.
