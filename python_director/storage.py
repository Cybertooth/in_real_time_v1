from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

if __package__:
    from .defaults import PROVIDER_MODELS, get_block_templates, get_default_pipeline
    from .models import (
        AppSettings,
        ArtifactFile,
        RunResult,
        RunSummary,
        SettingsPayload,
        SettingsStatus,
        StudioBootstrap,
    )
else:
    from defaults import PROVIDER_MODELS, get_block_templates, get_default_pipeline
    from models import (
        AppSettings,
        ArtifactFile,
        RunResult,
        RunSummary,
        SettingsPayload,
        SettingsStatus,
        StudioBootstrap,
    )

BASE_DIR = Path(__file__).resolve().parent
PIPELINE_FILE = BASE_DIR / "pipeline.json"
SETTINGS_FILE = BASE_DIR / "settings.local.json"
RUNS_DIR = BASE_DIR / "temp_artifacts"
SNAPSHOTS_DIR = BASE_DIR / "snapshots"
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_pipeline():
    default_pipeline = get_default_pipeline()
    if PIPELINE_FILE.exists():
        return default_pipeline.model_validate_json(PIPELINE_FILE.read_text(encoding="utf-8"))
    return default_pipeline


def save_pipeline(pipeline):
    payload = pipeline.model_copy(update={"updated_at": utc_now_iso()})
    _write_json(PIPELINE_FILE, payload.model_dump(mode="json"))
    return payload


def load_settings() -> AppSettings:
    payload: dict[str, Any] = {}
    if SETTINGS_FILE.exists():
        payload = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))

    payload.setdefault("gemini_api_key", os.getenv("GEMINI_API_KEY"))
    payload.setdefault("openai_api_key", os.getenv("OPENAI_API_KEY"))
    payload.setdefault(
        "google_application_credentials",
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
    )
    return AppSettings.model_validate(payload)


def save_settings(settings: AppSettings) -> AppSettings:
    _write_json(SETTINGS_FILE, settings.model_dump(mode="json"))
    return settings


def get_settings_payload() -> SettingsPayload:
    settings = load_settings()
    return SettingsPayload(
        settings=settings,
        status=SettingsStatus(
            gemini_configured=bool(settings.gemini_api_key),
            openai_configured=bool(settings.openai_api_key),
            google_credentials_configured=bool(settings.google_application_credentials),
        ),
    )


def snapshot_pipeline(pipeline, label: str | None = None) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_label = "_".join((label or pipeline.name or "pipeline").strip().lower().split())
    path = SNAPSHOTS_DIR / f"{stamp}_{safe_label}.json"
    _write_json(path, pipeline.model_dump(mode="json"))
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


def save_run_result(run_result: RunResult, pipeline) -> Path:
    run_dir = RUNS_DIR / run_result.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_json(run_dir / "run_result.json", run_result.model_dump(mode="json"))
    _write_json(run_dir / "pipeline_snapshot.json", pipeline.model_dump(mode="json"))
    return run_dir


def list_run_summaries() -> list[RunSummary]:
    if not RUNS_DIR.exists():
        return []

    summaries: list[RunSummary] = []
    for run_dir in RUNS_DIR.iterdir():
        if not run_dir.is_dir():
            continue
        run_result_path = run_dir / "run_result.json"
        if not run_result_path.exists():
            continue
        run_result = RunResult.model_validate_json(run_result_path.read_text(encoding="utf-8"))
        summaries.append(
            RunSummary(
                run_id=run_result.run_id,
                timestamp=run_result.timestamp,
                pipeline_name=run_result.pipeline_name,
                final_title=run_result.final_title,
                block_count=run_result.block_count,
                provider_summary=run_result.provider_summary,
                artifact_counts=run_result.artifact_counts,
                final_metrics=run_result.final_metrics,
                mode=run_result.mode,
            )
        )
    return sorted(summaries, key=lambda item: item.timestamp, reverse=True)


def load_run_result(run_id: str) -> RunResult:
    run_dir = RUNS_DIR / run_id
    run_result_path = run_dir / "run_result.json"
    if not run_result_path.exists():
        raise FileNotFoundError(f"Run '{run_id}' not found")

    run_result = RunResult.model_validate_json(run_result_path.read_text(encoding="utf-8"))
    return run_result.model_copy(update={"artifacts": _artifact_files_for_folder(run_dir)})


def build_studio_bootstrap() -> StudioBootstrap:
    return StudioBootstrap(
        pipeline=load_pipeline(),
        settings=get_settings_payload(),
        run_summaries=list_run_summaries(),
        schemas=["StoryPlan", "StoryCritique", "SceneList", "StoryGenerated"],
        block_types=[template.type for template in get_block_templates()],
        block_templates=get_block_templates(),
        provider_models=PROVIDER_MODELS,
    )
