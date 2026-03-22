from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

if __package__:
    from .defaults import (
        PROVIDER_MODELS,
        get_block_templates,
        get_default_pipeline,
        get_reset_template_catalog,
    )
    from .log_utils import get_logger
    from .models import (
        AppSettings,
        ArtifactFile,
        BlockTrace,
        PipelineDefinition,
        PipelineCatalogItem,
        RunProgress,
        RunResult,
        RunStatus,
        RunSummary,
        SettingsPayload,
        SettingsStatus,
        StudioBootstrap,
        SCHEMA_MAP,
    )
else:
    from defaults import (
        PROVIDER_MODELS,
        get_block_templates,
        get_default_pipeline,
        get_reset_template_catalog,
    )
    from log_utils import get_logger
    from models import (
        AppSettings,
        ArtifactFile,
        BlockTrace,
        PipelineDefinition,
        PipelineCatalogItem,
        RunProgress,
        RunResult,
        RunStatus,
        RunSummary,
        SettingsPayload,
        SettingsStatus,
        StudioBootstrap,
        SCHEMA_MAP,
    )

BASE_DIR = Path(__file__).resolve().parent
PIPELINE_FILE = BASE_DIR / "pipeline.json"
SETTINGS_FILE = BASE_DIR / "settings.local.json"
RUNS_DIR = BASE_DIR / "temp_artifacts"
SNAPSHOTS_DIR = BASE_DIR / "snapshots"
PIPELINES_DIR = BASE_DIR / "pipelines"
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)
logger = get_logger("python_director.storage")
RUN_PROGRESS_FILENAME = "run_progress.json"
RUN_RESULT_FILENAME = "run_result.json"
PIPELINE_SNAPSHOT_FILENAME = "pipeline_snapshot.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.debug("JSON written path=%s", path)


def _slugify(name: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower()).strip("_")
    return value or "pipeline"


def _pipeline_path_by_key(key: str) -> Path:
    return PIPELINES_DIR / f"{_slugify(key)}.json"


def delete_named_pipeline(key: str) -> bool:
    path = _pipeline_path_by_key(key)
    if not path.exists():
        return False
    path.unlink()
    logger.info("Deleted named pipeline key=%s path=%s", key, path)
    return True


def _normalize_pipeline_models(pipeline: PipelineDefinition) -> PipelineDefinition:
    payload = pipeline.model_copy(deep=True)
    default_models = dict(payload.default_models or {})
    if not default_models:
        default_models = get_default_pipeline().default_models
        payload.default_models = default_models

    for block in payload.blocks:
        provider_key = block.config.provider.value
        pipeline_default = default_models.get(provider_key)
        if block.config.use_pipeline_default_model and pipeline_default:
            block.config.model_name = pipeline_default
        elif not block.config.model_name and pipeline_default:
            block.config.model_name = pipeline_default

    return payload


def _archive_invalid_file(path: Path, reason: str) -> None:
    if not path.exists():
        return
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archived = path.with_name(f"{path.stem}.invalid.{stamp}{path.suffix}")
    try:
        path.replace(archived)
        logger.warning("Archived invalid file path=%s archived_to=%s reason=%s", path, archived, reason)
    except Exception:
        logger.exception("Failed to archive invalid file path=%s reason=%s", path, reason)


def load_pipeline():
    if PIPELINE_FILE.exists():
        logger.info("Loading active pipeline from %s", PIPELINE_FILE)
        try:
            return _normalize_pipeline_models(
                PipelineDefinition.model_validate_json(PIPELINE_FILE.read_text(encoding="utf-8"))
            )
        except Exception:
            logger.exception("Active pipeline is invalid; resetting to default pipeline")
            _archive_invalid_file(PIPELINE_FILE, "pipeline_parse_error")
            return save_pipeline(get_default_pipeline())
    logger.info("No pipeline file found, initializing from default pipeline")
    return save_pipeline(get_default_pipeline())


def save_pipeline(pipeline):
    payload = _normalize_pipeline_models(pipeline).model_copy(update={"updated_at": utc_now_iso()})
    _write_json(PIPELINE_FILE, payload.model_dump(mode="json"))
    logger.info("Saved active pipeline name=%s blocks=%s", payload.name, len(payload.blocks))
    return payload


