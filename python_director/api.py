from __future__ import annotations

import threading
from pathlib import Path
from time import perf_counter

from fastapi import APIRouter, BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

if __package__:
    from .defaults import get_pipeline_reset_template
    from .logic import PipelineRunner, compare_final_outputs, upload_to_firestore, derive_story_timeline
    from .log_utils import get_logger
    from .models import (
        AppSettings,
        CompareRunsRequest,
        NamedPipelineLoadRequest,
        NamedPipelineSaveRequest,
        PipelineDefinition,
        PipelineResetRequest,
        PipelineSnapshotRequest,
        RerunRequest,
        UploadRunRequest,
        RunPipelineRequest,
        RunProgress,
        RunStatus,
        RegenerateImageRequest,
    )
    from .storage import (
        BASE_DIR,
        RUNS_DIR,
        build_studio_bootstrap,
        delete_named_pipeline,
        delete_run,
        get_settings_payload,
        list_named_pipelines,
        load_named_pipeline,
        load_pipeline,
        load_run_result,
        load_settings,
        save_named_pipeline,
        save_pipeline,
        save_run_result,
        save_settings,
        snapshot_pipeline,
        PIPELINE_SNAPSHOT_FILENAME,
    )
else:
    from defaults import get_pipeline_reset_template
    from logic import PipelineRunner, compare_final_outputs, upload_to_firestore, derive_story_timeline
    from log_utils import get_logger
    from models import (
        AppSettings,
        CompareRunsRequest,
        NamedPipelineLoadRequest,
        NamedPipelineSaveRequest,
        PipelineDefinition,
        PipelineResetRequest,
        PipelineSnapshotRequest,
        RerunRequest,
        UploadRunRequest,
        RunPipelineRequest,
        RunProgress,
        RunStatus,
        RegenerateImageRequest,
    )
    from storage import (
        BASE_DIR,
        RUNS_DIR,
        build_studio_bootstrap,
        delete_named_pipeline,
        delete_run,
        get_settings_payload,
        list_named_pipelines,
        load_named_pipeline,
        load_pipeline,
        load_run_result,
        save_run_result,
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
async def reset_pipeline_to_default(request: PipelineResetRequest = PipelineResetRequest()):
    logger.warning("Resetting pipeline template_key=%s", request.template_key)
    try:
        pipeline = get_pipeline_reset_template(request.template_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return save_pipeline(pipeline)


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


def _bg_run_pipeline(
    run_id: str,
    pipeline: PipelineDefinition,
    settings: AppSettings,
    seed_prompt: str | None = None,
    tags: list[str] | None = None,
):
    runner = PipelineRunner(settings)

    def _progress_callback(p: RunProgress):
        active_runs[run_id] = p

    try:
        runner.run_pipeline(
            pipeline,
            run_id=run_id,
            progress_callback=_progress_callback,
            seed_prompt=seed_prompt,
            tags=tags or [],
        )
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

    background_tasks.add_task(
        _bg_run_pipeline, run_id, pipeline, settings,
        request.seed_prompt, request.tags,
    )

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


@router.post("/runs/{run_id}/rerun")
async def rerun_run(
    run_id: str,
    background_tasks: BackgroundTasks,
    request: RerunRequest = RerunRequest(),
):
    logger.info("Re-run requested from run_id=%s", run_id)

    # Load the original pipeline snapshot (seed-free)
    snapshot_path = RUNS_DIR / run_id / "pipeline_snapshot.json"
    if not snapshot_path.exists():
        raise HTTPException(status_code=404, detail=f"Pipeline snapshot for run '{run_id}' not found.")
    pipeline = PipelineDefinition.model_validate_json(snapshot_path.read_text(encoding="utf-8"))

    # Resolve seed/tags: use provided overrides, or fall back to what the original run used
    if request.use_original_seed and request.seed_prompt is None:
        try:
            original = load_run_result(run_id)
            seed_prompt = original.seed_prompt
            tags = original.tags
        except FileNotFoundError:
            seed_prompt = None
            tags = []
    else:
        seed_prompt = request.seed_prompt
        tags = request.tags

    settings = load_settings()
    new_run_id = f"run_{int(perf_counter() * 1000)}"

    initial_progress = RunProgress(
        run_id=new_run_id,
        timestamp=str(new_run_id),
        pipeline_name=pipeline.name,
        status=RunStatus.QUEUED,
        block_count=len([b for b in pipeline.blocks if b.enabled]),
        block_sequence=[b.id for b in pipeline.blocks if b.enabled],
    )
    active_runs[new_run_id] = initial_progress

    background_tasks.add_task(_bg_run_pipeline, new_run_id, pipeline, settings, seed_prompt, tags)
    logger.info("Re-run started new_run_id=%s from_run_id=%s", new_run_id, run_id)
    return initial_progress


def _bg_retry_block(run_id: str, block_id: str, settings: AppSettings):
    runner = PipelineRunner(settings)

    def _progress_callback(p: RunProgress):
        active_runs[run_id] = p

    try:
        runner.retry_block(run_id, block_id, _progress_callback)
    except Exception:
        pass
    finally:
        def _cleanup():
            import time
            time.sleep(60)
            active_runs.pop(run_id, None)
        threading.Thread(target=_cleanup, daemon=True).start()


@router.post("/runs/{run_id}/retry-block/{block_id}")
async def retry_block_endpoint(run_id: str, block_id: str, background_tasks: BackgroundTasks):
    logger.info("Retry block requested run_id=%s block_id=%s", run_id, block_id)

    # Guard: run must exist
    progress_path = RUNS_DIR / run_id / "run_progress.json"
    if not progress_path.exists():
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    # Guard: run must not already be active
    if run_id in active_runs and active_runs[run_id].status == RunStatus.RUNNING:
        raise HTTPException(status_code=409, detail="Run is already active. Wait for it to finish.")

    current = RunProgress.model_validate_json(progress_path.read_text(encoding="utf-8"))
    settings = load_settings()
    active_runs[run_id] = current
    background_tasks.add_task(_bg_retry_block, run_id, block_id, settings)
    return current


@router.delete("/runs/{run_id}")
async def delete_run_endpoint(run_id: str):
    logger.info("Delete run requested run_id=%s", run_id)
    if not delete_run(run_id):
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return {"status": "ok", "run_id": run_id}


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
async def upload_run(run_id: str, request: UploadRunRequest = UploadRunRequest()):
    logger.info(
        "Upload requested run_id=%s mode=%s tts_tier=%s scheduled_start_at=%s",
        run_id,
        request.story_mode.value,
        request.tts_tier.value,
        request.scheduled_start_at,
    )
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
        snapshot_path = RUNS_DIR / run_id / PIPELINE_SNAPSHOT_FILENAME
        if snapshot_path.exists():
            pipeline = PipelineDefinition.model_validate_json(snapshot_path.read_text(encoding="utf-8"))
        else:
            pipeline = load_pipeline()
        story_id = upload_to_firestore(
            run_result,
            cred_path,
            settings,
            pipeline,
            story_mode=request.story_mode.value,
            scheduled_start_at=request.scheduled_start_at,
            tts_tier=request.tts_tier.value,
        )
        logger.info("Upload completed run_id=%s story_id=%s", run_id, story_id)

        # Update the run_result on disk to persist the story_id
        run_result.story_id = story_id
        snapshot_path = RUNS_DIR / run_id / PIPELINE_SNAPSHOT_FILENAME
        if snapshot_path.exists():
            pipeline = PipelineDefinition.model_validate_json(snapshot_path.read_text(encoding="utf-8"))
            save_run_result(run_result, pipeline)
    except Exception as exc:
        logger.exception("Upload failed run_id=%s", run_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"status": "ok", "story_id": story_id}

@router.post("/runs/{run_id}/regenerate-image")
async def regenerate_image(run_id: str, req: RegenerateImageRequest):
    try:
        run_result = load_run_result(run_id)
        
        # Load the frozen pipeline from snapshot if it exists
        snapshot_path = RUNS_DIR / run_id / "pipeline_snapshot.json"
        if snapshot_path.exists():
            pipeline = PipelineDefinition.model_validate_json(snapshot_path.read_text(encoding="utf-8"))
        else:
            pipeline = load_pipeline()
            
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    settings = load_settings()

    from providers import get_provider, ProviderType
    image_provider_key = getattr(pipeline, "image_provider", ProviderType.GEMINI)
    image_model_name = getattr(pipeline, "default_image_models", {}).get(image_provider_key.value, "")
    
    if not image_model_name:
        raise HTTPException(status_code=400, detail="No image model configured.")

    api_keys = {
        "GEMINI_API_KEY": settings.gemini_api_key,
        "OPENAI_API_KEY": settings.openai_api_key,
        "OPENROUTER_API_KEY": settings.openrouter_api_key,
        "ANTHROPIC_API_KEY": settings.anthropic_api_key,
    }
    img_provider = get_provider(image_provider_key, api_keys)

    images_dir = RUNS_DIR / run_id / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    
    # Update property locally
    target_item = None
    filename = ""
    event_type = req.event_type
    final_out = run_result.final_output

    if not isinstance(final_out, dict):
        raise HTTPException(status_code=400, detail="Final output is not a dictionary.")

    if event_type == "headline":
        run_result.headline_image_prompt = req.new_prompt
        filename = "headline.jpg"
    else:
        # map `event_type` to plural if needed
        collection_map = {
            "journal": "journals", "chat": "chats", "email": "emails", "receipt": "receipts",
            "voice_note": "voice_notes", "social_post": "social_posts", "gallery": "photo_gallery",
        }
        collection_name = collection_map.get(event_type, event_type)
        if collection_name not in final_out:
            raise HTTPException(status_code=404, detail=f"Collection {collection_name} not found.")
        
        items = final_out[collection_name]
        if req.index < 0 or req.index >= len(items):
            raise HTTPException(status_code=404, detail="Index out of bounds.")
        
        target_item = items[req.index]
        target_item["image_prompt"] = req.new_prompt
        if collection_name == "photo_gallery":
            filename = f"gallery_{req.index}.jpg"
        else:
            filename = f"{collection_name}_{req.index}.jpg"

    # Invoke AI
    try:
        img_bytes = img_provider.generate_image(req.new_prompt, image_model_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Save to disk
    path = images_dir / filename
    path.write_bytes(img_bytes)

    # Attach local_image_path explicitly with cache buster
    import time
    cache_busted_path = f"images/{filename}?t={int(time.time())}"
    if event_type == "headline":
        run_result.headline_image_path = cache_busted_path
    elif target_item is not None:
        target_item["local_image_path"] = cache_busted_path
        run_result.timeline = derive_story_timeline(final_out)

    # Save updated RunResult
    # Important: Since we modified the original, we re-save using the snapshot pipeline
    save_run_result(run_result, pipeline)
    return {"status": "ok", "local_image_path": cache_busted_path}


@router.get("/runs/{run_id}/images/{filename:path}")
async def get_run_image(run_id: str, filename: str):
    # Drop query params (t=123) if present
    base_file = filename.split("?")[0]
    path = RUNS_DIR / run_id / "images" / base_file
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path)



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
    import os

    # Cloud Run provides the PORT environment variable.
    port = int(os.environ.get("PORT", 8042))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)
