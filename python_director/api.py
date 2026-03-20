from __future__ import annotations

import threading
from pathlib import Path
from time import perf_counter

from fastapi import APIRouter, BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

if __package__:
    from .defaults import get_default_pipeline
    from .logic import PipelineRunner, compare_final_outputs, upload_to_firestore
    from .log_utils import get_logger
    from .models import (
        AppSettings,
        CompareRunsRequest,
        NamedPipelineLoadRequest,
        NamedPipelineSaveRequest,
        PipelineDefinition,
        PipelineSnapshotRequest,
        RunPipelineRequest,
        RunProgress,
        RunStatus,
    )
    from .storage import (
        BASE_DIR,
        RUNS_DIR,
        build_studio_bootstrap,
        delete_named_pipeline,
        get_settings_payload,
        list_named_pipelines,
        load_named_pipeline,
        load_pipeline,
        load_run_result,
        load_settings,
        save_named_pipeline,
        save_pipeline,
        save_settings,
        snapshot_pipeline,
    )
else:
    from defaults import get_default_pipeline
    from logic import PipelineRunner, compare_final_outputs, upload_to_firestore
    from log_utils import get_logger
    from models import (
        AppSettings,
        CompareRunsRequest,
        NamedPipelineLoadRequest,
        NamedPipelineSaveRequest,
        PipelineDefinition,
        PipelineSnapshotRequest,
        RunPipelineRequest,
        RunProgress,
        RunStatus,
    )
    from storage import (
        BASE_DIR,
        RUNS_DIR,
        build_studio_bootstrap,
        delete_named_pipeline,
        get_settings_payload,
        list_named_pipelines,
        load_named_pipeline,
        load_pipeline,
        load_run_result,
        load_settings,
        save_named_pipeline,
        save_pipeline,
        save_settings,
        snapshot_pipeline,
    )

app = FastAPI(title="Python Director Studio API")
logger = get_logger("python_director.api")
ADMIN_UI_DIR = BASE_DIR / "admin_ui"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for active run progress
active_runs: dict[str, RunProgress] = {}


