from __future__ import annotations

import json
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel

if __package__:
    from .log_utils import get_logger
    from .models import (
        AppSettings,
        BlockExecutionStatus,
        BlockTrace,
        CompareRunsRequest,
        MetricDelta,
        PipelineBlock,
        PipelineDefinition,
        RunComparison,
        RunProgress,
        RunResult,
        RunStats,
        RunStatus,
        RunTimelineEntry,
        SCHEMA_MAP,
    )
    from .providers import get_provider
    from .storage import RUNS_DIR, save_run_result
else:
    from log_utils import get_logger
    from models import (
        AppSettings,
        BlockExecutionStatus,
        BlockTrace,
        CompareRunsRequest,
        MetricDelta,
        PipelineBlock,
        PipelineDefinition,
        RunComparison,
        RunProgress,
        RunResult,
        RunStats,
        RunStatus,
        RunTimelineEntry,
        SCHEMA_MAP,
    )
    from providers import get_provider
    from storage import RUNS_DIR, save_run_result

logger = get_logger("python_director.logic")


def _serialize_output(data: Any) -> Any:
    if isinstance(data, BaseModel):
        return data.model_dump(mode="json")
    return data


def _write_block_artifact(run_dir: Path, block_id: str, data: Any) -> None:
    is_json = isinstance(data, (dict, list, BaseModel))
    suffix = ".json" if is_json else ".txt"
    payload = _serialize_output(data)
    path = run_dir / f"{block_id}{suffix}"
    if is_json:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    else:
        path.write_text(str(payload), encoding="utf-8")
    logger.debug("Artifact written path=%s", path)


def _count_words(value: str) -> int:
    return len([token for token in value.split() if token.strip()])


def _burstiness_metrics(final_output: dict[str, Any]) -> dict[str, float | int]:
    """Compute engagement density / burstiness metrics from artifact timing."""
    import math

    all_items: list[int] = []
    for collection, key in [
        ("journals", "time_offset_minutes"),
        ("chats", "time_offset_minutes"),
        ("emails", "time_offset_minutes"),
        ("receipts", "time_offset_minutes"),
        ("voice_notes", "time_offset_minutes"),
    ]:
        for item in final_output.get(collection, []):
            t = item.get(key)
            if isinstance(t, (int, float)):
                all_items.append(int(t))

    if len(all_items) < 2:
        return {
            "total_pause_minutes": 0,
            "max_pause_minutes": 0,
            "act1_pause_minutes": 0,
            "burstiness_score": 0,
            "avg_chat_burst_length": 0,
        }

    sorted_times = sorted(all_items)
    gaps = [sorted_times[i + 1] - sorted_times[i] for i in range(len(sorted_times) - 1)]

    total_pause = sum(gaps)
    max_pause = max(gaps)

    # Act 1 = first 960 minutes (~16 hours, first third of 48h)
    act1_times = [t for t in sorted_times if t <= 960]
    act1_gaps = (
        [act1_times[i + 1] - act1_times[i] for i in range(len(act1_times) - 1)]
        if len(act1_times) >= 2
        else []
    )
    act1_pause = sum(act1_gaps)

    # Burstiness score: 0-100 based on coefficient of variation of gaps.
    # Low CV (even spacing) = high score. High CV (long waits punctuated by bursts) = lower score.
    # We invert CV: score = max(0, 100 * (1 - CV)), clamped to [0, 100].
    if gaps:
        mean_gap = total_pause / len(gaps)
        if mean_gap > 0:
            variance = sum((g - mean_gap) ** 2 for g in gaps) / len(gaps)
            std_gap = math.sqrt(variance)
            cv = std_gap / mean_gap
            burstiness_score = round(max(0.0, min(100.0, 100.0 * (1.0 - cv))), 1)
        else:
            burstiness_score = 100.0
    else:
        burstiness_score = 0.0

    # Average chat burst length: group chats by 5-minute windows and average group size.
    chat_times = sorted(
        int(c.get("time_offset_minutes", 0))
        for c in final_output.get("chats", [])
        if isinstance(c.get("time_offset_minutes"), (int, float))
    )
    if chat_times:
        windows: list[list[int]] = []
        current_window: list[int] = [chat_times[0]]
        for t in chat_times[1:]:
            if t - current_window[0] <= 5:
                current_window.append(t)
            else:
                windows.append(current_window)
                current_window = [t]
        windows.append(current_window)
        avg_chat_burst_length = round(sum(len(w) for w in windows) / len(windows), 1)
    else:
        avg_chat_burst_length = 0.0

    return {
        "total_pause_minutes": total_pause,
        "max_pause_minutes": max_pause,
        "act1_pause_minutes": act1_pause,
        "burstiness_score": burstiness_score,
        "avg_chat_burst_length": avg_chat_burst_length,
    }