def save_named_pipeline(name: str, pipeline, set_active: bool = True) -> tuple[Any, PipelineCatalogItem]:
    key = _slugify(name)
    payload = _normalize_pipeline_models(pipeline).model_copy(update={"name": name, "updated_at": utc_now_iso()})
    _write_json(_pipeline_path_by_key(key), payload.model_dump(mode="json"))
    logger.info("Saved named pipeline key=%s name=%s blocks=%s", key, payload.name, len(payload.blocks))
    if set_active:
        payload = save_pipeline(payload)
    return payload, PipelineCatalogItem(
        key=key,
        name=payload.name,
        description=payload.description,
        updated_at=payload.updated_at,
        block_count=len(payload.blocks),
    )


def load_named_pipeline(name: str):
    direct = _pipeline_path_by_key(name)
    if direct.exists():
        logger.info("Loading named pipeline direct key=%s", name)
        try:
            return _normalize_pipeline_models(
                PipelineDefinition.model_validate_json(direct.read_text(encoding="utf-8"))
            )
        except Exception as exc:
            logger.exception("Named pipeline file invalid key=%s path=%s", name, direct)
            raise FileNotFoundError(f"Named pipeline '{name}' is invalid. Re-save it from the UI.") from exc

    normalized = name.strip().lower()
    logger.info("Searching named pipeline by display name=%s", normalized)
    for path in PIPELINES_DIR.glob("*.json"):
        try:
            parsed = _normalize_pipeline_models(
                PipelineDefinition.model_validate_json(path.read_text(encoding="utf-8"))
            )
        except Exception:
            logger.exception("Skipping invalid named pipeline while searching path=%s", path)
            continue
        if parsed.name.strip().lower() == normalized:
            return parsed
    raise FileNotFoundError(f"Named pipeline '{name}' not found")


def list_named_pipelines() -> list[PipelineCatalogItem]:
    PIPELINES_DIR.mkdir(parents=True, exist_ok=True)
    items: list[PipelineCatalogItem] = []
    for path in PIPELINES_DIR.glob("*.json"):
        try:
            parsed = _normalize_pipeline_models(
                PipelineDefinition.model_validate_json(path.read_text(encoding="utf-8"))
            )
            items.append(
                PipelineCatalogItem(
                    key=path.stem,
                    name=parsed.name,
                    description=parsed.description,
                    updated_at=parsed.updated_at,
                    block_count=len(parsed.blocks),
                )
            )
        except Exception:
            logger.exception("Skipping invalid named pipeline file path=%s", path)
            continue

    sorted_items = sorted(items, key=lambda item: item.updated_at or "", reverse=True)
    logger.info("Listed named pipelines count=%s", len(sorted_items))
    return sorted_items


def load_settings() -> AppSettings:
    payload: dict[str, Any] = {}
    if SETTINGS_FILE.exists():
        logger.info("Loading settings from %s", SETTINGS_FILE)
        try:
            payload = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            logger.exception("Settings file invalid JSON; archiving and falling back to env/defaults")
            _archive_invalid_file(SETTINGS_FILE, "settings_parse_error")
            payload = {}

    payload.setdefault("gemini_api_key", os.getenv("GEMINI_API_KEY"))
    payload.setdefault("openai_api_key", os.getenv("OPENAI_API_KEY"))
    payload.setdefault("anthropic_api_key", os.getenv("ANTHROPIC_API_KEY"))
    payload.setdefault("openrouter_api_key", os.getenv("OPENROUTER_API_KEY"))
    payload.setdefault(
        "google_application_credentials",
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
    )
    return AppSettings.model_validate(payload)


def save_settings(settings: AppSettings) -> AppSettings:
    _write_json(SETTINGS_FILE, settings.model_dump(mode="json"))
    logger.info(
        "Saved settings gemini_set=%s openai_set=%s anthropic_set=%s openrouter_set=%s creds_set=%s",
        bool(settings.gemini_api_key),
        bool(settings.openai_api_key),
        bool(settings.anthropic_api_key),
        bool(settings.openrouter_api_key),
        bool(settings.google_application_credentials),
    )
    return settings