@app.middleware("http")
async def log_requests(request: Request, call_next):
    started = perf_counter()
    logger.info("HTTP start method=%s path=%s", request.method, request.url.path)
    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = (perf_counter() - started) * 1000
        logger.exception("HTTP error method=%s path=%s elapsed_ms=%.2f", request.method, request.url.path, elapsed_ms)
        raise
    elapsed_ms = (perf_counter() - started) * 1000
    logger.info(
        "HTTP done method=%s path=%s status=%s elapsed_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    if request.method == "GET":
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
    return response


@app.get("/health")
async def health():
    logger.debug("Health check requested")
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# API Router (all data endpoints under /api/ prefix)
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/api")


@router.get("/studio")
async def get_studio():
    logger.info("Building studio bootstrap payload")
    return build_studio_bootstrap()


@router.get("/pipeline")
async def get_pipeline():
    logger.info("Loading active pipeline")
    return load_pipeline()


@router.put("/pipeline")
async def update_pipeline(pipeline: PipelineDefinition):
    logger.info("Saving active pipeline name=%s blocks=%s", pipeline.name, len(pipeline.blocks))
    return save_pipeline(pipeline)


@router.get("/pipelines")
async def get_named_pipelines():
    logger.info("Listing named pipelines")
    return list_named_pipelines()


@router.post("/pipelines/save")
async def save_pipeline_as_named(request: NamedPipelineSaveRequest):
    logger.info(
        "Saving named pipeline requested_name=%s blocks=%s set_active=%s",
        request.name,
        len(request.pipeline.blocks),
        request.set_active,
    )
    pipeline, item = save_named_pipeline(
        request.name,
        request.pipeline,
        set_active=request.set_active,
    )
    return {
        "pipeline": pipeline,
        "catalog_item": item,
        "pipeline_catalog": list_named_pipelines(),
    }


@router.post("/pipelines/load")
async def load_pipeline_by_name(request: NamedPipelineLoadRequest):
    logger.info("Loading named pipeline key_or_name=%s set_active=%s", request.name, request.set_active)
    try:
        pipeline = load_named_pipeline(request.name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if request.set_active:
        pipeline = save_pipeline(pipeline)

    return {
        "pipeline": pipeline,
        "pipeline_catalog": list_named_pipelines(),
    }


@router.delete("/pipelines/{key}")
async def delete_named_pipeline_endpoint(key: str):
    if not delete_named_pipeline(key):
        raise HTTPException(status_code=404, detail=f"Pipeline '{key}' not found")
    return {"status": "ok", "pipeline_catalog": list_named_pipelines()}


@router.post("/pipeline/reset")
async def reset_pipeline_to_default():
    logger.warning("Resetting pipeline to default")
    return save_pipeline(get_default_pipeline())


@router.post("/pipeline/snapshot")
async def create_pipeline_snapshot(request: PipelineSnapshotRequest):
    logger.info("Creating pipeline snapshot label=%s", request.label or request.pipeline.name)
    path = snapshot_pipeline(request.pipeline, request.label)
    return {"status": "ok", "path": str(path)}


@router.get("/settings")
async def get_settings():
    logger.info("Fetching settings payload")
    return get_settings_payload()


@router.put("/settings")
async def update_settings(settings: AppSettings):
    logger.info(
        "Updating settings gemini_set=%s openai_set=%s creds_set=%s",
        bool(settings.gemini_api_key),
        bool(settings.openai_api_key),
        bool(settings.google_application_credentials),
    )
    save_settings(settings)
    return get_settings_payload()


@router.get("/runs")
async def list_runs():
    logger.info("Listing run summaries")
    return build_studio_bootstrap().run_summaries


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    logger.info("Loading run details run_id=%s", run_id)
    try:
        return load_run_result(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/runs/{run_id}/artifacts/{artifact_name}")
async def get_run_artifact(run_id: str, artifact_name: str):
    logger.info("Fetching run artifact run_id=%s artifact=%s", run_id, artifact_name)
    if Path(artifact_name).name != artifact_name:
        raise HTTPException(status_code=400, detail="Invalid artifact name.")
    path = RUNS_DIR / run_id / artifact_name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"Artifact '{artifact_name}' not found for run '{run_id}'.")

    media_type = "application/json" if path.suffix.lower() == ".json" else "text/plain"
    return FileResponse(path, media_type=media_type)


@router.get("/runs/{run_id}/pipeline")
async def get_run_pipeline(run_id: str):
    snapshot_path = RUNS_DIR / run_id / "pipeline_snapshot.json"
    if not snapshot_path.exists():
        raise HTTPException(status_code=404, detail=f"Pipeline snapshot for run '{run_id}' not found")
    return PipelineDefinition.model_validate_json(snapshot_path.read_text(encoding="utf-8"))


@router.post("/run")
async def run_pipeline(request: RunPipelineRequest = RunPipelineRequest()):
    logger.info(
        "Run requested run_id=%s persist_pipeline=%s inline_pipeline=%s",
        request.run_id,
        request.persist_pipeline,
        bool(request.pipeline),
    )
    pipeline = request.pipeline or load_pipeline()
    if request.persist_pipeline:
        pipeline = save_pipeline(pipeline)

    settings = load_settings()
    runner = PipelineRunner(settings)
    try:
        result = runner.run_pipeline(pipeline, run_id=request.run_id)
        logger.info(
            "Run finished run_id=%s blocks=%s final_title=%s",
            result.run_id,
            result.block_count,
            result.final_title,
        )
        return result
    except Exception as exc:
        logger.exception("Run failed run_id=%s", request.run_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _bg_run_pipeline(run_id: str, pipeline: PipelineDefinition, settings: AppSettings):
    runner = PipelineRunner(settings)

    def _progress_callback(p: RunProgress):
        active_runs[run_id] = p

    try:
        runner.run_pipeline(pipeline, run_id=run_id, progress_callback=_progress_callback)
    except Exception:
        # runner already logs and updates progress status to FAILED
        pass
    finally:
        # Schedule cleanup after 60 seconds
        def _cleanup():
            import time
            time.sleep(60)
            active_runs.pop(run_id, None)
        threading.Thread(target=_cleanup, daemon=True).start()


@router.post("/runs/start")
async def start_run(
    background_tasks: BackgroundTasks,
    request: RunPipelineRequest = RunPipelineRequest(),
):
    run_id = request.run_id or f"run_{int(perf_counter() * 1000)}"
    logger.info("Async run start requested run_id=%s", run_id)

    pipeline = request.pipeline or load_pipeline()
    if request.persist_pipeline:
        pipeline = save_pipeline(pipeline)

    settings = load_settings()

    initial_progress = RunProgress(
        run_id=run_id,
        timestamp=Path().cwd().name,  # placeholder, runner will set real one
        pipeline_name=pipeline.name,
        status=RunStatus.QUEUED,
        block_count=len(pipeline.blocks),
        block_sequence=[b.id for b in pipeline.blocks if b.enabled],
    )
    active_runs[run_id] = initial_progress

    background_tasks.add_task(_bg_run_pipeline, run_id, pipeline, settings)

    return initial_progress


@router.get("/runs/{run_id}/status")
async def get_run_status(run_id: str):
    # Check in-memory first
    if run_id in active_runs:
        return active_runs[run_id]

    # Fallback to disk
    progress_path = RUNS_DIR / run_id / "run_progress.json"
    if progress_path.exists():
        return RunProgress.model_validate_json(progress_path.read_text(encoding="utf-8"))

    # If result exists but progress doesn't (old runs), synthesize progress
    try:
        result = load_run_result(run_id)
        return RunProgress(
            run_id=result.run_id,
            timestamp=result.timestamp,
            pipeline_name=result.pipeline_name,
            status=result.status,
            block_count=result.block_count,
            current_block_id=result.current_block_id,
            final_title=result.final_title,
            final_metrics=result.final_metrics,
            block_sequence=result.block_sequence,
            block_traces=result.block_traces,
            timeline=result.timeline,
            stats=result.stats,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")


@router.post("/compare")
async def compare_runs(request: CompareRunsRequest):
    logger.info(
        "Comparing runs baseline=%s candidate=%s",
        request.baseline_run_id,
        request.candidate_run_id,
    )
    try:
        baseline = load_run_result(request.baseline_run_id)
        candidate = load_run_result(request.candidate_run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return compare_final_outputs(request, baseline, candidate)


@router.post("/upload/{run_id}")
async def upload_run(run_id: str):
    logger.info("Upload requested for run_id=%s", run_id)
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
        logger.info("Upload completed run_id=%s story_id=%s", run_id, story_id)
    except Exception as exc:
        logger.exception("Upload failed run_id=%s", run_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"status": "ok", "story_id": story_id}


# ---------------------------------------------------------------------------
# Include the API router
# ---------------------------------------------------------------------------
app.include_router(router)

# ---------------------------------------------------------------------------
# SPA fallback: serve React build or legacy admin UI
# ---------------------------------------------------------------------------
REACT_BUILD_DIR = BASE_DIR / "admin_ui_v3" / "dist"

if REACT_BUILD_DIR.exists():
    app.mount("/assets", StaticFiles(directory=REACT_BUILD_DIR / "assets"), name="spa-assets")
elif ADMIN_UI_DIR.exists():
    app.mount("/admin-static", StaticFiles(directory=ADMIN_UI_DIR), name="admin-static")


@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    if REACT_BUILD_DIR.exists():
        index = REACT_BUILD_DIR / "index.html"
        if index.exists():
            return FileResponse(index)
    old_index = ADMIN_UI_DIR / "index.html"
    if old_index.exists():
        return FileResponse(old_index)
    raise HTTPException(404, detail="Admin UI not found.")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8042, reload=False)