def _story_metrics(final_output: dict[str, Any] | None) -> dict[str, float | int]:
    if not isinstance(final_output, dict):
        return {}

    journals = final_output.get("journals", [])
    chats = final_output.get("chats", [])
    emails = final_output.get("emails", [])
    receipts = final_output.get("receipts", [])
    voice_notes = final_output.get("voice_notes", [])

    metrics = {
        "total_artifacts": len(journals) + len(chats) + len(emails) + len(receipts) + len(voice_notes),
        "journal_count": len(journals),
        "chat_count": len(chats),
        "email_count": len(emails),
        "receipt_count": len(receipts),
        "voice_note_count": len(voice_notes),
        "journal_words": sum(_count_words(item.get("body", "")) for item in journals),
        "chat_words": sum(_count_words(item.get("text", "")) for item in chats),
        "email_words": sum(
            _count_words(item.get("subject", "")) + _count_words(item.get("body", ""))
            for item in emails
        ),
        "voice_note_words": sum(_count_words(item.get("transcript", "")) for item in voice_notes),
    }
    metrics["total_words"] = (
        metrics["journal_words"]
        + metrics["chat_words"]
        + metrics["email_words"]
        + metrics["voice_note_words"]
    )
    metrics["quality_proxy_score"] = round(
        (
            metrics["total_artifacts"] * 1.5
            + metrics["total_words"] / 160
            + metrics["voice_note_count"] * 2
            + metrics["journal_count"] * 1.2
        ),
        2,
    )
    metrics.update(_burstiness_metrics(final_output))
    return metrics


def calculate_run_stats(traces: dict[str, BlockTrace], final_output: Any = None) -> RunStats:
    stats = RunStats(block_count=len(traces))
    total_tokens = 0
    total_cost = 0.0
    success_count = 0

    for trace in traces.values():
        if trace.status == BlockExecutionStatus.SUCCEEDED:
            success_count += 1
        # Basic cost estimation if we had token counts in traces (placeholder for now)
        # total_tokens += trace.metrics.get("tokens", 0)

    if stats.block_count > 0:
        stats.success_rate = round(float(success_count) / stats.block_count, 2)


    if isinstance(final_output, dict):
        story_metrics = _story_metrics(final_output)
        stats.total_words = story_metrics.get("total_words", 0)
        # stats.average_tension_score = story_metrics.get("average_tension", None)

    return stats


def derive_story_timeline(final_output: Any) -> list[RunTimelineEntry]:
    if not isinstance(final_output, dict):
        return []

    entries: list[RunTimelineEntry] = []

    def _to_clock(total_mins: int) -> str:
        # Simplistic mapping: 0 mins = 09:00 AM
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


