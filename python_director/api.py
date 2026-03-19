from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

if __package__:
    from .defaults import get_default_pipeline
    from .logic import PipelineRunner, compare_final_outputs, upload_to_firestore
    from .models import (
        AppSettings,
        CompareRunsRequest,
        PipelineDefinition,
        PipelineSnapshotRequest,
        RunPipelineRequest,
    )
    from .storage import (
        BASE_DIR,
        RUNS_DIR,
        build_studio_bootstrap,
        get_settings_payload,
        load_pipeline,
        load_run_result,
        load_settings,
        save_pipeline,
        save_settings,
        snapshot_pipeline,
    )
else:
    from defaults import get_default_pipeline
    from logic import PipelineRunner, compare_final_outputs, upload_to_firestore
    from models import (
        AppSettings,
        CompareRunsRequest,
        PipelineDefinition,
        PipelineSnapshotRequest,
        RunPipelineRequest,
    )
    from storage import (
        BASE_DIR,
        RUNS_DIR,
        build_studio_bootstrap,
        get_settings_payload,
        load_pipeline,
        load_run_result,
        load_settings,
        save_pipeline,
        save_settings,
        snapshot_pipeline,
    )

app = FastAPI(title="Python Director Studio API")
ADMIN_UI_DIR = BASE_DIR / "admin_ui"

if ADMIN_UI_DIR.exists():
    app.mount("/admin-static", StaticFiles(directory=ADMIN_UI_DIR), name="admin-static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def admin_home():
    index_file = ADMIN_UI_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Admin UI is missing.")
    return FileResponse(index_file)


@app.get("/admin")
async def admin_alias():
    return await admin_home()


@app.get("/studio")
async def get_studio():
    return build_studio_bootstrap()


@app.get("/pipeline")
async def get_pipeline():
    return load_pipeline()


@app.put("/pipeline")
async def update_pipeline(pipeline: PipelineDefinition):
    return save_pipeline(pipeline)


@app.post("/pipeline/reset")
async def reset_pipeline_to_default():
    return save_pipeline(get_default_pipeline())


@app.post("/pipeline/snapshot")
async def create_pipeline_snapshot(request: PipelineSnapshotRequest):
    path = snapshot_pipeline(request.pipeline, request.label)
    return {"status": "ok", "path": str(path)}


@app.get("/settings")
async def get_settings():
    return get_settings_payload()


@app.put("/settings")
async def update_settings(settings: AppSettings):
    save_settings(settings)
    return get_settings_payload()


@app.get("/runs")
async def list_runs():
    return build_studio_bootstrap().run_summaries


@app.get("/runs/{run_id}")
async def get_run(run_id: str):
    try:
        return load_run_result(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/runs/{run_id}/artifacts/{artifact_name}")
async def get_run_artifact(run_id: str, artifact_name: str):
    if Path(artifact_name).name != artifact_name:
        raise HTTPException(status_code=400, detail="Invalid artifact name.")
    path = RUNS_DIR / run_id / artifact_name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"Artifact '{artifact_name}' not found for run '{run_id}'.")

    media_type = "application/json" if path.suffix.lower() == ".json" else "text/plain"
    return FileResponse(path, media_type=media_type)


@app.post("/run")
async def run_pipeline(request: RunPipelineRequest = RunPipelineRequest()):
    pipeline = request.pipeline or load_pipeline()
    if request.persist_pipeline:
        pipeline = save_pipeline(pipeline)

    settings = load_settings()
    runner = PipelineRunner(settings)
    try:
        return runner.run_pipeline(pipeline, run_id=request.run_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/compare")
async def compare_runs(request: CompareRunsRequest):
    try:
        baseline = load_run_result(request.baseline_run_id)
        candidate = load_run_result(request.candidate_run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return compare_final_outputs(request, baseline, candidate)


@app.post("/upload/{run_id}")
async def upload_run(run_id: str):
    try:
        run_result = load_run_result(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if not isinstance(run_result.final_output, dict):
        raise HTTPException(status_code=400, detail="Selected run has no structured final artifact.")

    settings = load_settings()
    cred_path = settings.google_application_credentials
    if not cred_path:
        raise HTTPException(
            status_code=400,
            detail="Google credentials path is missing. Add it in Settings before uploading.",
        )

    try:
        story_id = upload_to_firestore(run_result.final_output, cred_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"status": "ok", "story_id": story_id}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("python_director.api:app", host="0.0.0.0", port=8000, reload=False)