def get_settings_payload() -> SettingsPayload:
    settings = load_settings()
    return SettingsPayload(
        settings=settings,
        status=SettingsStatus(
            gemini_configured=bool(settings.gemini_api_key),
            openai_configured=bool(settings.openai_api_key),
            anthropic_configured=bool(settings.anthropic_api_key),
            openrouter_configured=bool(settings.openrouter_api_key),
            google_credentials_configured=bool(settings.google_application_credentials),
        ),
    )


def snapshot_pipeline(pipeline, label: str | None = None) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_label = "_".join((label or pipeline.name or "pipeline").strip().lower().split())
    path = SNAPSHOTS_DIR / f"{stamp}_{safe_label}.json"
    _write_json(path, pipeline.model_dump(mode="json"))
    logger.info("Created pipeline snapshot path=%s", path)
    return path


def _artifact_files_for_folder(folder: Path) -> list[ArtifactFile]:
    artifact_files: list[ArtifactFile] = []
    if not folder.exists():
        return artifact_files

    for path in sorted(folder.iterdir()):
        if not path.is_file():
            continue
        artifact_files.append(
            ArtifactFile(
                name=path.name,
                relative_path=str(path.relative_to(BASE_DIR)),
                size_bytes=path.stat().st_size,
                content_type="application/json" if path.suffix.lower() == ".json" else "text/plain",
            )
        )
    return artifact_files


def _run_progress_path(run_id: str) -> Path:
    return RUNS_DIR / run_id / RUN_PROGRESS_FILENAME


def _run_result_path(run_id: str) -> Path:
    return RUNS_DIR / run_id / RUN_RESULT_FILENAME


def _pipeline_snapshot_path(run_id: str) -> Path:
    return RUNS_DIR / run_id / PIPELINE_SNAPSHOT_FILENAME


def save_run_progress(run_progress: RunProgress, pipeline: PipelineDefinition | None = None) -> Path:
    run_dir = RUNS_DIR / run_progress.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_json(_run_progress_path(run_progress.run_id), run_progress.model_dump(mode="json"))
    if pipeline is not None and not _pipeline_snapshot_path(run_progress.run_id).exists():
        _write_json(_pipeline_snapshot_path(run_progress.run_id), pipeline.model_dump(mode="json"))
    logger.debug("Persisted run progress run_id=%s status=%s", run_progress.run_id, run_progress.status)
    return run_dir


def load_run_progress(run_id: str) -> RunProgress:
    progress_path = _run_progress_path(run_id)
    if not progress_path.exists():
        raise FileNotFoundError(f"Run progress for '{run_id}' not found")
    run_progress = RunProgress.model_validate_json(progress_path.read_text(encoding="utf-8"))
    logger.info("Loaded run progress run_id=%s status=%s", run_id, run_progress.status)
    return run_progress


def run_progress_from_result(run_result: RunResult) -> RunProgress:
    return RunProgress(
        run_id=run_result.run_id,
        timestamp=run_result.timestamp,
        pipeline_name=run_result.pipeline_name,
        status=run_result.status,
        mode=run_result.mode,
        block_count=run_result.block_count,
        current_block_id=run_result.current_block_id,
        started_at=run_result.timestamp,
        completed_at=max(
            (trace.completed_at for trace in run_result.block_traces.values() if trace.completed_at),
            default=None,
        ),
        error_message=run_result.error_message,
        final_title=run_result.final_title,
        final_metrics=run_result.final_metrics,
        block_sequence=run_result.block_sequence,
        block_traces=run_result.block_traces,
        timeline=run_result.timeline,
        stats=run_result.stats,
        story_id=run_result.story_id,
    )