def compare_final_outputs(request: CompareRunsRequest, baseline: RunResult, candidate: RunResult) -> RunComparison:
    logger.info(
        "Comparing outputs baseline=%s candidate=%s",
        request.baseline_run_id,
        request.candidate_run_id,
    )
    baseline_metrics = _story_metrics(baseline.final_output if isinstance(baseline.final_output, dict) else None)
    candidate_metrics = _story_metrics(candidate.final_output if isinstance(candidate.final_output, dict) else None)
    metric_labels = [
        "total_artifacts",
        "total_words",
        "journal_count",
        "journal_words",
        "chat_count",
        "chat_words",
        "email_count",
        "email_words",
        "voice_note_count",
        "voice_note_words",
        "receipt_count",
        "quality_proxy_score",
        "burstiness_score",
        "total_pause_minutes",
        "max_pause_minutes",
        "act1_pause_minutes",
        "avg_chat_burst_length",
    ]

    metrics = [
        MetricDelta(
            label=label,
            baseline=baseline_metrics.get(label, 0),
            candidate=candidate_metrics.get(label, 0),
            delta=candidate_metrics.get(label, 0) - baseline_metrics.get(label, 0),
        )
        for label in metric_labels
    ]

    notes: list[str] = []
    score_delta = candidate_metrics.get("quality_proxy_score", 0) - baseline_metrics.get("quality_proxy_score", 0)
    total_words_delta = candidate_metrics.get("total_words", 0) - baseline_metrics.get("total_words", 0)
    voice_delta = candidate_metrics.get("voice_note_count", 0) - baseline_metrics.get("voice_note_count", 0)
    journal_delta = candidate_metrics.get("journal_words", 0) - baseline_metrics.get("journal_words", 0)
    burst_delta = candidate_metrics.get("burstiness_score", 0) - baseline_metrics.get("burstiness_score", 0)
    act1_pause_delta = candidate_metrics.get("act1_pause_minutes", 0) - baseline_metrics.get("act1_pause_minutes", 0)

    if score_delta > 0:
        notes.append(f"Overall quality proxy improved by {score_delta:.2f}.")
    elif score_delta < 0:
        notes.append(f"Overall quality proxy decreased by {abs(score_delta):.2f}.")
    else:
        notes.append("Overall quality proxy stayed flat.")

    if total_words_delta > 0:
        notes.append(f"Narrative depth increased (+{int(total_words_delta)} words).")
    elif total_words_delta < 0:
        notes.append(f"Narrative depth decreased ({int(total_words_delta)} words).")

    if voice_delta > 0:
        notes.append(f"Voice note coverage increased (+{int(voice_delta)}).")
    elif voice_delta < 0:
        notes.append(f"Voice note coverage decreased ({int(voice_delta)}).")

    if journal_delta > 0:
        notes.append(f"Journal richness improved (+{int(journal_delta)} words).")
    elif journal_delta < 0:
        notes.append(f"Journal richness reduced ({int(journal_delta)} words).")

    if burst_delta > 2:
        notes.append(f"Engagement density improved (burstiness +{burst_delta:.1f}).")
    elif burst_delta < -2:
        notes.append(f"Engagement density dropped (burstiness {burst_delta:.1f}). Users may disengage.")

    if act1_pause_delta < -30:
        notes.append(f"Act 1 dead time reduced by {abs(int(act1_pause_delta))} min — better early retention.")
    elif act1_pause_delta > 30:
        notes.append(f"Act 1 dead time increased by {int(act1_pause_delta)} min — risk of early drop-off.")

    return RunComparison(
        baseline_run_id=request.baseline_run_id,
        candidate_run_id=request.candidate_run_id,
        baseline_title=(baseline.final_output or {}).get("story_title")
        if isinstance(baseline.final_output, dict)
        else None,
        candidate_title=(candidate.final_output or {}).get("story_title")
        if isinstance(candidate.final_output, dict)
        else None,
        metrics=metrics,
        quality_notes=notes,
        baseline_output=baseline.final_output,
        candidate_output=candidate.final_output,
    )


