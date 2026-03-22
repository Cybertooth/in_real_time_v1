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
        BlockType,
        ProviderType,
        RunComparison,
        RunProgress,
        RunResult,
        RunStats,
        RunStatus,
        RunTimelineEntry,
        SCHEMA_MAP,
    )
    from .providers import get_provider
    from .storage import (
        BASE_DIR,
        PIPELINE_SNAPSHOT_FILENAME,
        RUNS_DIR,
        load_run_progress,
        load_run_result,
        save_run_progress,
        save_run_result,
    )
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
        ProviderType,
        RunComparison,
        RunProgress,
        RunResult,
        RunStats,
        RunStatus,
        RunTimelineEntry,
        SCHEMA_MAP,
    )
    from providers import get_provider
    from storage import (
        BASE_DIR,
        PIPELINE_SNAPSHOT_FILENAME,
        RUNS_DIR,
        load_run_progress,
        load_run_result,
        save_run_progress,
        save_run_result,
    )

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
        ("social_posts", "time_offset_minutes"),
        ("phone_calls", "time_offset_minutes"),
        ("group_chats", "time_offset_minutes"),
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
    social_posts = final_output.get("social_posts", [])
    phone_calls = final_output.get("phone_calls", [])
    group_chats = final_output.get("group_chats", [])

    # Count group chat messages across all threads
    group_chat_messages = sum(len(gc.get("messages", [])) for gc in group_chats)
    # Count phone call lines across all calls
    phone_call_lines = sum(len(pc.get("lines", [])) for pc in phone_calls)

    metrics = {
        "total_artifacts": (
            len(journals) + len(chats) + len(emails) + len(receipts) + len(voice_notes)
            + len(social_posts) + len(phone_calls) + len(group_chats)
        ),
        "journal_count": len(journals),
        "chat_count": len(chats),
        "email_count": len(emails),
        "receipt_count": len(receipts),
        "voice_note_count": len(voice_notes),
        "social_post_count": len(social_posts),
        "phone_call_count": len(phone_calls),
        "group_chat_count": len(group_chats),
        "group_chat_messages": group_chat_messages,
        "phone_call_lines": phone_call_lines,
        "journal_words": sum(_count_words(item.get("body", "")) for item in journals),
        "chat_words": sum(_count_words(item.get("text", "")) for item in chats),
        "email_words": sum(
            _count_words(item.get("subject", "")) + _count_words(item.get("body", ""))
            for item in emails
        ),
        "voice_note_words": sum(_count_words(item.get("transcript", "")) for item in voice_notes),
        "social_post_words": sum(_count_words(item.get("content", "")) for item in social_posts),
        "phone_call_words": sum(
            _count_words(line.get("text", ""))
            for pc in phone_calls
            for line in pc.get("lines", [])
        ),
        "group_chat_words": sum(
            _count_words(msg.get("text", ""))
            for gc in group_chats
            for msg in gc.get("messages", [])
        ),
    }
    metrics["total_words"] = (
        metrics["journal_words"]
        + metrics["chat_words"]
        + metrics["email_words"]
        + metrics["voice_note_words"]
        + metrics["social_post_words"]
        + metrics["phone_call_words"]
        + metrics["group_chat_words"]
    )
    metrics["quality_proxy_score"] = round(
        (
            metrics["total_artifacts"] * 1.5
            + metrics["total_words"] / 160
            + metrics["voice_note_count"] * 2
            + metrics["journal_count"] * 1.2
            + metrics["phone_call_count"] * 3
            + metrics["group_chat_count"] * 2.5
            + metrics["social_post_count"] * 1.0
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

    for i, sp in enumerate(final_output.get("social_posts", [])):
        mins = sp.get("time_offset_minutes", 0)
        platform = sp.get("platform", "social")
        entries.append(RunTimelineEntry(
            block_id=f"social_post_{i}", event_type="social_post",
            story_day=(mins // (24 * 60)) + 1, story_time=_to_clock(mins),
            title=f"{platform.capitalize()}: @{sp.get('handle', sp.get('author', 'Unknown'))}",
            content=dict(sp),
        ))

    for i, pc in enumerate(final_output.get("phone_calls", [])):
        mins = pc.get("time_offset_minutes", 0)
        entries.append(RunTimelineEntry(
            block_id=f"phone_call_{i}", event_type="phone_call",
            story_day=(mins // (24 * 60)) + 1, story_time=_to_clock(mins),
            title=f"Call: {pc.get('caller', '?')} → {pc.get('receiver', '?')}",
            content=dict(pc),
        ))

    for i, gc in enumerate(final_output.get("group_chats", [])):
        mins = gc.get("time_offset_minutes", 0)
        platform = gc.get("platform", "chat")
        entries.append(RunTimelineEntry(
            block_id=f"group_chat_{i}", event_type="group_chat",
            story_day=(mins // (24 * 60)) + 1, story_time=_to_clock(mins),
            title=f"{platform.capitalize()} Group: {gc.get('group_name', f'Thread {i+1}')}",
            content=dict(gc),
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
        "social_post_count",
        "social_post_words",
        "phone_call_count",
        "phone_call_words",
        "group_chat_count",
        "group_chat_words",
        "group_chat_messages",
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
            if block.type == BlockType.IMAGE_GENERATOR:
                # Find the upstream dependent payload
                if not block.input_blocks:
                    raise ValueError("Image Generator requires an input block.")
                input_id = block.input_blocks[0]
                if input_id not in outputs:
                    raise ValueError(f"Image Generator dependent block {input_id} output not found.")
                
                # We do a deep copy to preserve the original output's state, and mutate the new one
                import copy
                source_payload = copy.deepcopy(outputs[input_id])
                if hasattr(source_payload, "model_dump"):
                    source_payload = source_payload.model_dump()
                    
                output = generate_block_images(progress.run_id, source_payload, definition, self.settings)
                
            else:
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
        seed_prompt: str | None = None,
        tags: list[str] | None = None,
    ) -> RunResult:
        run_id = run_id or f"run_{int(time.time())}"
        started_at = datetime.now(timezone.utc)
        run_dir = RUNS_DIR / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Keep the original definition for snapshotting (seed must not be baked in)
        original_definition = definition

        # Inject seed prompt and tags into the first creative_outliner block's prompt
        if seed_prompt or tags:
            injected_parts: list[str] = []
            if seed_prompt:
                injected_parts.append(f"STORY SEED (use as creative inspiration):\n{seed_prompt}")
            if tags:
                injected_parts.append(f"REQUIRED THEMES / TAGS: {', '.join(tags)}")
            prefix = "\n\n".join(injected_parts) + "\n\n"

            import copy as _copy
            definition = _copy.deepcopy(definition)
            for block in definition.blocks:
                if block.enabled and block.type == "creative_outliner":
                    block.config.prompt_template = prefix + block.config.prompt_template
                    logger.info(
                        "Injected seed/tags into block id=%s seed_len=%s tags=%s",
                        block.id, len(seed_prompt or ""), tags,
                    )
                    break

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

        setup_val = ""
        characters_val = []
        for val in outputs.values():
            if isinstance(val, dict):
                if not characters_val and isinstance(val.get("characters"), list):
                    characters_val = val["characters"]
                if not setup_val and "core_conflict" in val:
                    setup_val = val["core_conflict"]
            elif hasattr(val, "model_dump"):
                dump = val.model_dump()
                if not characters_val and isinstance(dump.get("characters"), list):
                    characters_val = dump["characters"]
                if not setup_val and "core_conflict" in dump:
                    setup_val = dump["core_conflict"]

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
            seed_prompt=seed_prompt or None,
            tags=list(tags or []),
            setup=setup_val,
            characters=characters_val,
            outputs={block_id: _serialize_output(value) for block_id, value in outputs.items()},
            final_output=final_output,
            block_sequence=block_sequence,
            block_traces=traces,
            timeline=progress.timeline,
            stats=progress.stats,
        )

        # Image generation is now handled natively via the Pipeline blocks!

        # Save the ORIGINAL pipeline (without seed prefix baked in) so re-runs work cleanly
        save_run_result(result, original_definition)
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

    def retry_block(
        self,
        run_id: str,
        block_id: str,
        progress_callback: Any | None = None,
    ) -> RunProgress:
        """Re-execute a specific failed block and all downstream blocks that failed or never ran."""
        run_dir = RUNS_DIR / run_id

        # Load existing progress and pipeline snapshot
        progress = load_run_progress(run_id)
        snapshot_path = run_dir / PIPELINE_SNAPSHOT_FILENAME
        if not snapshot_path.exists():
            raise FileNotFoundError(f"Pipeline snapshot not found for run '{run_id}'")
        definition = PipelineDefinition.model_validate_json(
            snapshot_path.read_text(encoding="utf-8")
        )

        block_map = {b.id: b for b in definition.blocks if b.enabled}
        if block_id not in block_map:
            raise ValueError(f"Block '{block_id}' not found in pipeline for run '{run_id}'")

        # Restore outputs from artifacts for all succeeded blocks
        outputs: dict[str, Any] = {}
        for bid, trace in progress.block_traces.items():
            if trace.status == BlockExecutionStatus.SUCCEEDED:
                json_path = run_dir / f"{bid}.json"
                txt_path = run_dir / f"{bid}.txt"
                if json_path.exists():
                    outputs[bid] = json.loads(json_path.read_text(encoding="utf-8"))
                elif txt_path.exists():
                    outputs[bid] = txt_path.read_text(encoding="utf-8")

        # Build reverse dependency graph to find downstream blocks
        dependents: dict[str, set[str]] = {bid: set() for bid in block_map}
        for bid, block in block_map.items():
            for dep in block.input_blocks:
                if dep in dependents:
                    dependents[dep].add(bid)

        # BFS: retry the target block + all downstream that are failed or never ran
        retry_set: set[str] = set()
        queue = [block_id]
        while queue:
            current = queue.pop()
            if current not in block_map or current in retry_set:
                continue
            trace = progress.block_traces.get(current)
            if current == block_id or trace is None or trace.status != BlockExecutionStatus.SUCCEEDED:
                retry_set.add(current)
                queue.extend(dependents.get(current, set()))

        logger.info(
            "Retry start run_id=%s target_block=%s retry_set=%s",
            run_id, block_id, sorted(retry_set),
        )

        # Reset retry blocks to pending in progress
        for bid in retry_set:
            if bid in progress.block_traces:
                t = progress.block_traces[bid]
                t.status = BlockExecutionStatus.PENDING
                t.output = None
                t.error_message = None
                t.error_traceback = None
                t.started_at = None
                t.completed_at = None
                t.elapsed_ms = None
            else:
                block = block_map[bid]
                progress.block_traces[bid] = BlockTrace(
                    block_id=bid,
                    block_name=block.name,
                    block_type=block.type,
                    provider=block.config.provider,
                    model_name=block.config.model_name or "",
                    status=BlockExecutionStatus.PENDING,
                    response_schema_name=block.config.response_schema_name,
                    temperature=block.config.temperature,
                    input_blocks=list(block.input_blocks),
                )

        progress.status = RunStatus.RUNNING
        progress.error_message = None
        progress.completed_at = None

        # traces dict mirrors progress.block_traces so _run_one_block updates both
        traces: dict[str, BlockTrace] = dict(progress.block_traces)

        def _persist_progress():
            save_run_progress(progress)
            if progress_callback:
                progress_callback(progress)

        _persist_progress()

        # Build execution waves for retry_set only, using succeeded outputs as satisfied deps
        completed_deps: set[str] = set(outputs.keys())
        waves: list[list[PipelineBlock]] = []
        remaining = set(retry_set)
        while remaining:
            wave = [
                block_map[bid]
                for bid in sorted(remaining)
                if all(
                    dep in completed_deps or dep not in block_map
                    for dep in block_map[bid].input_blocks
                )
            ]
            if not wave:
                raise ValueError("Retry set has unresolvable dependencies — possible cycle.")
            for b in wave:
                completed_deps.add(b.id)
                remaining.discard(b.id)
            waves.append(wave)

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
                        bid_err, exc = errors[0]
                        raise RuntimeError(f"Block '{bid_err}' failed: {exc}") from exc

            progress.status = RunStatus.SUCCEEDED
            progress.completed_at = datetime.now(timezone.utc).isoformat()
        except Exception as exc:
            error_msg = str(exc)
            logger.exception("Retry failed run_id=%s", run_id)
            progress.status = RunStatus.FAILED
            progress.error_message = error_msg
            progress.completed_at = datetime.now(timezone.utc).isoformat()
            _persist_progress()

        # Recompute final output and metrics using the full pipeline wave order
        all_waves = self._execution_waves(definition)
        final_block_id_val = all_waves[-1][-1].id if all_waves else None
        final_output = _serialize_output(outputs.get(final_block_id_val)) if final_block_id_val else None
        final_metrics = _story_metrics(final_output if isinstance(final_output, dict) else None)

        if progress.status == RunStatus.SUCCEEDED:
            progress.final_title = (
                final_output.get("story_title") if isinstance(final_output, dict) else None
            )
            progress.final_metrics = final_metrics
            progress.timeline = derive_story_timeline(final_output)

        progress.stats = calculate_run_stats(traces, final_output)
        _persist_progress()

        # Persist updated RunResult if the run is now fully succeeded
        if progress.status == RunStatus.SUCCEEDED:
            try:
                old_result = load_run_result(run_id)
                seed = old_result.seed_prompt
                run_tags = old_result.tags
                ts = old_result.timestamp
            except Exception:
                seed = None
                run_tags = []
                ts = datetime.now(timezone.utc).isoformat()

            setup_val = ""
            characters_val = []
            for val in outputs.values():
                if isinstance(val, dict):
                    if not characters_val and isinstance(val.get("characters"), list):
                        characters_val = val["characters"]
                    if not setup_val and "core_conflict" in val:
                        setup_val = val["core_conflict"]
                elif hasattr(val, "model_dump"):
                    dump = val.model_dump()
                    if not characters_val and isinstance(dump.get("characters"), list):
                        characters_val = dump["characters"]
                    if not setup_val and "core_conflict" in dump:
                        setup_val = dump["core_conflict"]

            result = RunResult(
                run_id=run_id,
                timestamp=ts,
                pipeline_name=definition.name,
                status=RunStatus.SUCCEEDED,
                final_title=progress.final_title,
                block_count=len([t for t in traces.values() if t.status == BlockExecutionStatus.SUCCEEDED]),
                provider_summary=dict(provider_summary),
                artifact_counts={"blocks": len(execution_order), "files": len(list(run_dir.iterdir()))},
                final_metrics=final_metrics,
                mode="dry_run",
                seed_prompt=seed,
                tags=run_tags,
                setup=setup_val,
                characters=characters_val,
                outputs={bid: _serialize_output(v) for bid, v in outputs.items()},
                final_output=final_output,
                block_sequence=list(progress.block_sequence),
                block_traces=traces,
                timeline=progress.timeline,
                stats=progress.stats,
            )
            
            # Re-generate local block images (if IMAGE_GENERATOR was retried) is handled naturally inside the wave runner now!
            
            save_run_result(result, definition)

        logger.info(
            "Retry complete run_id=%s status=%s retried_blocks=%s",
            run_id, progress.status, sorted(retry_set),
        )

        if progress.status == RunStatus.FAILED:
            raise RuntimeError(progress.error_message)

        return progress

def generate_block_images(run_id: str, story_payload: dict[str, Any], pipeline: PipelineDefinition, settings: AppSettings) -> dict[str, Any]:
    image_provider_key = getattr(pipeline, "image_provider", ProviderType.GEMINI)
    provider_val = image_provider_key.value if hasattr(image_provider_key, "value") else image_provider_key
    image_model_name = getattr(pipeline, "default_image_models", {}).get(provider_val, "")
    
    if not image_model_name:
        return story_payload

    api_keys = {
        "GEMINI_API_KEY": settings.gemini_api_key,
        "OPENAI_API_KEY": settings.openai_api_key,
        "OPENROUTER_API_KEY": settings.openrouter_api_key,
        "ANTHROPIC_API_KEY": settings.anthropic_api_key,
    }
    
    try:
        img_provider = get_provider(image_provider_key, api_keys)
    except Exception as e:
        logger.warning(f"Could not initialize image provider: {e}")
        return story_payload

    images_dir = RUNS_DIR / run_id / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    def _gen_and_save(prompt: str, filename: str) -> str | None:
        try:
            logger.info("Generating image locally: %s", filename)
            img_bytes = img_provider.generate_image(prompt, image_model_name)
            path = images_dir / filename
            path.write_bytes(img_bytes)
            return f"images/{filename}"
        except Exception as e:
            logger.error("Local image generation failed for %s: %s", filename, e)
            return None

    if story_payload.get("headline_image_prompt") and not story_payload.get("headline_image_path"):
        path = _gen_and_save(story_payload["headline_image_prompt"], "headline.jpg")
        if path:
            story_payload["headline_image_path"] = path

    for collection_name in ["journals", "chats", "emails", "receipts", "voice_notes", "social_posts"]:
        items = story_payload.get(collection_name, [])
        for i, item in enumerate(items):
            prompt = item.get("image_prompt")
            if prompt and not item.get("local_image_path"):
                path = _gen_and_save(prompt, f"{collection_name}_{i}.jpg")
                if path:
                    item["local_image_path"] = path

    return story_payload


def upload_to_firestore(result: RunResult, firebase_service_account_path: str, settings: AppSettings, pipeline: PipelineDefinition):
    story_data = result.final_output
    if not isinstance(story_data, dict):
        raise ValueError("final_output must be a dict")
        
    logger.info("Upload start story_title=%s", story_data.get("story_title"))
    import firebase_admin
    from firebase_admin import credentials, firestore, storage
    import time
    from datetime import datetime, timezone, timedelta

    # Ensure path is absolute relative to BASE_DIR if it's a simple filename
    path = Path(firebase_service_account_path)
    if not path.is_absolute():
        path = (BASE_DIR / path).resolve()
    
    if not path.exists():
        raise FileNotFoundError(f"Firebase service account key not found at: {path}")
    
    resolved_path = str(path)

    cred = credentials.Certificate(resolved_path)
    try:
        app = firebase_admin.get_app()
    except ValueError:
        import json
        with open(resolved_path, "r", encoding="utf-8") as f:
            sa = json.load(f)
            project_id = sa.get("project_id")
        app = firebase_admin.initialize_app(cred, {"storageBucket": f"{project_id}.appspot.com"})
        
    db = firestore.client()
    try:
        bucket = storage.bucket()
    except Exception as e:
        logger.warning(f"Could not initialize storage bucket, images will be skipped. {e}")
        bucket = None

    start_time = datetime.now(timezone.utc)
    story_id = f"story_{int(time.time())}"
    story_ref = db.collection("stories").document(story_id)
    
    headline_url = None
    if getattr(result, "headline_image_path", None) and bucket:
        try:
            full_local_path = RUNS_DIR / result.run_id / result.headline_image_path
            if full_local_path.exists():
                blob = bucket.blob(f"stories/{story_id}/headline_{int(time.time())}.jpg")
                blob.upload_from_filename(str(full_local_path), content_type="image/jpeg")
                blob.make_public()
                headline_url = blob.public_url
        except Exception as e:
            logger.error("Headline image upload failed: %s", e)

    story_ref.set(
        {
            "title": story_data.get("story_title", "Untitled"),
            "setup": result.setup,
            "tags": result.tags,
            "characters": [_serialize_output(c) for c in result.characters],
            "headlineImageUrl": headline_url,
            "createdAt": start_time,
        }
    )

    def upload_collection(collection_name, items):
        if not items:
            return

        batch = db.batch()
        for i, item in enumerate(items):
            doc_ref = story_ref.collection(collection_name).document()
            unlock_time = start_time + timedelta(minutes=item.get("time_offset_minutes", 0))
            doc_data = item.copy()
            doc_data.pop("time_offset_minutes", None)
            doc_data["unlockTimestamp"] = unlock_time
            
            local_path = doc_data.pop("local_image_path", None)
            if local_path and bucket:
                try:
                    full_local_path = RUNS_DIR / result.run_id / local_path
                    if full_local_path.exists():
                        blob = bucket.blob(f"stories/{story_id}/{collection_name}_{i}_{int(time.time())}.jpg")
                        blob.upload_from_filename(str(full_local_path), content_type="image/jpeg")
                        blob.make_public()
                        doc_data["imageUrl"] = blob.public_url
                except Exception as e:
                    logger.error("Image upload failed: %s", e)

            batch.set(doc_ref, doc_data)
        batch.commit()

    upload_collection("journals", story_data.get("journals", []))
    upload_collection("chats", story_data.get("chats", []))
    upload_collection("emails", story_data.get("emails", []))
    upload_collection("receipts", story_data.get("receipts", []))
    upload_collection("voice_notes", story_data.get("voice_notes", []))
    upload_collection("social_posts", story_data.get("social_posts", []))
    upload_collection("phone_calls", story_data.get("phone_calls", []))
    upload_collection("group_chats", story_data.get("group_chats", []))

    logger.info("Upload complete story_id=%s", story_id)
    return story_id
