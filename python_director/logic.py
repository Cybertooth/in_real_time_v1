from __future__ import annotations

import json
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel

if __package__:
    from .log_utils import get_logger
    from .models import (
        AppSettings,
        BlockTrace,
        CompareRunsRequest,
        MetricDelta,
        PipelineBlock,
        PipelineDefinition,
        RunComparison,
        RunResult,
        SCHEMA_MAP,
    )
    from .providers import get_provider
    from .storage import RUNS_DIR, save_run_result
else:
    from log_utils import get_logger
    from models import (
        AppSettings,
        BlockTrace,
        CompareRunsRequest,
        MetricDelta,
        PipelineBlock,
        PipelineDefinition,
        RunComparison,
        RunResult,
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
    return metrics


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

    def _sorted_blocks(self, definition: PipelineDefinition) -> list[PipelineBlock]:
        block_map = {block.id: block for block in definition.blocks if block.enabled}
        indegree = {block_id: 0 for block_id in block_map}

        for block in block_map.values():
            for dependency in block.input_blocks:
                if dependency in indegree:
                    indegree[block.id] += 1

        ready = [block_map[block_id] for block_id, degree in indegree.items() if degree == 0]
        order: list[PipelineBlock] = []

        while ready:
            current = ready.pop(0)
            order.append(current)
            for candidate in block_map.values():
                if current.id in candidate.input_blocks:
                    indegree[candidate.id] -= 1
                    if indegree[candidate.id] == 0:
                        ready.append(candidate)

        if len(order) != len(block_map):
            logger.error("Pipeline sort failed: cycle or missing dependency detected")
            raise ValueError("Pipeline has a cycle or references a missing dependency.")

        logger.info("Execution order resolved blocks=%s", [block.id for block in order])
        return order

    def run_pipeline(self, definition: PipelineDefinition, run_id: str | None = None) -> RunResult:
        run_id = run_id or f"run_{int(time.time())}"
        started_at = datetime.now(timezone.utc)
        run_dir = RUNS_DIR / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            "Run start run_id=%s pipeline=%s block_count=%s output_dir=%s",
            run_id,
            definition.name,
            len(definition.blocks),
            run_dir,
        )

        outputs: dict[str, Any] = {}
        traces: dict[str, BlockTrace] = {}
        provider_summary: Counter[str] = Counter()
        execution_order: list[str] = []

        for block in self._sorted_blocks(definition):
            block_started = time.time()
            effective_model_name = self._resolve_model_name(definition, block)
            effective_config = block.config.model_copy(update={"model_name": effective_model_name})
            provider_summary[block.config.provider.value] += 1
            execution_order.append(block.id)
            logger.info(
                "Block start id=%s type=%s provider=%s model=%s temp=%s inherited_model=%s",
                block.id,
                block.type,
                effective_config.provider,
                effective_config.model_name,
                effective_config.temperature,
                block.config.use_pipeline_default_model,
            )

            contents = block.config.prompt_template
            replaced_inputs = 0
            for input_id in block.input_blocks:
                if input_id not in outputs:
                    logger.warning("Block id=%s missing_input=%s (placeholder left unresolved)", block.id, input_id)
                    continue
                input_value = outputs[input_id]
                serialized = (
                    input_value.model_dump_json(indent=2)
                    if isinstance(input_value, BaseModel)
                    else json.dumps(input_value, indent=2)
                    if isinstance(input_value, (dict, list))
                    else str(input_value)
                )
                contents = contents.replace(f"{{{{{input_id}}}}}", serialized)
                replaced_inputs += 1
            logger.debug(
                "Block prompt prepared id=%s replaced_inputs=%s prompt_chars=%s",
                block.id,
                replaced_inputs,
                len(contents),
            )

            trace = BlockTrace(
                block_id=block.id,
                block_name=block.name,
                block_type=block.type,
                provider=effective_config.provider,
                model_name=effective_config.model_name or "",
                response_schema_name=effective_config.response_schema_name,
                temperature=effective_config.temperature,
                input_blocks=list(block.input_blocks),
                resolved_prompt=contents,
            )
            traces[block.id] = trace

            provider = get_provider(effective_config.provider, self._api_keys())
            if effective_config.response_schema_name:
                schema = SCHEMA_MAP.get(effective_config.response_schema_name)
                if schema is None:
                    logger.error("Block id=%s schema_missing=%s", block.id, effective_config.response_schema_name)
                    raise ValueError(f"Schema '{effective_config.response_schema_name}' is not defined.")
                output = provider.generate_structured_output(effective_config, contents, schema)
            else:
                output = provider.generate_content(effective_config, contents)

            outputs[block.id] = output
            _write_block_artifact(run_dir, block.id, output)
            _write_block_artifact(run_dir, f"{block.id}.prompt", contents)
            elapsed_ms = (time.time() - block_started) * 1000
            logger.info("Block done id=%s elapsed_ms=%.2f", block.id, elapsed_ms)

        final_block_id = execution_order[-1] if execution_order else None
        final_output = _serialize_output(outputs.get(final_block_id)) if final_block_id else None
        final_metrics = _story_metrics(final_output if isinstance(final_output, dict) else None)

        result = RunResult(
            run_id=run_id,
            timestamp=started_at.isoformat(),
            pipeline_name=definition.name,
            final_title=(final_output or {}).get("story_title") if isinstance(final_output, dict) else None,
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
            block_sequence=execution_order,
            block_traces=traces,
        )

        save_run_result(result, definition)
        logger.info(
            "Run complete run_id=%s blocks=%s final_title=%s quality_score=%s",
            run_id,
            result.block_count,
            result.final_title,
            result.final_metrics.get("quality_proxy_score"),
        )
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