class PipelineRunner:
    def __init__(self, settings: AppSettings):
        self.settings = settings

    def _api_keys(self) -> dict[str, str | None]:
        return {
            "GEMINI_API_KEY": self.settings.gemini_api_key,
            "OPENAI_API_KEY": self.settings.openai_api_key,
            "ANTHROPIC_API_KEY": self.settings.anthropic_api_key,
            "OPENROUTER_API_KEY": self.settings.openrouter_api_key,
        }

    def _resolve_model_name(self, definition: PipelineDefinition, block: PipelineBlock) -> str:
        provider_key = block.config.provider.value
        pipeline_default = definition.default_models.get(provider_key)

        if block.config.use_pipeline_default_model and pipeline_default:
            return pipeline_default
        if block.config.model_name:
            return block.config.model_name
        if pipeline_default:
            return pipeline_default

        raise ValueError(
            f"Block '{block.id}' has no model configured and pipeline default for provider '{provider_key}' is missing."
        )

    def _execution_waves(self, definition: PipelineDefinition) -> list[list[PipelineBlock]]:
        """Group enabled blocks into parallel execution waves.

        Blocks within the same wave have no inter-dependencies and can run in parallel.
        Blocks in later waves depend only on blocks from earlier waves.
        """
        block_map = {b.id: b for b in definition.blocks if b.enabled}
        completed: set[str] = set()
        waves: list[list[PipelineBlock]] = []
        remaining = set(block_map.keys())

        while remaining:
            wave = [
                block_map[bid]
                for bid in sorted(remaining)  # sorted for determinism within a wave
                if all(
                    dep in completed or dep not in block_map
                    for dep in block_map[bid].input_blocks
                )
            ]
            if not wave:
                logger.error("Pipeline sort failed: cycle or unresolved dependency")
                raise ValueError("Pipeline has a cycle or references a missing dependency.")
            for b in wave:
                completed.add(b.id)
                remaining.discard(b.id)
            waves.append(wave)

        logger.info("Execution waves: %s", [[b.id for b in w] for w in waves])
        return waves

    def _run_one_block(
        self,
        block: PipelineBlock,
        definition: PipelineDefinition,
        outputs: dict[str, Any],
        run_dir: Path,
        lock: threading.Lock,
        traces: dict[str, BlockTrace],
        progress: RunProgress,
        persist_fn: Any,
        provider_summary: Counter[str],
        execution_order: list[str],
    ) -> None:
        """Execute a single block. Safe to call from a thread pool."""
        import traceback as tb

        block_started = time.time()
        effective_model_name = self._resolve_model_name(definition, block)
        effective_config = block.config.model_copy(update={"model_name": effective_model_name})

        logger.info(
            "Block start id=%s type=%s provider=%s model=%s temp=%s inherited=%s",
            block.id,
            block.type,
            effective_config.provider,
            effective_config.model_name,
            effective_config.temperature,
            block.config.use_pipeline_default_model,
        )

        # Resolve prompt — reads outputs of previous waves only, safe without lock
        contents = block.config.prompt_template
        resolved_inputs: dict[str, Any] = {}
        for input_id in block.input_blocks:
            if input_id not in outputs:
                logger.warning("Block id=%s missing_input=%s (left unresolved)", block.id, input_id)
                continue
            input_value = outputs[input_id]
            resolved_inputs[input_id] = _serialize_output(input_value)
            serialized = (
                input_value.model_dump_json(indent=2)
                if isinstance(input_value, BaseModel)
                else json.dumps(input_value, indent=2)
                if isinstance(input_value, (dict, list))
                else str(input_value)
            )
            contents = contents.replace(f"{{{{{input_id}}}}}", serialized)

        trace = BlockTrace(
            block_id=block.id,
            block_name=block.name,
            block_type=block.type,
            provider=effective_config.provider,
            model_name=effective_config.model_name or "",
            status=BlockExecutionStatus.RUNNING,
            response_schema_name=effective_config.response_schema_name,
            temperature=effective_config.temperature,
            input_blocks=list(block.input_blocks),
            resolved_prompt=contents,
            resolved_inputs=resolved_inputs,
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        with lock:
            traces[block.id] = trace
            progress.block_traces[block.id] = trace
            progress.current_block_id = block.id
            provider_summary[effective_config.provider.value] += 1
            execution_order.append(block.id)
            persist_fn()

        try:
            provider = get_provider(effective_config.provider, self._api_keys())
            if effective_config.response_schema_name:
                schema = SCHEMA_MAP.get(effective_config.response_schema_name)
                if schema is None:
                    raise ValueError(f"Schema '{effective_config.response_schema_name}' is not defined.")
                output = provider.generate_structured_output(effective_config, contents, schema)
            else:
                output = provider.generate_content(effective_config, contents)
        except Exception as exc:
            elapsed_ms = (time.time() - block_started) * 1000
            with lock:
                trace.status = BlockExecutionStatus.FAILED
                trace.error_message = str(exc)
                trace.error_traceback = tb.format_exc()
                trace.completed_at = datetime.now(timezone.utc).isoformat()
                trace.elapsed_ms = elapsed_ms
                persist_fn()
            raise

        elapsed_ms = (time.time() - block_started) * 1000
        logger.info("Block done id=%s elapsed_ms=%.2f", block.id, elapsed_ms)

        with lock:
            outputs[block.id] = output
            _write_block_artifact(run_dir, block.id, output)
            _write_block_artifact(run_dir, f"{block.id}.prompt", contents)
            trace.status = BlockExecutionStatus.SUCCEEDED
            trace.output = _serialize_output(output)
            trace.completed_at = datetime.now(timezone.utc).isoformat()
            trace.elapsed_ms = elapsed_ms
            persist_fn()

    def run_pipeline(
        self,
        definition: PipelineDefinition,
        run_id: str | None = None,
        progress_callback: Any | None = None,
    ) -> RunResult:
        run_id = run_id or f"run_{int(time.time())}"
        started_at = datetime.now(timezone.utc)
        run_dir = RUNS_DIR / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        waves = self._execution_waves(definition)
        # Pre-compute block_sequence from waves (deterministic, wave order preserved)
        block_sequence = [b.id for wave in waves for b in wave]

        progress = RunProgress(
            run_id=run_id,
            timestamp=started_at.isoformat(),
            pipeline_name=definition.name,
            status=RunStatus.RUNNING,
            block_count=len(block_sequence),
            block_sequence=block_sequence,
            started_at=started_at.isoformat(),
        )

        def _persist_progress():
            path = run_dir / "run_progress.json"
            path.write_text(progress.model_dump_json(indent=2), encoding="utf-8")
            if progress_callback:
                progress_callback(progress)

        logger.info(
            "Run start run_id=%s pipeline=%s blocks=%s waves=%s output_dir=%s",
            run_id,
            definition.name,
            len(block_sequence),
            len(waves),
            run_dir,
        )
        _persist_progress()

        outputs: dict[str, Any] = {}
        traces: dict[str, BlockTrace] = {}
        provider_summary: Counter[str] = Counter()
        execution_order: list[str] = []
        lock = threading.Lock()

        try:
            for wave in waves:
                if len(wave) == 1:
                    self._run_one_block(
                        wave[0], definition, outputs, run_dir, lock,
                        traces, progress, _persist_progress, provider_summary, execution_order,
                    )
                else:
                    logger.info(
                        "Parallel council wave (%d blocks): %s",
                        len(wave),
                        [b.id for b in wave],
                    )
                    errors: list[tuple[str, BaseException]] = []
                    with ThreadPoolExecutor(max_workers=len(wave)) as executor:
                        future_map = {
                            executor.submit(
                                self._run_one_block,
                                block, definition, outputs, run_dir, lock,
                                traces, progress, _persist_progress, provider_summary, execution_order,
                            ): block
                            for block in wave
                        }
                        for future in as_completed(future_map):
                            blk = future_map[future]
                            try:
                                future.result()
                            except Exception as exc:
                                errors.append((blk.id, exc))
                    if errors:
                        block_id, exc = errors[0]
                        raise RuntimeError(f"Council block '{block_id}' failed: {exc}") from exc

            progress.status = RunStatus.SUCCEEDED
            progress.completed_at = datetime.now(timezone.utc).isoformat()
        except Exception as exc:
            error_msg = str(exc)
            logger.exception("Run failed run_id=%s", run_id)
            progress.status = RunStatus.FAILED
            progress.error_message = error_msg
            progress.completed_at = datetime.now(timezone.utc).isoformat()
            _persist_progress()

        # Determine final output from the last wave's single block
        final_block_id = waves[-1][-1].id if waves else None
        final_output = _serialize_output(outputs.get(final_block_id)) if final_block_id else None
        final_metrics = _story_metrics(final_output if isinstance(final_output, dict) else None)

        if progress.status == RunStatus.SUCCEEDED:
            progress.final_title = (
                final_output.get("story_title") if isinstance(final_output, dict) else None
            )
            progress.final_metrics = final_metrics

        progress.stats = calculate_run_stats(traces, final_output)
        progress.timeline = derive_story_timeline(final_output)

        result = RunResult(
            run_id=run_id,
            timestamp=started_at.isoformat(),
            pipeline_name=definition.name,
            status=progress.status,
            error_message=progress.error_message,
            final_title=progress.final_title,
            block_count=len(execution_order),
            provider_summary=dict(provider_summary),
            artifact_counts={
                "blocks": len(execution_order),
                "files": len(list(run_dir.iterdir())),
            },
            final_metrics=final_metrics,
            mode="dry_run",
            outputs={block_id: _serialize_output(value) for block_id, value in outputs.items()},
            final_output=final_output,
            block_sequence=block_sequence,
            block_traces=traces,
            timeline=progress.timeline,
            stats=progress.stats,
        )

        save_run_result(result, definition)
        logger.info(
            "Run complete status=%s run_id=%s blocks=%s final_title=%s quality_score=%s",
            progress.status,
            run_id,
            result.block_count,
            result.final_title,
            result.final_metrics.get("quality_proxy_score"),
        )
        _persist_progress()

        if progress.status == RunStatus.FAILED:
            raise RuntimeError(progress.error_message)

        return result


def upload_to_firestore(story_data: dict, firebase_service_account_path: str):
    logger.info("Upload start story_title=%s", story_data.get("story_title"))
    import firebase_admin
    from firebase_admin import credentials, firestore

    cred = credentials.Certificate(firebase_service_account_path)
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(cred)
    db = firestore.client()

    start_time = datetime.now()
    story_id = f"story_{int(time.time())}"
    story_ref = db.collection("stories").document(story_id)
    story_ref.set(
        {
            "title": story_data.get("story_title", "Untitled"),
            "createdAt": start_time,
        }
    )

    def upload_collection(collection_name, items):
        if not items:
            return

        batch = db.batch()
        for item in items:
            doc_ref = story_ref.collection(collection_name).document()
            unlock_time = start_time + timedelta(minutes=item["time_offset_minutes"])
            doc_data = item.copy()
            doc_data.pop("time_offset_minutes", None)
            doc_data["unlockTimestamp"] = unlock_time
            batch.set(doc_ref, doc_data)
        batch.commit()

    upload_collection("journals", story_data.get("journals", []))
    upload_collection("chats", story_data.get("chats", []))
    upload_collection("emails", story_data.get("emails", []))
    upload_collection("receipts", story_data.get("receipts", []))
    upload_collection("voice_notes", story_data.get("voice_notes", []))

    logger.info("Upload complete story_id=%s", story_id)
    return story_id