def _summary_from_run_progress(run_progress: RunProgress) -> RunSummary:
    return RunSummary(
        run_id=run_progress.run_id,
        timestamp=run_progress.timestamp,
        pipeline_name=run_progress.pipeline_name,
        status=run_progress.status,
        final_title=run_progress.final_title,
        block_count=run_progress.block_count,
        provider_summary={
            trace.provider.value: sum(1 for candidate in run_progress.block_traces.values() if candidate.provider == trace.provider)
            for trace in run_progress.block_traces.values()
        },
        artifact_counts={},
        final_metrics=run_progress.final_metrics,
        mode=run_progress.mode,
        error_message=run_progress.error_message,
        story_id=run_progress.story_id,
    )


def save_run_result(run_result: RunResult, pipeline) -> Path:
    run_dir = RUNS_DIR / run_result.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_json(_run_result_path(run_result.run_id), run_result.model_dump(mode="json"))
    _write_json(_pipeline_snapshot_path(run_result.run_id), pipeline.model_dump(mode="json"))
    save_run_progress(run_progress_from_result(run_result), pipeline)
    logger.info("Persisted run result run_id=%s path=%s", run_result.run_id, run_dir)
    return run_dir


def list_run_summaries() -> list[RunSummary]:
    if not RUNS_DIR.exists():
        return []

    summaries: list[RunSummary] = []
    skipped = 0
    for run_dir in RUNS_DIR.iterdir():
        if not run_dir.is_dir():
            continue
        run_result_path = run_dir / RUN_RESULT_FILENAME
        run_progress_path = run_dir / RUN_PROGRESS_FILENAME
        if run_result_path.exists():
            try:
                run_result = RunResult.model_validate_json(run_result_path.read_text(encoding="utf-8"))
            except Exception:
                skipped += 1
                logger.exception("Skipping invalid run_result file path=%s", run_result_path)
                continue
            summaries.append(
                RunSummary(
                    run_id=run_result.run_id,
                    timestamp=run_result.timestamp,
                    pipeline_name=run_result.pipeline_name,
                    status=run_result.status,
                    final_title=run_result.final_title,
                    block_count=run_result.block_count,
                    provider_summary=run_result.provider_summary,
                    artifact_counts=run_result.artifact_counts,
                    final_metrics=run_result.final_metrics,
                    mode=run_result.mode,
                    error_message=run_result.error_message,
                    seed_prompt=run_result.seed_prompt,
                    tags=run_result.tags,
                    story_id=run_result.story_id,
                )
            )
            continue

        if run_progress_path.exists():
            try:
                run_progress = RunProgress.model_validate_json(run_progress_path.read_text(encoding="utf-8"))
            except Exception:
                skipped += 1
                logger.exception("Skipping invalid run_progress file path=%s", run_progress_path)
                continue
            summaries.append(_summary_from_run_progress(run_progress))
    sorted_runs = sorted(summaries, key=lambda item: item.timestamp, reverse=True)
    logger.info("Listed run summaries count=%s skipped_invalid=%s", len(sorted_runs), skipped)
    return sorted_runs


def load_run_result(run_id: str) -> RunResult:
    run_dir = RUNS_DIR / run_id
    run_result_path = run_dir / RUN_RESULT_FILENAME
    if not run_result_path.exists():
        raise FileNotFoundError(f"Run '{run_id}' not found")

    run_result = RunResult.model_validate_json(run_result_path.read_text(encoding="utf-8"))
    logger.info("Loaded run result run_id=%s", run_id)
    return run_result.model_copy(update={"artifacts": _artifact_files_for_folder(run_dir)})


def delete_run(run_id: str) -> bool:
    import shutil
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        return False
    shutil.rmtree(run_dir)
    logger.info("Deleted run run_id=%s", run_id)
    return True


def build_studio_bootstrap() -> StudioBootstrap:
    logger.info("Building studio bootstrap")
    return StudioBootstrap(
        pipeline=load_pipeline(),
        pipeline_catalog=list_named_pipelines(),
        settings=get_settings_payload(),
        run_summaries=list_run_summaries(),
        schemas=list(SCHEMA_MAP.keys()),
        block_types=[template.type for template in get_block_templates()],
        block_templates=get_block_templates(),
        reset_templates=get_reset_template_catalog(),
        provider_models=PROVIDER_MODELS,
    )
