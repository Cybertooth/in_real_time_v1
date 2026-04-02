from __future__ import annotations

import json
import hashlib
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel

if __package__:
    from .log_utils import get_logger
    from .models import (
        AppSettings,
        BlockConfig,
        BlockExecutionStatus,
        BlockTrace,
        CompareRunsRequest,
        EvaluatedArtifactRef,
        HookReadinessStatus,
        HookSimulationDeterministicSignals,
        HookSimulationLLMReview,
        HookSimulationReport,
        HookSimulationScores,
        HookTimelineBeat,
        HookDeadZone,
        MetricDelta,
        PipelineBlock,
        PipelineDefinition,
        BlockType,
        ProviderType,
        QAFindingSeverity,
        QAPassStatus,
        RunComparison,
        RunProgress,
        RunResult,
        RunStats,
        RunStatus,
        RunTimelineEntry,
        SCHEMA_MAP,
        StoryQAReport,
        StoryQAFinding,
        StoryQAPassResult,
        StoryQAPassReview,
        StoryQAStatus,
        StoryGeneratedImagePatch,
        StoryPackaging,
        HeroArtifactPreview,
        BlockConfig,
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
        BlockConfig,
        BlockExecutionStatus,
        BlockTrace,
        CompareRunsRequest,
        EvaluatedArtifactRef,
        HookReadinessStatus,
        HookSimulationDeterministicSignals,
        HookSimulationLLMReview,
        HookSimulationReport,
        HookSimulationScores,
        HookTimelineBeat,
        HookDeadZone,
        MetricDelta,
        PipelineBlock,
        PipelineDefinition,
        BlockType,
        ProviderType,
        QAFindingSeverity,
        QAPassStatus,
        RunComparison,
        RunProgress,
        RunResult,
        RunStats,
        RunStatus,
        RunTimelineEntry,
        SCHEMA_MAP,
        StoryQAReport,
        StoryQAFinding,
        StoryQAPassResult,
        StoryQAPassReview,
        StoryQAStatus,
        StoryGeneratedImagePatch,
        StoryPackaging,
        HeroArtifactPreview,
        BlockConfig,
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

_PREMIUM_TTS_VOICES = ["alloy", "echo", "fable", "nova", "onyx", "shimmer"]
_CHEAP_TTS_VOICES = ["alloy", "echo", "nova"]
_THEME_PALETTE = [
    "#00FF9C",
    "#FF8A65",
    "#90CAF9",
    "#A5D6A7",
    "#FFB74D",
    "#4DD0E1",
    "#CE93D8",
    "#F48FB1",
    "#81D4FA",
    "#AED581",
]
_IMAGE_MODEL_FALLBACKS: dict[ProviderType, list[str]] = {
    ProviderType.OPENROUTER: [
        "bytedance-seed/seedream-4.5",
        "black-forest-labs/flux-1-schnell",
        "stabilityai/stable-diffusion-3.5-large",
    ],
    ProviderType.OPENAI: ["gpt-image-1"],
    ProviderType.GEMINI: ["gemini-3.1-flash-image-preview", "imagen-4.0-fast-generate-001"],
}
_IMAGE_PROVIDER_ORDER: list[ProviderType] = [
    ProviderType.OPENROUTER,
    ProviderType.OPENAI,
    ProviderType.GEMINI,
]
_DRY_RUN_STAGE_MIN = 1
_DRY_RUN_STAGE_MAX = 3
_DRY_RUN_STAGE_NAMES: dict[int, str] = {
    1: "fundamental_story_generation",
    2: "story_event_decomposition",
    3: "multimedia_artifact_generation",
}
_STAGE1_BLOCK_TYPES: set[BlockType] = {
    BlockType.CREATIVE_OUTLINER,
    BlockType.BRAINSTORM_CRITIC,
    BlockType.BRAINSTORM_REWRITER,
    BlockType.PLANNER,
    BlockType.CRITIC,
    BlockType.REVISER,
    BlockType.CONTINUITY_AUDITOR,
    BlockType.DROP_DIRECTOR,
    BlockType.COUNCIL_MEMBER,
    BlockType.COUNCIL_JUDGE,
    BlockType.VISUAL_BIBLE,
}
_STAGE2_BLOCK_TYPES: set[BlockType] = {
    BlockType.DECOMPOSER,
    BlockType.GENERATOR,
}
_ON_DEMAND_DEFAULT_CONFIG: dict[str, int] = {
    "burstWindowMinutes": 90,
    "sessionDurationMinutes": 9,
    "inactivityResetMinutes": 12,
}
_HOOK_WINDOW_MINUTES = 24 * 60
_HOOK_ARTIFACT_LIMIT = 10
_HOOK_DEAD_ZONE_THRESHOLD = 150
_HIGH_INTEREST_THRESHOLD = 6.5
_CONCRETE_EVIDENCE_TYPES = {"receipt", "voice_note", "phone_call", "photo"}
_HIGH_SIGNAL_TERMS = {
    "blood", "help", "missing", "urgent", "police", "scream", "gun", "secret", "lied",
    "betray", "don't tell", "delete", "proof", "receipt", "call me", "where are you",
    "found", "panic", "hurry", "afraid", "sorry", "caught", "dead", "hide",
}
_EMOTIONAL_TERMS = {
    "afraid", "terrified", "ashamed", "sorry", "love", "hate", "panic", "cry", "please",
    "betrayed", "worried", "desperate", "furious", "confused", "regret",
}
_QUESTION_TERMS = {"why", "who", "what happened", "where", "how", "did you", "are you"}
_EVALUATION_PROVIDER_FALLBACKS: list[tuple[ProviderType, str]] = [
    (ProviderType.OPENAI, "gpt-5.4-mini"),
    (ProviderType.GEMINI, "gemini-2.5-flash"),
    (ProviderType.OPENROUTER, "openai/gpt-4.1-mini"),
    (ProviderType.ANTHROPIC, "claude-3-5-haiku-latest"),
]


def _resolve_credentials_path_with_candidates(path_val: str | None) -> tuple[Path | None, list[Path]]:
    """Resolve Firebase credentials path across common project-relative locations."""
    if not path_val:
        return None, []

    raw = Path(path_val).expanduser()
    candidates: list[Path] = []
    if raw.is_absolute():
        candidates.append(raw)
    else:
        candidates.extend(
            [
                BASE_DIR / raw,      # python_director/<relative>
                Path.cwd() / raw,    # current process working directory
                raw,                 # as provided
            ]
        )

    seen: set[str] = set()
    deduped: list[Path] = []
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)

    for candidate in deduped:
        if candidate.exists():
            return candidate.resolve(), deduped

    return deduped[0].resolve(), deduped


@lru_cache(maxsize=1)
def _assert_google_oauth_dns_reachable() -> None:
    import socket

    host = "oauth2.googleapis.com"
    try:
        socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise RuntimeError(
            f"Google OAuth DNS lookup failed for '{host}'. "
            "Check internet connectivity, DNS, VPN/proxy/firewall rules, and retry."
        ) from exc


def _normalize_allowed_languages(raw_languages: list[str] | None) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in raw_languages or []:
        lang = str(raw or "").strip()
        if not lang:
            continue
        key = lang.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(lang)
    return normalized


def _allowed_languages_instruction(allowed_languages: list[str]) -> str:
    if not allowed_languages:
        return ""
    languages = ", ".join(allowed_languages)
    mix_hint = (
        "Code-switching between these languages is allowed where natural."
        if len(allowed_languages) > 1
        else "Do not code-switch into any other language."
    )
    return (
        "LANGUAGE CONSTRAINTS (strict):\n"
        f"- Allowed language(s): {languages}\n"
        "- All user-facing artifact text must stay within the allowed language set.\n"
        f"- {mix_hint}\n"
        "- Keep platform conventions (chat slang, social tone) while respecting the language constraint."
    )


def _normalize_delivery_profile(value: str | None) -> str:
    normalized = (value or "standard").strip().lower()
    if normalized in {"on_demand", "ondemand", "subscription_on_demand", "burst"}:
        return "on_demand"
    return "standard"


def _normalize_story_publish_settings(
    story_mode: str | None,
    story_sub_mode: str | None,
    scheduled_start_at: datetime | None,
    tts_tier: str | None,
) -> tuple[str, str, datetime | None, str]:
    mode = (story_mode or "live").strip().lower()
    if mode not in {"live", "scheduled", "subscription"}:
        mode = "live"

    sub_mode = (story_sub_mode or "default").strip().lower()
    if sub_mode not in {"default", "on_demand"}:
        sub_mode = "default"
    if mode != "subscription":
        sub_mode = "default"

    normalized_start = _normalize_story_datetime_utc(scheduled_start_at)
    if mode != "scheduled":
        normalized_start = None

    tier = (tts_tier or "premium").strip().lower()
    if tier not in {"premium", "cheap"}:
        tier = "premium"

    return mode, sub_mode, normalized_start, tier


def _dry_run_stage_name(stage: int) -> str:
    return _DRY_RUN_STAGE_NAMES.get(stage, _DRY_RUN_STAGE_NAMES[_DRY_RUN_STAGE_MAX])


def _sanitize_target_stage(value: int | None, *, default: int) -> int:
    if value is None:
        stage = default
    else:
        stage = int(value)
    if stage < _DRY_RUN_STAGE_MIN:
        return _DRY_RUN_STAGE_MIN
    if stage > _DRY_RUN_STAGE_MAX:
        return _DRY_RUN_STAGE_MAX
    return stage


def _block_stage(block: PipelineBlock) -> int:
    if block.type in _STAGE1_BLOCK_TYPES:
        return 1
    if block.type in _STAGE2_BLOCK_TYPES:
        return 2
    return 3


def _final_block_id_for_stage(waves: list[list[PipelineBlock]], stage: int) -> str | None:
    final_block_id: str | None = None
    for wave in waves:
        for block in wave:
            if _block_stage(block) <= stage:
                final_block_id = block.id
    return final_block_id


def _on_demand_config() -> dict[str, int]:
    return dict(_ON_DEMAND_DEFAULT_CONFIG)


def _provider_has_api_key(provider: ProviderType, settings: AppSettings) -> bool:
    if provider == ProviderType.OPENROUTER:
        return bool(settings.openrouter_api_key)
    if provider == ProviderType.OPENAI:
        return bool(settings.openai_api_key)
    if provider == ProviderType.GEMINI:
        return bool(settings.gemini_api_key)
    if provider == ProviderType.ANTHROPIC:
        return bool(settings.anthropic_api_key)
    return False


def _configured_image_model(
    pipeline: PipelineDefinition,
    provider: ProviderType,
) -> str:
    model_map = getattr(pipeline, "default_image_models", {}) or {}
    return str(model_map.get(provider.value, "") or "").strip()


def _build_image_generation_candidates(
    pipeline: PipelineDefinition,
    settings: AppSettings,
) -> list[tuple[ProviderType, str]]:
    configured_provider = getattr(pipeline, "image_provider", ProviderType.GEMINI)
    if not isinstance(configured_provider, ProviderType):
        try:
            configured_provider = ProviderType(str(configured_provider))
        except ValueError:
            configured_provider = ProviderType.GEMINI

    ordered_providers = [configured_provider] + [
        provider for provider in _IMAGE_PROVIDER_ORDER if provider != configured_provider
    ]
    candidates: list[tuple[ProviderType, str]] = []
    seen: set[tuple[ProviderType, str]] = set()

    for provider in ordered_providers:
        if not _provider_has_api_key(provider, settings):
            continue
        configured_model = _configured_image_model(pipeline, provider)
        model_list: list[str] = []
        if configured_model:
            model_list.append(configured_model)
        model_list.extend(_IMAGE_MODEL_FALLBACKS.get(provider, []))

        for model in model_list:
            key = (provider, model)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(key)

    return candidates


def _short_error_message(exc: Exception, max_chars: int = 280) -> str:
    message = " ".join(str(exc).split())
    if len(message) <= max_chars:
        return message
    return message[:max_chars].rstrip() + "..."


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


def _coerce_offset_minutes(raw: Any) -> int:
    if isinstance(raw, (int, float)):
        return int(raw)
    try:
        return int(str(raw).strip())
    except Exception:
        return 0


def _normalize_story_datetime_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        local_tz = datetime.now().astimezone().tzinfo or timezone.utc
        value = value.replace(tzinfo=local_tz)
    return value.astimezone(timezone.utc)


def _derive_theme_color_hex(story_id: str, story_title: str) -> str:
    seed = f"{story_id}::{story_title}".encode("utf-8")
    digest = hashlib.sha256(seed).hexdigest()
    idx = int(digest[:8], 16) % len(_THEME_PALETTE)
    return _THEME_PALETTE[idx]


def _story_duration_minutes(story_payload: dict[str, Any]) -> int:
    max_offset = 0
    for key in [
        "journals",
        "chats",
        "emails",
        "receipts",
        "voice_notes",
        "social_posts",
        "phone_calls",
        "group_chats",
        "photo_gallery",
    ]:
        for item in story_payload.get(key, []):
            max_offset = max(max_offset, _coerce_offset_minutes(item.get("time_offset_minutes", 0)))
    return max_offset


def _voice_pool(tts_tier: str) -> list[str]:
    return _CHEAP_TTS_VOICES if tts_tier == "cheap" else _PREMIUM_TTS_VOICES


def _build_voice_map(
    story_id: str,
    voice_notes: list[dict[str, Any]],
    tts_tier: str,
    existing_map: dict[str, str] | None = None,
) -> dict[str, str]:
    voice_map = dict(existing_map or {})
    pool = _voice_pool(tts_tier)
    for note in voice_notes:
        speaker = (note.get("speaker") or "Unknown").strip() or "Unknown"
        if speaker in voice_map:
            continue
        digest = hashlib.sha256(f"{story_id}:{speaker}:{tts_tier}".encode("utf-8")).hexdigest()
        voice_map[speaker] = pool[int(digest[:8], 16) % len(pool)]
    return voice_map


def _read_audio_response_bytes(response: Any) -> bytes:
    if hasattr(response, "read"):
        data = response.read()
        if isinstance(data, bytes):
            return data
    if hasattr(response, "content") and isinstance(response.content, bytes):
        return response.content
    if isinstance(response, bytes):
        return response
    raise ValueError("TTS provider did not return audio bytes.")


def _generate_tts_bytes(
    transcript: str,
    voice_id: str,
    tts_tier: str,
    settings: AppSettings,
) -> bytes:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ImportError("openai is not installed. Run script\\director-install.cmd first.") from exc

    text = transcript.strip()
    if not text:
        raise ValueError("Transcript is empty.")

    # Premium path: OpenAI native TTS.
    if tts_tier != "cheap":
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is missing for premium TTS generation.")
        client = OpenAI(api_key=settings.openai_api_key, timeout=3600.0)
        response = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=voice_id,
            input=text,
            response_format="mp3",
        )
        return _read_audio_response_bytes(response)

    # Cheap path: prefer OpenRouter if configured, else fallback to OpenAI.
    if settings.openrouter_api_key:
        client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            timeout=3600.0,
        )
        response = client.audio.speech.create(
            model="openai/gpt-4o-mini-tts",
            voice=voice_id,
            input=text,
            response_format="mp3",
        )
        return _read_audio_response_bytes(response)

    if settings.openai_api_key:
        client = OpenAI(api_key=settings.openai_api_key, timeout=3600.0)
        response = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=voice_id,
            input=text,
            response_format="mp3",
        )
        return _read_audio_response_bytes(response)

    raise ValueError("Neither OpenRouter nor OpenAI API key is configured for cheap TTS generation.")


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


def _story_clock_from_offset(total_mins: int) -> str:
    base_hour = 9
    hours = (base_hour + (total_mins // 60)) % 24
    mins = total_mins % 60
    ampm = "AM" if hours < 12 else "PM"
    display_hour = hours if hours <= 12 else hours - 12
    if display_hour == 0:
        display_hour = 12
    return f"{display_hour:02d}:{mins:02d} {ampm}"


def _clip_text(value: str, max_chars: int = 180) -> str:
    clean = " ".join(str(value or "").split())
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 3].rstrip() + "..."


def _artifact_title(event_type: str, item: dict[str, Any], index: int) -> str:
    if event_type == "journal":
        return str(item.get("title") or f"Journal Entry {index + 1}")
    if event_type == "chat":
        return f"Chat: {item.get('senderId', 'Unknown')}"
    if event_type == "email":
        return str(item.get("subject") or f"Email {index + 1}")
    if event_type == "receipt":
        return str(item.get("merchantName") or f"Receipt {index + 1}")
    if event_type == "voice_note":
        return f"Voice: {item.get('speaker', 'Unknown')}"
    if event_type == "social_post":
        platform = item.get("platform", "social")
        handle = item.get("handle") or item.get("author") or "unknown"
        return f"{str(platform).capitalize()}: @{handle}"
    if event_type == "phone_call":
        return f"Call: {item.get('caller', '?')} -> {item.get('receiver', '?')}"
    if event_type == "group_chat":
        platform = item.get("platform", "chat")
        return f"{str(platform).capitalize()} Group: {item.get('group_name', f'Thread {index + 1}')}"
    if event_type == "photo":
        return str(item.get("subject") or f"Photo {index + 1}")
    return f"{event_type.replace('_', ' ').title()} {index + 1}"


def _artifact_text(event_type: str, item: dict[str, Any]) -> str:
    if event_type == "journal":
        return " ".join(
            part for part in [item.get("title"), item.get("body")] if isinstance(part, str) and part.strip()
        )
    if event_type == "chat":
        return str(item.get("text") or "")
    if event_type == "email":
        return " ".join(
            part for part in [item.get("subject"), item.get("body")] if isinstance(part, str) and part.strip()
        )
    if event_type == "receipt":
        return " ".join(
            part for part in [item.get("merchantName"), item.get("description")] if isinstance(part, str) and part.strip()
        )
    if event_type == "voice_note":
        return str(item.get("transcript") or "")
    if event_type == "social_post":
        return str(item.get("content") or "")
    if event_type == "phone_call":
        lines = item.get("lines") or []
        if isinstance(lines, list):
            return " ".join(
                f"{line.get('speaker', 'Unknown')}: {line.get('text', '')}"
                for line in lines
                if isinstance(line, dict)
            )
        return ""
    if event_type == "group_chat":
        messages = item.get("messages") or []
        if isinstance(messages, list):
            return " ".join(
                f"{msg.get('sender', 'Unknown')}: {msg.get('text', '')}"
                for msg in messages
                if isinstance(msg, dict)
            )
        return ""
    if event_type == "photo":
        return " ".join(
            part for part in [item.get("subject"), item.get("caption")] if isinstance(part, str) and part.strip()
        )
    return ""


def _flatten_story_artifacts(final_output: dict[str, Any]) -> list[dict[str, Any]]:
    collection_map = [
        ("journals", "journal"),
        ("chats", "chat"),
        ("emails", "email"),
        ("receipts", "receipt"),
        ("voice_notes", "voice_note"),
        ("social_posts", "social_post"),
        ("phone_calls", "phone_call"),
        ("group_chats", "group_chat"),
        ("photo_gallery", "photo"),
    ]
    flattened: list[dict[str, Any]] = []
    for collection_name, event_type in collection_map:
        items = final_output.get(collection_name, [])
        if not isinstance(items, list):
            continue
        for index, raw_item in enumerate(items):
            if not isinstance(raw_item, dict):
                continue
            time_offset = _coerce_offset_minutes(raw_item.get("time_offset_minutes", 0))
            text = _artifact_text(event_type, raw_item)
            flattened.append(
                {
                    "artifact_id": f"{event_type}_{index}",
                    "event_type": event_type,
                    "title": _artifact_title(event_type, raw_item, index),
                    "time_offset_minutes": time_offset,
                    "story_day": (time_offset // (24 * 60)) + 1,
                    "story_time": _story_clock_from_offset(time_offset),
                    "excerpt": _clip_text(text),
                    "text": text,
                    "payload": raw_item,
                }
            )
    flattened.sort(key=lambda item: (item["time_offset_minutes"], item["artifact_id"]))
    return flattened


def _stable_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _merge_unique(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for item in group:
            text = " ".join(str(item or "").split())
            if not text:
                continue
            key = text.casefold()
            if key in seen:
                continue
            seen.add(key)
            merged.append(text)
    return merged


def _signal_hits(text: str, terms: set[str]) -> int:
    lowered = text.casefold()
    return sum(1 for term in terms if term in lowered)


def _artifact_interest_score(artifact: dict[str, Any], previous_type: str | None = None) -> float:
    text = str(artifact.get("text") or "")
    event_type = str(artifact.get("event_type") or "")
    score = 2.8
    if event_type in _CONCRETE_EVIDENCE_TYPES:
        score += 2.2
    if event_type in {"voice_note", "phone_call"}:
        score += 0.6
    score += min(2.6, 0.85 * _signal_hits(text, _HIGH_SIGNAL_TERMS))
    score += min(1.5, 0.5 * _signal_hits(text, _QUESTION_TERMS))
    score += min(1.2, 0.4 * _signal_hits(text, _EMOTIONAL_TERMS))
    if "?" in text:
        score += 0.6
    if len(text) < 24:
        score -= 0.8
    elif len(text) > 260:
        score += 0.4
    if previous_type and previous_type == event_type:
        score -= 0.8
    return round(max(0.0, min(10.0, score)), 1)


def _max_repetition_streak(artifacts: list[dict[str, Any]]) -> int:
    longest = 0
    current = 0
    previous: str | None = None
    for artifact in artifacts:
        current_type = str(artifact.get("event_type") or "")
        if current_type == previous:
            current += 1
        else:
            current = 1
            previous = current_type
        longest = max(longest, current)
    return longest


def _collect_dead_zones(
    artifacts: list[dict[str, Any]],
    *,
    window_minutes: int = _HOOK_WINDOW_MINUTES,
    threshold_minutes: int = _HOOK_DEAD_ZONE_THRESHOLD,
) -> list[HookDeadZone]:
    within_window = [item for item in artifacts if item["time_offset_minutes"] <= window_minutes]
    if not within_window:
        return [
            HookDeadZone(
                start_offset_minutes=0,
                end_offset_minutes=window_minutes,
                duration_minutes=window_minutes,
                label="No opening artifacts land in the first 24 hours.",
            )
        ]

    dead_zones: list[HookDeadZone] = []
    previous_offset = 0
    for artifact in within_window:
        current_offset = int(artifact["time_offset_minutes"])
        gap = current_offset - previous_offset
        if gap >= threshold_minutes:
            dead_zones.append(
                HookDeadZone(
                    start_offset_minutes=previous_offset,
                    end_offset_minutes=current_offset,
                    duration_minutes=gap,
                    label=f"{gap} min without a meaningful drop.",
                )
            )
        previous_offset = current_offset

    trailing_gap = window_minutes - previous_offset
    if trailing_gap >= threshold_minutes:
        dead_zones.append(
            HookDeadZone(
                start_offset_minutes=previous_offset,
                end_offset_minutes=window_minutes,
                duration_minutes=trailing_gap,
                label=f"{trailing_gap} min quiet stretch before the 24h mark.",
            )
        )
    return dead_zones


def _artifact_ref_map(artifacts: list[dict[str, Any]]) -> dict[str, EvaluatedArtifactRef]:
    return {
        artifact["artifact_id"]: EvaluatedArtifactRef(
            artifact_id=artifact["artifact_id"],
            event_type=artifact["event_type"],
            title=artifact["title"],
            time_offset_minutes=artifact["time_offset_minutes"],
            story_day=artifact["story_day"],
            story_time=artifact["story_time"],
            excerpt=artifact["excerpt"],
        )
        for artifact in artifacts
    }


def _finding_severity_rank(severity: QAFindingSeverity) -> int:
    return {
        QAFindingSeverity.CRITICAL: 0,
        QAFindingSeverity.HIGH: 1,
        QAFindingSeverity.MEDIUM: 2,
        QAFindingSeverity.LOW: 3,
    }.get(severity, 4)


def _attach_refs_to_findings(
    findings: list[StoryQAFinding],
    artifact_map: dict[str, EvaluatedArtifactRef],
    *,
    pass_name: str,
) -> list[StoryQAFinding]:
    attached: list[StoryQAFinding] = []
    for finding in findings:
        refs = [artifact_map[artifact_id] for artifact_id in finding.artifact_ids if artifact_id in artifact_map]
        attached.append(
            finding.model_copy(
                update={
                    "artifact_refs": refs,
                    "pass_name": finding.pass_name or pass_name,
                }
            )
        )
    return attached


def _status_from_hook_score(score: float) -> HookReadinessStatus:
    if score >= 8.0:
        return HookReadinessStatus.READY
    if score >= 6.0:
        return HookReadinessStatus.CAUTION
    return HookReadinessStatus.HIGH_RISK


def _status_from_qa_score(score: int) -> StoryQAStatus:
    if score >= 85:
        return StoryQAStatus.STRONG
    if score >= 70:
        return StoryQAStatus.WARNING
    return StoryQAStatus.WEAK


def _evaluation_provider_bundle(
    settings: AppSettings,
    pipeline: PipelineDefinition | None,
) -> tuple[Any, ProviderType, str] | None:
    default_models = dict(getattr(pipeline, "default_models", {}) or {})
    for provider_type, fallback_model in _EVALUATION_PROVIDER_FALLBACKS:
        if not _provider_has_api_key(provider_type, settings):
            continue
        model_name = str(default_models.get(provider_type.value) or fallback_model).strip()
        if not model_name:
            continue
        try:
            provider = get_provider(provider_type, {
                "GEMINI_API_KEY": settings.gemini_api_key,
                "OPENAI_API_KEY": settings.openai_api_key,
                "OPENROUTER_API_KEY": settings.openrouter_api_key,
                "ANTHROPIC_API_KEY": settings.anthropic_api_key,
            })
            return provider, provider_type, model_name
        except Exception:
            logger.exception("Failed to initialize evaluator provider=%s", provider_type.value)
    return None


def _evaluation_config(provider_type: ProviderType, model_name: str, system_instruction: str) -> BlockConfig:
    return BlockConfig(
        provider=provider_type,
        model_name=model_name,
        use_pipeline_default_model=False,
        temperature=0.2,
        system_instruction=system_instruction,
        prompt_template="[handled directly]",
    )


def _build_deterministic_hook_report(
    run_result: RunResult,
    artifacts: list[dict[str, Any]],
) -> HookSimulationReport:
    first_24h = [artifact for artifact in artifacts if artifact["time_offset_minutes"] <= _HOOK_WINDOW_MINUTES]
    opening = first_24h[:_HOOK_ARTIFACT_LIMIT]
    if not opening:
        return HookSimulationReport(
            generated_at=datetime.now(timezone.utc).isoformat(),
            status=HookReadinessStatus.HIGH_RISK,
            overall_hook_score=0.0,
            warnings=["No opening artifacts were available to evaluate."],
            recommended_actions=[
                "Generate at least 4 early artifacts before reviewing hook readiness.",
                "Introduce a high-signal artifact in the first five drops.",
            ],
            deterministic_signals=HookSimulationDeterministicSignals(
                artifact_count_first_24h=0,
                artifact_count_first_10=0,
                dead_zones=_collect_dead_zones([]),
            ),
            evaluation_mode="deterministic",
        )

    interest_scores: list[float] = []
    previous_type: str | None = None
    timeline_beats: list[HookTimelineBeat] = []
    for artifact in opening:
        score = _artifact_interest_score(artifact, previous_type)
        note_parts: list[str] = []
        if artifact["event_type"] in _CONCRETE_EVIDENCE_TYPES:
            note_parts.append("concrete evidence")
        if _signal_hits(str(artifact["text"]), _HIGH_SIGNAL_TERMS):
            note_parts.append("high-signal language")
        if "?" in str(artifact["text"]):
            note_parts.append("open question")
        interest_scores.append(score)
        timeline_beats.append(
            HookTimelineBeat(
                artifact_id=artifact["artifact_id"],
                event_type=artifact["event_type"],
                title=artifact["title"],
                time_offset_minutes=artifact["time_offset_minutes"],
                tension_score=score,
                note=", ".join(note_parts) or "baseline beat",
            )
        )
        previous_type = artifact["event_type"]

    evidence_types = _stable_unique(
        [artifact["event_type"] for artifact in opening if artifact["event_type"] in _CONCRETE_EVIDENCE_TYPES]
    )
    repeated_type_streak = _max_repetition_streak(opening)
    dead_zones = _collect_dead_zones(first_24h)
    max_gap = max(
        [dead_zone.duration_minutes for dead_zone in dead_zones],
        default=0,
    )
    average_gap = round(
        sum(dead_zone.duration_minutes for dead_zone in dead_zones) / len(dead_zones),
        1,
    ) if dead_zones else 0.0
    first_high_interest_index = next(
        (index for index, score in enumerate(interest_scores) if score >= _HIGH_INTEREST_THRESHOLD),
        None,
    )
    second_high_interest_index = next(
        (
            index for index, score in enumerate(interest_scores)
            if index != first_high_interest_index and score >= _HIGH_INTEREST_THRESHOLD
        ),
        None,
    )
    unique_types = len({artifact["event_type"] for artifact in opening})
    emotion_hits = sum(_signal_hits(str(artifact["text"]), _EMOTIONAL_TERMS) for artifact in opening)
    question_hits = sum("?" in str(artifact["text"]) for artifact in opening)
    long_openers = sum(1 for artifact in opening[:3] if len(str(artifact["text"] or "")) > 420)
    opening_with_text = sum(1 for artifact in opening[:3] if len(str(artifact["text"] or "")) >= 40)

    hook_strength = 4.8
    hook_strength += 1.8 if first_high_interest_index == 0 else 0.0
    hook_strength += 1.2 if first_high_interest_index is not None and first_high_interest_index <= 2 else 0.0
    hook_strength += 1.0 if evidence_types else 0.0
    hook_strength += min(1.2, len(opening) / 5.0)
    hook_strength -= 1.3 if first_high_interest_index is None else 0.0
    hook_strength -= 0.5 * max(0, repeated_type_streak - 2)

    clarity = 4.8 + 1.3 * min(opening_with_text, 3) / 3.0 + 1.2 * min(unique_types, 3) / 3.0
    clarity -= 0.7 * long_openers
    clarity -= 0.5 if len(opening) < 3 else 0.0

    tension_ramp = 4.2
    if first_high_interest_index is not None:
        tension_ramp += max(0.0, 2.2 - 0.5 * first_high_interest_index)
    if second_high_interest_index is not None:
        tension_ramp += max(0.0, 1.7 - 0.25 * (second_high_interest_index - (first_high_interest_index or 0)))
    tension_ramp += min(1.0, question_hits * 0.2)
    tension_ramp -= 0.45 * len(dead_zones)

    artifact_variety = 3.4 + unique_types * 1.15 - 0.55 * max(0, repeated_type_streak - 1)
    if "photo" in evidence_types:
        artifact_variety += 0.4

    emotional_pull = 4.0 + min(2.3, emotion_hits * 0.35)
    if any(artifact["event_type"] in {"journal", "voice_note", "phone_call"} for artifact in opening):
        emotional_pull += 1.2
    if any(" i " in f" {str(artifact['text']).casefold()} " for artifact in opening):
        emotional_pull += 0.6

    last_three_scores = interest_scores[-3:] if len(interest_scores) >= 3 else interest_scores
    cliffhanger_strength = 4.3 + (sum(last_three_scores) / max(len(last_three_scores), 1) - 4.5) * 0.55
    cliffhanger_strength += min(1.2, question_hits * 0.2)
    if opening[-1]["event_type"] in _CONCRETE_EVIDENCE_TYPES:
        cliffhanger_strength += 0.8

    dead_zone_risk = 2.0
    dead_zone_risk += 1.6 if not evidence_types else 0.0
    dead_zone_risk += min(3.6, max_gap / 75.0)
    dead_zone_risk += 0.8 * max(0, repeated_type_streak - 2)
    dead_zone_risk += 0.7 * len(dead_zones)
    dead_zone_risk += 1.0 if len(opening) < 5 else 0.0

    scores = HookSimulationScores(
        hook_strength=round(max(0.0, min(10.0, hook_strength)), 1),
        clarity=round(max(0.0, min(10.0, clarity)), 1),
        tension_ramp=round(max(0.0, min(10.0, tension_ramp)), 1),
        artifact_variety=round(max(0.0, min(10.0, artifact_variety)), 1),
        emotional_pull=round(max(0.0, min(10.0, emotional_pull)), 1),
        cliffhanger_strength=round(max(0.0, min(10.0, cliffhanger_strength)), 1),
        dead_zone_risk=round(max(0.0, min(10.0, dead_zone_risk)), 1),
    )
    overall_score = round(
        (
            scores.hook_strength
            + scores.clarity
            + scores.tension_ramp
            + scores.artifact_variety
            + scores.emotional_pull
            + scores.cliffhanger_strength
            + (10.0 - scores.dead_zone_risk)
        ) / 7.0,
        1,
    )

    warnings: list[str] = []
    recommended_actions: list[str] = []
    if len(first_24h) < 5:
        warnings.append(f"Only {len(first_24h)} artifacts land in the first 24 hours.")
        recommended_actions.append("Add 2-3 more early artifacts so users feel momentum in session one.")
    if first_high_interest_index is None or first_high_interest_index >= 4:
        warnings.append("No clear high-interest artifact lands in the first five drops.")
        recommended_actions.append("Move a more suspicious or concrete artifact into the first three beats.")
    if repeated_type_streak >= 3:
        warnings.append(f"{repeated_type_streak} opening artifacts in a row use the same format.")
        recommended_actions.append("Break up repeated artifact types with a voice note, phone call, receipt, or photo.")
    if not evidence_types:
        warnings.append("The opening lacks a concrete evidence artifact such as a receipt, photo, voice note, or phone call.")
        recommended_actions.append("Introduce one concrete evidence artifact before artifact five.")
    if max_gap >= _HOOK_DEAD_ZONE_THRESHOLD:
        warnings.append(f"A {max_gap}-minute quiet stretch creates a likely dead zone in the opening.")
        recommended_actions.append("Tighten the largest opening gap or insert a short interrupting artifact.")
    if scores.clarity < 6.0:
        warnings.append("The premise takes too long to become legible in the opening sequence.")
        recommended_actions.append("Use the first two artifacts to establish who is in trouble and why it matters.")
    if scores.cliffhanger_strength < 6.0:
        recommended_actions.append("End the opening window on a sharper unanswered question or confrontation.")

    return HookSimulationReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        status=_status_from_hook_score(overall_score),
        overall_hook_score=overall_score,
        scores=scores,
        warnings=_merge_unique(warnings),
        recommended_actions=_merge_unique(recommended_actions),
        deterministic_signals=HookSimulationDeterministicSignals(
            artifact_count_first_24h=len(first_24h),
            artifact_count_first_10=len(opening),
            first_high_interest_index=first_high_interest_index,
            second_high_interest_index=second_high_interest_index,
            repeated_type_streak=repeated_type_streak,
            concrete_evidence_present=bool(evidence_types),
            evidence_artifact_types=evidence_types,
            max_gap_minutes_first_24h=max_gap,
            average_gap_minutes_first_24h=average_gap,
            dead_zones=dead_zones,
        ),
        timeline_beats=timeline_beats,
        llm_summary="",
        evaluation_mode="deterministic",
    )


def _run_hook_llm_review(
    run_result: RunResult,
    pipeline: PipelineDefinition,
    settings: AppSettings,
    artifacts: list[dict[str, Any]],
    deterministic_report: HookSimulationReport,
) -> HookSimulationLLMReview | None:
    provider_bundle = _evaluation_provider_bundle(settings, pipeline)
    if provider_bundle is None:
        return None
    provider, provider_type, model_name = provider_bundle
    opening_payload = [
        {
            "artifact_id": artifact["artifact_id"],
            "event_type": artifact["event_type"],
            "time_offset_minutes": artifact["time_offset_minutes"],
            "title": artifact["title"],
            "excerpt": artifact["excerpt"],
        }
        for artifact in artifacts[:_HOOK_ARTIFACT_LIMIT]
    ]
    prompt = json.dumps(
        {
            "story_title": run_result.final_title or (run_result.final_output or {}).get("story_title"),
            "setup": _clip_text(run_result.setup, 220),
            "opening_artifacts": opening_payload,
            "deterministic_signals": deterministic_report.deterministic_signals.model_dump(mode="json"),
            "deterministic_warnings": deterministic_report.warnings,
        },
        indent=2,
    )
    system_instruction = (
        "You are a ruthless but constructive story-hook evaluator for a found-phone narrative studio. "
        "Score the first 24 hours / first 10 artifacts only. "
        "Return JSON only. "
        "All scores must be 0-10. "
        "For dead_zone_risk, 0 means no meaningful dead-zone risk and 10 means severe dead-zone risk. "
        "Warnings and recommendations must be concrete and specific to the provided artifacts."
    )
    try:
        return provider.generate_structured_output(
            _evaluation_config(provider_type, model_name, system_instruction),
            (
                "Evaluate whether the opening would hook a new user within three minutes.\n"
                "Focus on hook strength, clarity, tension ramp, artifact variety, emotional pull, "
                "cliffhanger strength, and dead-zone risk.\n"
                f"{prompt}"
            ),
            HookSimulationLLMReview,
        )
    except Exception:
        logger.exception("Hook simulation LLM review failed run_id=%s", run_result.run_id)
        return None


def generate_hook_simulation_report(
    run_result: RunResult,
    settings: AppSettings,
    pipeline: PipelineDefinition,
) -> HookSimulationReport:
    if not isinstance(run_result.final_output, dict):
        raise ValueError("Run has no structured final artifact to evaluate.")

    artifacts = _flatten_story_artifacts(run_result.final_output)
    deterministic_report = _build_deterministic_hook_report(run_result, artifacts)
    llm_review = _run_hook_llm_review(run_result, pipeline, settings, artifacts, deterministic_report)
    if llm_review is None:
        return deterministic_report

    merged_scores = HookSimulationScores(
        hook_strength=round((deterministic_report.scores.hook_strength + llm_review.scores.hook_strength) / 2.0, 1),
        clarity=round((deterministic_report.scores.clarity + llm_review.scores.clarity) / 2.0, 1),
        tension_ramp=round((deterministic_report.scores.tension_ramp + llm_review.scores.tension_ramp) / 2.0, 1),
        artifact_variety=round((deterministic_report.scores.artifact_variety + llm_review.scores.artifact_variety) / 2.0, 1),
        emotional_pull=round((deterministic_report.scores.emotional_pull + llm_review.scores.emotional_pull) / 2.0, 1),
        cliffhanger_strength=round((deterministic_report.scores.cliffhanger_strength + llm_review.scores.cliffhanger_strength) / 2.0, 1),
        dead_zone_risk=round((deterministic_report.scores.dead_zone_risk + llm_review.scores.dead_zone_risk) / 2.0, 1),
    )
    overall_score = round(
        (
            merged_scores.hook_strength
            + merged_scores.clarity
            + merged_scores.tension_ramp
            + merged_scores.artifact_variety
            + merged_scores.emotional_pull
            + merged_scores.cliffhanger_strength
            + (10.0 - merged_scores.dead_zone_risk)
        ) / 7.0,
        1,
    )
    return deterministic_report.model_copy(
        update={
            "status": _status_from_hook_score(overall_score),
            "overall_hook_score": overall_score,
            "scores": merged_scores,
            "warnings": _merge_unique(deterministic_report.warnings, llm_review.warnings),
            "recommended_actions": _merge_unique(
                deterministic_report.recommended_actions,
                llm_review.recommended_actions,
            ),
            "llm_summary": llm_review.summary,
            "evaluation_mode": "deterministic+llm",
        }
    )


def _extract_continuity_audit_payload(run_result: RunResult) -> dict[str, Any] | None:
    for value in run_result.outputs.values():
        candidate = value.model_dump(mode="json") if hasattr(value, "model_dump") else value
        if not isinstance(candidate, dict):
            continue
        if "continuity_score" in candidate and "contradictions" in candidate:
            return candidate
    return None


def _severity_from_score(score: int, *, critical_cutoff: int = 45, high_cutoff: int = 65) -> QAFindingSeverity:
    if score < critical_cutoff:
        return QAFindingSeverity.CRITICAL
    if score < high_cutoff:
        return QAFindingSeverity.HIGH
    return QAFindingSeverity.MEDIUM


def _finding(
    severity: QAFindingSeverity,
    category: str,
    message: str,
    recommendation: str = "",
    artifact_ids: list[str] | None = None,
) -> StoryQAFinding:
    return StoryQAFinding(
        severity=severity,
        category=category,
        message=message,
        recommendation=recommendation,
        artifact_ids=list(artifact_ids or []),
    )


def _pass_status(score: int, findings: list[StoryQAFinding]) -> QAPassStatus:
    if score < 55 or any(finding.severity == QAFindingSeverity.CRITICAL for finding in findings):
        return QAPassStatus.FAIL
    if score < 75 or any(finding.severity == QAFindingSeverity.HIGH for finding in findings):
        return QAPassStatus.WARNING
    return QAPassStatus.PASS


def _top_similar_pairs(
    artifacts: list[dict[str, Any]],
    limit: int = 3,
) -> list[tuple[dict[str, Any], dict[str, Any], float]]:
    pairs: list[tuple[dict[str, Any], dict[str, Any], float]] = []
    textful = [artifact for artifact in artifacts if len(str(artifact.get("text") or "")) >= 40]
    for left_index, left in enumerate(textful):
        for right in textful[left_index + 1:]:
            ratio = SequenceMatcher(None, str(left["text"]).casefold(), str(right["text"]).casefold()).ratio()
            if ratio >= 0.82:
                pairs.append((left, right, ratio))
    pairs.sort(key=lambda item: item[2], reverse=True)
    return pairs[:limit]


def _opening_hook_pass(hook_report: HookSimulationReport) -> StoryQAPassResult:
    score = int(round(hook_report.overall_hook_score * 10))
    findings: list[StoryQAFinding] = []
    anchor_ids = [beat.artifact_id for beat in hook_report.timeline_beats[:3]]
    for warning in hook_report.warnings[:3]:
        findings.append(
            _finding(
                _severity_from_score(score),
                "opening_hook",
                warning,
                hook_report.recommended_actions[0] if hook_report.recommended_actions else "",
                anchor_ids,
            )
        )
    summary = (
        hook_report.llm_summary
        or f"Opening hook scored {hook_report.overall_hook_score}/10 with status {hook_report.status.value}."
    )
    return StoryQAPassResult(
        pass_name="OpeningHookPass",
        label="Opening Hook",
        status=_pass_status(score, findings),
        score=score,
        findings=findings,
        recommendations=list(hook_report.recommended_actions[:4]),
        summary=summary,
    )


def _continuity_pass(run_result: RunResult) -> StoryQAPassResult:
    audit = _extract_continuity_audit_payload(run_result)
    findings: list[StoryQAFinding] = []
    recommendations: list[str] = []
    if audit is None:
        return StoryQAPassResult(
            pass_name="ContinuityPass",
            label="Continuity",
            status=QAPassStatus.WARNING,
            score=68,
            findings=[
                _finding(
                    QAFindingSeverity.MEDIUM,
                    "continuity",
                    "No dedicated continuity audit output was available for this run.",
                    "Re-run the continuity auditor block or review contradictions manually.",
                )
            ],
            recommendations=["Run a continuity-focused audit before publishing."],
            summary="Continuity score is provisional because no upstream continuity audit output was found.",
        )

    contradictions = audit.get("contradictions") or []
    for contradiction in contradictions[:4]:
        if not isinstance(contradiction, dict):
            continue
        severity = str(contradiction.get("severity") or "medium").lower()
        findings.append(
            _finding(
                QAFindingSeverity.CRITICAL if severity == "critical" else QAFindingSeverity.HIGH if severity == "high" else QAFindingSeverity.MEDIUM,
                str(contradiction.get("category") or "continuity"),
                str(contradiction.get("description") or "Continuity issue detected."),
                str(contradiction.get("fix_instruction") or ""),
            )
        )
    for note in audit.get("motivation_breaks") or []:
        recommendations.append(str(note))
    score = int(max(0, min(100, audit.get("continuity_score", 70))))
    return StoryQAPassResult(
        pass_name="ContinuityPass",
        label="Continuity",
        status=_pass_status(score, findings),
        score=score,
        findings=findings,
        recommendations=_merge_unique(recommendations, [str(audit.get("release_recommendation") or "")]),
        summary=str(audit.get("release_recommendation") or "Continuity audit integrated into QA."),
    )


def _character_voice_pass(artifacts: list[dict[str, Any]]) -> StoryQAPassResult:
    findings: list[StoryQAFinding] = []
    recommendations: list[str] = []
    speaker_like_types = [
        artifact
        for artifact in artifacts
        if artifact["event_type"] in {"chat", "voice_note", "phone_call", "group_chat", "social_post"}
    ]
    unique_speakers = set()
    for artifact in speaker_like_types:
        payload = artifact["payload"]
        for key in ("senderId", "speaker", "caller", "author", "handle"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                unique_speakers.add(value.strip().casefold())
    repeated_openings = sum(
        1
        for left, right, ratio in _top_similar_pairs(speaker_like_types, limit=6)
        if ratio >= 0.9 and left["event_type"] == right["event_type"]
    )
    score = 88
    if len(unique_speakers) < 3:
        score -= 18
        findings.append(
            _finding(
                QAFindingSeverity.HIGH,
                "character_consistency",
                "Too few distinct voices appear across conversational artifacts.",
                "Give at least one more character a strongly differentiated artifact voice early.",
            )
        )
    if repeated_openings >= 2:
        score -= 14
        findings.append(
            _finding(
                QAFindingSeverity.MEDIUM,
                "character_consistency",
                "Multiple conversational artifacts read too similarly, which flattens character voice.",
                "Vary syntax, pacing, and emotional framing between characters.",
            )
        )
    if any(artifact["event_type"] == "journal" for artifact in artifacts) and not speaker_like_types:
        score -= 10
        recommendations.append("Balance introspective artifacts with more dialog-driven voice surfaces.")
    return StoryQAPassResult(
        pass_name="CharacterVoicePass",
        label="Character Voice",
        status=_pass_status(score, findings),
        score=max(0, score),
        findings=findings,
        recommendations=_merge_unique(recommendations),
        summary="Character voice checks look for differentiated speakers and non-generic conversational texture.",
    )


def _artifact_diversity_pass(
    artifacts: list[dict[str, Any]],
    hook_report: HookSimulationReport,
) -> StoryQAPassResult:
    findings: list[StoryQAFinding] = []
    recommendations: list[str] = []
    counts = Counter(artifact["event_type"] for artifact in artifacts)
    dominant_count = max(counts.values(), default=0)
    unique_types = len(counts)
    score = min(100, 34 + unique_types * 9 + (8 if any(t in counts for t in _CONCRETE_EVIDENCE_TYPES) else 0))
    if dominant_count > max(4, len(artifacts) // 2):
        score -= 18
        dominant_type = counts.most_common(1)[0][0]
        findings.append(
            _finding(
                QAFindingSeverity.HIGH,
                "artifact_usefulness",
                f"{dominant_type.replace('_', ' ').title()} artifacts dominate the run and reduce texture.",
                "Swap some repeated exposition artifacts for evidence, dialog, or media-driven beats.",
            )
        )
    if unique_types < 4:
        score -= 16
        findings.append(
            _finding(
                QAFindingSeverity.HIGH,
                "artifact_usefulness",
                "The run uses too few artifact formats to feel like a rich phone-native story.",
                "Add at least one audio, evidence, or public-facing artifact type.",
            )
        )
    if not hook_report.deterministic_signals.concrete_evidence_present:
        score -= 12
        recommendations.append("Introduce a receipt, phone call, voice note, or photo before publish.")
    if "photo" not in counts:
        recommendations.append("Consider adding a photo or visual clue opportunity to improve sensory variety.")
    if "voice_note" not in counts:
        recommendations.append("Add a voice note if the emotional beats need more immediacy.")
    return StoryQAPassResult(
        pass_name="ArtifactDiversityPass",
        label="Artifact Diversity",
        status=_pass_status(score, findings),
        score=max(0, min(100, score)),
        findings=findings,
        recommendations=_merge_unique(recommendations),
        summary="Artifact diversity measures whether the story uses the phone-native canvas instead of repeating one format.",
    )


def _redundancy_pass(artifacts: list[dict[str, Any]]) -> StoryQAPassResult:
    findings: list[StoryQAFinding] = []
    recommendations: list[str] = []
    score = 90
    for left, right, ratio in _top_similar_pairs(artifacts):
        score -= 10
        findings.append(
            _finding(
                QAFindingSeverity.MEDIUM if ratio < 0.9 else QAFindingSeverity.HIGH,
                "redundancy",
                f"{left['title']} and {right['title']} feel near-duplicate in content or exposition.",
                "Compress or rewrite one of the overlapping artifacts so it adds new information.",
                [left["artifact_id"], right["artifact_id"]],
            )
        )
    repeated_streak = _max_repetition_streak(artifacts[:10])
    if repeated_streak >= 3:
        score -= 8
        recommendations.append("Break long same-format streaks so each drop changes the reading experience.")
    return StoryQAPassResult(
        pass_name="RedundancyPass",
        label="Redundancy",
        status=_pass_status(score, findings),
        score=max(0, score),
        findings=findings,
        recommendations=_merge_unique(recommendations),
        summary="Redundancy checks look for duplicated exposition, repeated beats, and same-format drag.",
    )


def _schema_pass(artifacts: list[dict[str, Any]]) -> StoryQAPassResult:
    findings: list[StoryQAFinding] = []
    score = 100
    for artifact in artifacts:
        payload = artifact["payload"]
        event_type = artifact["event_type"]
        missing_fields: list[str] = []
        if event_type == "journal":
            if not str(payload.get("title") or "").strip():
                missing_fields.append("title")
            if not str(payload.get("body") or "").strip():
                missing_fields.append("body")
        elif event_type == "chat":
            if not str(payload.get("text") or "").strip():
                missing_fields.append("text")
        elif event_type == "email":
            if not str(payload.get("subject") or "").strip():
                missing_fields.append("subject")
            if not str(payload.get("body") or "").strip():
                missing_fields.append("body")
        elif event_type == "voice_note":
            if not str(payload.get("transcript") or "").strip():
                missing_fields.append("transcript")
        elif event_type == "phone_call":
            if not isinstance(payload.get("lines"), list) or not payload.get("lines"):
                missing_fields.append("lines")
        elif event_type == "group_chat":
            if not isinstance(payload.get("messages"), list) or not payload.get("messages"):
                missing_fields.append("messages")
        elif event_type == "photo":
            if not str(payload.get("subject") or "").strip():
                missing_fields.append("subject")
        if missing_fields:
            score -= 16
            findings.append(
                _finding(
                    QAFindingSeverity.CRITICAL,
                    "schema_correctness",
                    f"{artifact['title']} is missing required fields: {', '.join(missing_fields)}.",
                    "Fix the malformed artifact before publish.",
                    [artifact["artifact_id"]],
                )
            )
    return StoryQAPassResult(
        pass_name="SchemaPass",
        label="Schema",
        status=_pass_status(score, findings),
        score=max(0, score),
        findings=findings,
        recommendations=["Fix any malformed artifacts before publishing."] if findings else [],
        summary="Schema checks validate required content fields and basic artifact integrity.",
    )


def _run_story_qa_llm_pass(
    run_result: RunResult,
    pipeline: PipelineDefinition,
    settings: AppSettings,
    pass_result: StoryQAPassResult,
    artifacts: list[dict[str, Any]],
) -> StoryQAPassReview | None:
    if pass_result.pass_name == "SchemaPass":
        return None
    provider_bundle = _evaluation_provider_bundle(settings, pipeline)
    if provider_bundle is None:
        return None
    provider, provider_type, model_name = provider_bundle
    artifact_payload = [
        {
            "artifact_id": artifact["artifact_id"],
            "event_type": artifact["event_type"],
            "time_offset_minutes": artifact["time_offset_minutes"],
            "title": artifact["title"],
            "excerpt": artifact["excerpt"],
        }
        for artifact in artifacts[:18]
    ]
    continuity_audit = _extract_continuity_audit_payload(run_result)
    prompt = json.dumps(
        {
            "story_title": run_result.final_title or (run_result.final_output or {}).get("story_title"),
            "setup": _clip_text(run_result.setup, 220),
            "pass_name": pass_result.pass_name,
            "deterministic_summary": pass_result.summary,
            "deterministic_findings": [finding.model_dump(mode="json") for finding in pass_result.findings],
            "artifacts": artifact_payload,
            "continuity_audit": continuity_audit,
        },
        indent=2,
    )
    system_instruction = (
        "You are a meticulous narrative QA reviewer for a mobile found-phone story studio. "
        "Evaluate only the requested pass. "
        "Return JSON only with a 0-100 score, specific findings, and precise rewrite recommendations. "
        "When citing artifacts, use only artifact_ids that exist in the provided list."
    )
    try:
        return provider.generate_structured_output(
            _evaluation_config(provider_type, model_name, system_instruction),
            (
                f"Review this run for {pass_result.label}. "
                "Findings must be actionable for a writer or engineer. "
                f"{prompt}"
            ),
            StoryQAPassReview,
        )
    except Exception:
        logger.exception("Story QA LLM pass failed run_id=%s pass=%s", run_result.run_id, pass_result.pass_name)
        return None


def generate_story_qa_report(
    run_result: RunResult,
    settings: AppSettings,
    pipeline: PipelineDefinition,
    *,
    hook_report: HookSimulationReport | None = None,
) -> StoryQAReport:
    if not isinstance(run_result.final_output, dict):
        raise ValueError("Run has no structured final artifact to evaluate.")

    artifacts = _flatten_story_artifacts(run_result.final_output)
    artifact_map = _artifact_ref_map(artifacts)
    resolved_hook_report = hook_report or run_result.hook_simulation or generate_hook_simulation_report(
        run_result,
        settings,
        pipeline,
    )

    passes: list[StoryQAPassResult] = [
        _opening_hook_pass(resolved_hook_report),
        _continuity_pass(run_result),
        _character_voice_pass(artifacts),
        _artifact_diversity_pass(artifacts, resolved_hook_report),
        _redundancy_pass(artifacts),
        _schema_pass(artifacts),
    ]

    llm_used = False
    merged_passes: list[StoryQAPassResult] = []
    for pass_result in passes:
        llm_review = _run_story_qa_llm_pass(run_result, pipeline, settings, pass_result, artifacts)
        if llm_review is None:
            merged_pass = pass_result
        else:
            llm_used = True
            merged_score = int(round((pass_result.score + llm_review.score) / 2.0))
            merged_findings = _attach_refs_to_findings(
                pass_result.findings + llm_review.findings,
                artifact_map,
                pass_name=pass_result.pass_name,
            )
            merged_pass = pass_result.model_copy(
                update={
                    "score": merged_score,
                    "status": _pass_status(merged_score, merged_findings),
                    "findings": merged_findings,
                    "recommendations": _merge_unique(pass_result.recommendations, llm_review.recommendations),
                    "summary": llm_review.summary or pass_result.summary,
                }
            )
        if llm_review is None:
            merged_pass = merged_pass.model_copy(
                update={
                    "findings": _attach_refs_to_findings(merged_pass.findings, artifact_map, pass_name=merged_pass.pass_name),
                }
            )
        merged_passes.append(merged_pass)

    aggregate_findings = sorted(
        [finding for pass_result in merged_passes for finding in pass_result.findings],
        key=lambda finding: (_finding_severity_rank(finding.severity), finding.category, finding.message),
    )
    aggregate_recommendations = _merge_unique(*[pass_result.recommendations for pass_result in merged_passes])
    overall_score = int(round(sum(pass_result.score for pass_result in merged_passes) / max(len(merged_passes), 1)))
    blockers: list[str] = []
    schema_result = next((pass_result for pass_result in merged_passes if pass_result.pass_name == "SchemaPass"), None)
    continuity_result = next((pass_result for pass_result in merged_passes if pass_result.pass_name == "ContinuityPass"), None)
    opening_result = next((pass_result for pass_result in merged_passes if pass_result.pass_name == "OpeningHookPass"), None)
    if schema_result and schema_result.status == QAPassStatus.FAIL:
        blockers.append("Schema pass failed; malformed artifacts should be fixed before publish.")
    if continuity_result and any(finding.severity == QAFindingSeverity.CRITICAL for finding in continuity_result.findings):
        blockers.append("Continuity audit found a critical contradiction in the run.")
    if opening_result and resolved_hook_report.overall_hook_score < 5.0:
        blockers.append("Opening hook is below the minimum 5/10 threshold.")

    return StoryQAReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        status=_status_from_qa_score(overall_score),
        score=overall_score,
        findings=aggregate_findings,
        recommended_fixes=aggregate_recommendations,
        passes=merged_passes,
        blockers=blockers,
        evaluation_mode="deterministic+llm" if llm_used else "deterministic",
    )


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

            elif block.type == BlockType.TTS_GENERATOR:
                if not block.input_blocks:
                    raise ValueError("TTS Generator requires an input block.")
                input_id = block.input_blocks[0]
                if input_id not in outputs:
                    raise ValueError(f"TTS Generator dependent block {input_id} output not found.")

                import copy
                source_payload = copy.deepcopy(outputs[input_id])
                if hasattr(source_payload, "model_dump"):
                    source_payload = source_payload.model_dump()
                output = generate_block_tts(
                    progress.run_id,
                    source_payload,
                    self.settings,
                    tts_tier=getattr(progress, "tts_tier", "premium"),
                    story_id_seed=progress.run_id,
                    force_regenerate=False,
                    existing_voice_map=source_payload.get("voice_map") if isinstance(source_payload, dict) else None,
                )

            elif block.type == BlockType.IMAGE_PROMPT_DIRECTOR:
                # Run the LLM call to get the patch, then merge it into the upstream StoryGenerated.
                # The merged result is stored in outputs[block.id] so IMAGE_GENERATOR reads a full payload.
                provider = get_provider(effective_config.provider, self._api_keys())
                patch: StoryGeneratedImagePatch = provider.generate_structured_output(
                    effective_config, contents, StoryGeneratedImagePatch
                )

                # Locate the upstream StoryGenerated (first input block)
                upstream_id = block.input_blocks[0] if block.input_blocks else None
                import copy
                base: dict = {}
                if upstream_id and upstream_id in outputs:
                    base = copy.deepcopy(outputs[upstream_id])
                    if hasattr(base, "model_dump"):
                        base = base.model_dump()

                # Apply headline prompt
                if patch.headline_image_prompt:
                    base["headline_image_prompt"] = patch.headline_image_prompt

                # Apply per-artifact patches
                for ap in patch.artifact_patches:
                    items = base.get(ap.collection, [])
                    if 0 <= ap.index < len(items):
                        items[ap.index]["image_prompt"] = ap.image_prompt

                # Add gallery photos
                base["photo_gallery"] = [
                    p.model_dump() if hasattr(p, "model_dump") else p
                    for p in patch.photo_gallery
                ]

                output = base

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
        allowed_languages: list[str] | None = None,
        staged_workflow: bool = False,
        target_dry_run_stage: int | None = None,
        delivery_profile: str = "standard",
        story_mode: str = "live",
        story_sub_mode: str = "default",
        scheduled_start_at: datetime | None = None,
        tts_tier: str = "premium",
    ) -> RunResult:
        run_id = run_id or f"run_{int(time.time())}"
        started_at = datetime.now(timezone.utc)
        run_dir = RUNS_DIR / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        normalized_languages = _normalize_allowed_languages(allowed_languages)
        normalized_delivery_profile = _normalize_delivery_profile(delivery_profile)
        (
            normalized_story_mode,
            normalized_story_sub_mode,
            normalized_scheduled_start_at,
            normalized_tts_tier,
        ) = _normalize_story_publish_settings(
            story_mode,
            story_sub_mode,
            scheduled_start_at,
            tts_tier,
        )
        run_staged_workflow = bool(staged_workflow)
        stage_default = _DRY_RUN_STAGE_MIN if run_staged_workflow else _DRY_RUN_STAGE_MAX
        requested_stage = _sanitize_target_stage(target_dry_run_stage, default=stage_default)

        # Keep the original definition for snapshotting (seed must not be baked in)
        original_definition = definition

        # Inject seed prompt/tags/language constraints into brainstorm + generation blocks.
        if seed_prompt or tags or normalized_languages or normalized_delivery_profile == "on_demand":
            injected_parts: list[str] = []
            if seed_prompt:
                injected_parts.append(f"STORY SEED (use as creative inspiration):\n{seed_prompt}")
            if tags:
                injected_parts.append(f"REQUIRED THEMES / TAGS: {', '.join(tags)}")
            language_instruction = _allowed_languages_instruction(normalized_languages)
            if language_instruction:
                injected_parts.append(language_instruction)
            if normalized_delivery_profile == "on_demand":
                injected_parts.append(
                    "DELIVERY PROFILE: ON-DEMAND BURST SUBSCRIPTION.\n"
                    "- Build the narrative in compact flurries suitable for active user sessions.\n"
                    "- Prefer micro-clusters of 3-8 artifacts that unfold across 6-12 in-story minutes.\n"
                    "- Between clusters, leave a strong hook that motivates return sessions."
                )
            prefix = "\n\n".join(injected_parts) + "\n\n"

            import copy as _copy
            definition = _copy.deepcopy(definition)
            creative_injected = False
            for block in definition.blocks:
                if block.enabled and block.type == BlockType.CREATIVE_OUTLINER and not creative_injected:
                    block.config.prompt_template = prefix + block.config.prompt_template
                    creative_injected = True
                    logger.info(
                        "Injected seed/tags/languages into block id=%s seed_len=%s tags=%s languages=%s",
                        block.id,
                        len(seed_prompt or ""),
                        tags,
                        normalized_languages,
                    )
                elif block.enabled and block.type == BlockType.GENERATOR and language_instruction:
                    block.config.prompt_template = f"{language_instruction}\n\n{block.config.prompt_template}"
                    logger.info(
                        "Injected allowed_languages into generator block id=%s languages=%s",
                        block.id,
                        normalized_languages,
                    )

        waves = self._execution_waves(definition)
        selected_waves: list[list[PipelineBlock]] = []
        for wave in waves:
            filtered = [block for block in wave if _block_stage(block) <= requested_stage]
            if filtered:
                selected_waves.append(filtered)
        # Pre-compute block_sequence from selected waves (deterministic, wave order preserved)
        block_sequence = [b.id for wave in selected_waves for b in wave]

        progress = RunProgress(
            run_id=run_id,
            timestamp=started_at.isoformat(),
            pipeline_name=definition.name,
            status=RunStatus.RUNNING,
            block_count=len(block_sequence),
            block_sequence=block_sequence,
            started_at=started_at.isoformat(),
            seed_prompt=seed_prompt or None,
            tags=list(tags or []),
            allowed_languages=normalized_languages,
            dry_run_stage=requested_stage,
            dry_run_stage_name=_dry_run_stage_name(requested_stage),
            awaiting_stage_approval=False,
            staged_workflow=run_staged_workflow,
            delivery_profile=normalized_delivery_profile,
            deployment_stage="dry_run",
            story_mode=normalized_story_mode,
            story_sub_mode=normalized_story_sub_mode,
            scheduled_start_at=normalized_scheduled_start_at,
            tts_tier=normalized_tts_tier,
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
            len(selected_waves),
            run_dir,
        )
        _persist_progress()

        outputs: dict[str, Any] = {}
        traces: dict[str, BlockTrace] = {}
        provider_summary: Counter[str] = Counter()
        execution_order: list[str] = []
        lock = threading.Lock()

        try:
            for wave in selected_waves:
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
            progress.awaiting_stage_approval = bool(
                run_staged_workflow and requested_stage < _DRY_RUN_STAGE_MAX
            )
        except Exception as exc:
            error_msg = str(exc)
            logger.exception("Run failed run_id=%s", run_id)
            progress.status = RunStatus.FAILED
            progress.error_message = error_msg
            progress.completed_at = datetime.now(timezone.utc).isoformat()
            progress.awaiting_stage_approval = False
            _persist_progress()

        # Determine final output from the highest block completed in the requested stage.
        final_block_id = _final_block_id_for_stage(waves, requested_stage)
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
            allowed_languages=normalized_languages,
            setup=setup_val,
            characters=characters_val,
            outputs={block_id: _serialize_output(value) for block_id, value in outputs.items()},
            final_output=final_output,
            block_sequence=block_sequence,
            block_traces=traces,
            timeline=progress.timeline,
            stats=progress.stats,
            dry_run_stage=requested_stage,
            dry_run_stage_name=_dry_run_stage_name(requested_stage),
            awaiting_stage_approval=progress.awaiting_stage_approval,
            staged_workflow=run_staged_workflow,
            delivery_profile=normalized_delivery_profile,
            deployment_stage="dry_run",
            story_mode=normalized_story_mode,
            story_sub_mode=normalized_story_sub_mode,
            scheduled_start_at=normalized_scheduled_start_at,
            tts_tier=normalized_tts_tier,
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

    def advance_run_stage(
        self,
        run_id: str,
        *,
        target_dry_run_stage: int | None = None,
        progress_callback: Any | None = None,
    ) -> RunProgress:
        run_dir = RUNS_DIR / run_id
        progress = load_run_progress(run_id)
        if progress.status == RunStatus.RUNNING:
            raise ValueError("Run is currently active. Wait for it to finish before advancing stages.")

        snapshot_path = run_dir / PIPELINE_SNAPSHOT_FILENAME
        if not snapshot_path.exists():
            raise FileNotFoundError(f"Pipeline snapshot not found for run '{run_id}'")
        definition = PipelineDefinition.model_validate_json(snapshot_path.read_text(encoding="utf-8"))

        current_stage = _sanitize_target_stage(
            getattr(progress, "dry_run_stage", _DRY_RUN_STAGE_MAX),
            default=_DRY_RUN_STAGE_MAX,
        )
        if not bool(getattr(progress, "staged_workflow", False)):
            raise ValueError("This run was not started in staged workflow mode.")

        requested_stage = _sanitize_target_stage(
            target_dry_run_stage,
            default=current_stage + 1,
        )
        if requested_stage <= current_stage:
            raise ValueError(
                f"Requested stage ({requested_stage}) must be greater than current stage ({current_stage})."
            )

        block_map = {b.id: b for b in definition.blocks if b.enabled}

        outputs: dict[str, Any] = {}
        for bid, trace in progress.block_traces.items():
            if trace.status != BlockExecutionStatus.SUCCEEDED:
                continue
            json_path = run_dir / f"{bid}.json"
            txt_path = run_dir / f"{bid}.txt"
            if json_path.exists():
                outputs[bid] = json.loads(json_path.read_text(encoding="utf-8"))
            elif txt_path.exists():
                outputs[bid] = txt_path.read_text(encoding="utf-8")

        eligible_ids = {
            bid
            for bid, block in block_map.items()
            if _block_stage(block) <= requested_stage
        }
        advance_set: set[str] = set()
        for bid in eligible_ids:
            trace = progress.block_traces.get(bid)
            if trace is None or trace.status != BlockExecutionStatus.SUCCEEDED:
                advance_set.add(bid)

        traces: dict[str, BlockTrace] = dict(progress.block_traces)
        for bid in advance_set:
            if bid in progress.block_traces:
                trace = progress.block_traces[bid]
                trace.status = BlockExecutionStatus.PENDING
                trace.output = None
                trace.error_message = None
                trace.error_traceback = None
                trace.started_at = None
                trace.completed_at = None
                trace.elapsed_ms = None
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
        traces = dict(progress.block_traces)

        progress.status = RunStatus.RUNNING
        progress.error_message = None
        progress.completed_at = None
        progress.awaiting_stage_approval = False

        def _persist_progress():
            save_run_progress(progress)
            if progress_callback:
                progress_callback(progress)

        _persist_progress()

        completed_deps: set[str] = set(outputs.keys())
        waves: list[list[PipelineBlock]] = []
        remaining = set(advance_set)
        while remaining:
            wave = [
                block_map[bid]
                for bid in sorted(remaining)
                if all(dep in completed_deps or dep not in block_map for dep in block_map[bid].input_blocks)
            ]
            if not wave:
                raise ValueError("Stage advance has unresolvable dependencies.")
            for block in wave:
                completed_deps.add(block.id)
                remaining.discard(block.id)
            waves.append(wave)

        provider_summary: Counter[str] = Counter()
        execution_order: list[str] = []
        lock = threading.Lock()

        try:
            for wave in waves:
                if len(wave) == 1:
                    self._run_one_block(
                        wave[0],
                        definition,
                        outputs,
                        run_dir,
                        lock,
                        traces,
                        progress,
                        _persist_progress,
                        provider_summary,
                        execution_order,
                    )
                else:
                    errors: list[tuple[str, BaseException]] = []
                    with ThreadPoolExecutor(max_workers=len(wave)) as executor:
                        future_map = {
                            executor.submit(
                                self._run_one_block,
                                block,
                                definition,
                                outputs,
                                run_dir,
                                lock,
                                traces,
                                progress,
                                _persist_progress,
                                provider_summary,
                                execution_order,
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
                        raise RuntimeError(f"Stage advance block '{block_id}' failed: {exc}") from exc

            progress.status = RunStatus.SUCCEEDED
            progress.completed_at = datetime.now(timezone.utc).isoformat()
            progress.dry_run_stage = requested_stage
            progress.dry_run_stage_name = _dry_run_stage_name(requested_stage)
            progress.awaiting_stage_approval = requested_stage < _DRY_RUN_STAGE_MAX
        except Exception as exc:
            logger.exception("Stage advance failed run_id=%s target_stage=%s", run_id, requested_stage)
            progress.status = RunStatus.FAILED
            progress.error_message = str(exc)
            progress.completed_at = datetime.now(timezone.utc).isoformat()
            progress.awaiting_stage_approval = False
            _persist_progress()
            raise

        all_waves = self._execution_waves(definition)
        progress.block_sequence = [
            block.id
            for wave in all_waves
            for block in wave
            if _block_stage(block) <= requested_stage
        ]
        progress.block_count = len(progress.block_sequence)
        final_block_id = _final_block_id_for_stage(all_waves, requested_stage)
        final_output = _serialize_output(outputs.get(final_block_id)) if final_block_id else None
        final_metrics = _story_metrics(final_output if isinstance(final_output, dict) else None)
        progress.final_title = final_output.get("story_title") if isinstance(final_output, dict) else progress.final_title
        progress.final_metrics = final_metrics
        progress.timeline = derive_story_timeline(final_output)
        progress.stats = calculate_run_stats(traces, final_output)
        _persist_progress()

        try:
            old_result = load_run_result(run_id)
            seed_prompt = old_result.seed_prompt
            run_tags = old_result.tags
            allowed_languages = old_result.allowed_languages
            setup_val = old_result.setup
            characters_val = old_result.characters
            timestamp = old_result.timestamp
            story_id = old_result.story_id
            deployment_stage = old_result.deployment_stage
            delivery_profile = old_result.delivery_profile
            story_mode = old_result.story_mode
            story_sub_mode = old_result.story_sub_mode
            scheduled_start_at = old_result.scheduled_start_at
            tts_tier = old_result.tts_tier
        except Exception:
            seed_prompt = progress.seed_prompt
            run_tags = progress.tags
            allowed_languages = progress.allowed_languages
            setup_val = ""
            characters_val = []
            timestamp = progress.timestamp
            story_id = None
            deployment_stage = progress.deployment_stage
            delivery_profile = progress.delivery_profile
            story_mode = progress.story_mode
            story_sub_mode = progress.story_sub_mode
            scheduled_start_at = progress.scheduled_start_at
            tts_tier = progress.tts_tier

        if not setup_val or not characters_val:
            for value in outputs.values():
                if isinstance(value, dict):
                    if not characters_val and isinstance(value.get("characters"), list):
                        characters_val = value["characters"]
                    if not setup_val and "core_conflict" in value:
                        setup_val = value["core_conflict"]

        if not provider_summary:
            provider_summary = Counter(
                trace.provider.value
                for trace in traces.values()
                if trace.status == BlockExecutionStatus.SUCCEEDED
            )

        result = RunResult(
            run_id=run_id,
            timestamp=timestamp,
            pipeline_name=definition.name,
            status=progress.status,
            error_message=progress.error_message,
            final_title=progress.final_title,
            block_count=len([t for t in traces.values() if t.status == BlockExecutionStatus.SUCCEEDED]),
            provider_summary=dict(provider_summary),
            artifact_counts={"blocks": len(traces), "files": len(list(run_dir.iterdir()))},
            final_metrics=final_metrics,
            mode="dry_run",
            seed_prompt=seed_prompt or None,
            tags=list(run_tags or []),
            allowed_languages=list(allowed_languages or []),
            setup=setup_val,
            characters=characters_val,
            outputs={bid: _serialize_output(v) for bid, v in outputs.items()},
            final_output=final_output,
            block_sequence=list(progress.block_sequence),
            block_traces=traces,
            timeline=progress.timeline,
            stats=progress.stats,
            story_id=story_id,
            dry_run_stage=requested_stage,
            dry_run_stage_name=_dry_run_stage_name(requested_stage),
            awaiting_stage_approval=progress.awaiting_stage_approval,
            staged_workflow=True,
            delivery_profile=delivery_profile or progress.delivery_profile,
            deployment_stage=deployment_stage or "dry_run",
            story_mode=story_mode or progress.story_mode,
            story_sub_mode=story_sub_mode or progress.story_sub_mode,
            scheduled_start_at=scheduled_start_at or progress.scheduled_start_at,
            tts_tier=tts_tier or progress.tts_tier,
        )
        save_run_result(result, definition)
        return progress

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
                dry_run_stage=progress.dry_run_stage,
                dry_run_stage_name=progress.dry_run_stage_name,
                awaiting_stage_approval=progress.awaiting_stage_approval,
                staged_workflow=progress.staged_workflow,
                delivery_profile=progress.delivery_profile,
                deployment_stage=progress.deployment_stage,
                story_mode=progress.story_mode,
                story_sub_mode=progress.story_sub_mode,
                scheduled_start_at=progress.scheduled_start_at,
                tts_tier=progress.tts_tier,
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

def generate_image_with_fallback(
    prompt: str,
    pipeline: PipelineDefinition,
    settings: AppSettings,
    *,
    provider_cache: dict[ProviderType, Any] | None = None,
    preferred_candidate: tuple[ProviderType, str] | None = None,
) -> tuple[bytes, tuple[ProviderType, str]]:
    candidates = _build_image_generation_candidates(pipeline, settings)
    if not candidates:
        raise ValueError(
            "No image generation provider is configured with a usable API key/model. "
            "Add an image-capable key in Settings."
        )

    ordered_candidates = list(candidates)
    if preferred_candidate and preferred_candidate in ordered_candidates:
        ordered_candidates.remove(preferred_candidate)
        ordered_candidates.insert(0, preferred_candidate)

    cache = provider_cache if provider_cache is not None else {}
    api_keys = {
        "GEMINI_API_KEY": settings.gemini_api_key,
        "OPENAI_API_KEY": settings.openai_api_key,
        "OPENROUTER_API_KEY": settings.openrouter_api_key,
        "ANTHROPIC_API_KEY": settings.anthropic_api_key,
    }

    errors: list[str] = []
    for provider_type, model_name in ordered_candidates:
        provider = cache.get(provider_type)
        if provider is None:
            try:
                provider = get_provider(provider_type, api_keys)
                cache[provider_type] = provider
            except Exception as exc:
                errors.append(f"{provider_type.value}/{model_name} init error: {_short_error_message(exc)}")
                continue

        try:
            image_bytes = provider.generate_image(prompt, model_name)
            return image_bytes, (provider_type, model_name)
        except Exception as exc:
            errors.append(f"{provider_type.value}/{model_name} failed: {_short_error_message(exc)}")

    raise RuntimeError("Image generation failed across all candidates: " + " | ".join(errors))


def generate_block_images(run_id: str, story_payload: dict[str, Any], pipeline: PipelineDefinition, settings: AppSettings) -> dict[str, Any]:
    provider_cache: dict[ProviderType, Any] = {}
    preferred_candidate: tuple[ProviderType, str] | None = None

    images_dir = RUNS_DIR / run_id / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    def _gen_and_save(prompt: str, filename: str) -> str | None:
        nonlocal preferred_candidate
        try:
            logger.info("Generating image locally: %s", filename)
            img_bytes, preferred_candidate = generate_image_with_fallback(
                prompt,
                pipeline,
                settings,
                provider_cache=provider_cache,
                preferred_candidate=preferred_candidate,
            )
            path = images_dir / filename
            path.write_bytes(img_bytes)
            return f"images/{filename}"
        except Exception as exc:
            logger.error("Local image generation failed for %s: %s", filename, _short_error_message(exc))
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

    for i, item in enumerate(story_payload.get("photo_gallery", [])):
        prompt = item.get("image_prompt")
        if prompt and not item.get("local_image_path"):
            path = _gen_and_save(prompt, f"gallery_{i}.jpg")
            if path:
                item["local_image_path"] = path

    return story_payload


def generate_block_tts(
    run_id: str,
    story_payload: dict[str, Any],
    settings: AppSettings,
    *,
    tts_tier: str = "premium",
    story_id_seed: str | None = None,
    force_regenerate: bool = False,
    existing_voice_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    voice_notes = story_payload.get("voice_notes", [])
    if not isinstance(voice_notes, list) or not voice_notes:
        story_payload["voice_map"] = dict(existing_voice_map or {})
        story_payload["tts_tier"] = tts_tier
        return story_payload

    audio_dir = RUNS_DIR / run_id / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    stable_story_id = story_id_seed or story_payload.get("story_title") or run_id
    voice_map = _build_voice_map(
        stable_story_id,
        [item for item in voice_notes if isinstance(item, dict)],
        tts_tier,
        existing_map=existing_voice_map,
    )

    for i, item in enumerate(voice_notes):
        if not isinstance(item, dict):
            continue
        transcript = str(item.get("transcript") or "").strip()
        if not transcript:
            continue

        speaker = (item.get("speaker") or "Unknown").strip() or "Unknown"
        voice_id = voice_map.get(speaker) or _voice_pool(tts_tier)[0]
        prior_voice = str(item.get("voice_id") or "")
        prior_audio = str(item.get("local_audio_path") or "")
        if (
            not force_regenerate
            and prior_audio
            and prior_voice == voice_id
            and (RUNS_DIR / run_id / prior_audio).exists()
        ):
            item["voice_id"] = voice_id
            continue

        try:
            audio_bytes = _generate_tts_bytes(transcript, voice_id, tts_tier, settings)
            filename = f"voice_note_{i}.mp3"
            output_path = audio_dir / filename
            output_path.write_bytes(audio_bytes)
            item["local_audio_path"] = f"audio/{filename}"
            item["voice_id"] = voice_id
        except Exception as exc:
            logger.error("TTS generation failed for voice note index=%s speaker=%s: %s", i, speaker, exc)

    story_payload["voice_map"] = voice_map
    story_payload["tts_tier"] = tts_tier
    return story_payload

def _get_firebase_clients(settings: AppSettings):
    """Helper to initialize and return Firestore and Storage clients."""
    import firebase_admin
    from firebase_admin import credentials, firestore, storage
    import json

    path_val = settings.google_application_credentials
    if not path_val:
        return None, None

    path, candidates = _resolve_credentials_path_with_candidates(path_val)
    if path is None or not path.exists():
        attempted = [str(candidate.resolve()) for candidate in candidates]
        logger.warning(
            "Firebase credentials not found. configured_path=%s attempted=%s",
            path_val,
            attempted,
        )
        return None, None

    _assert_google_oauth_dns_reachable()

    resolved_path = str(path)
    cred = credentials.Certificate(resolved_path)
    configured_bucket = (settings.firebase_storage_bucket or "").strip()
    bucket_candidates: list[str] = []
    if configured_bucket:
        bucket_candidates = [configured_bucket]
    else:
        with open(resolved_path, "r", encoding="utf-8") as f:
            sa = json.load(f)
            project_id = (sa.get("project_id") or "").strip()
        if project_id:
            bucket_candidates = [
                f"{project_id}.appspot.com",
                f"{project_id}.firebasestorage.app",
            ]

    try:
        firebase_admin.get_app()
    except ValueError:
        init_bucket = bucket_candidates[0] if bucket_candidates else None
        options = {"storageBucket": init_bucket} if init_bucket else {}
        firebase_admin.initialize_app(cred, options)
        
    db = firestore.client()
    bucket = None
    for bucket_name in bucket_candidates:
        try:
            candidate = storage.bucket(name=bucket_name)
            if candidate.exists():
                bucket = candidate
                break
            logger.warning("Bucket %s does not exist", bucket_name)
        except Exception as e:
            logger.warning("Could not get bucket %s: %s", bucket_name, e)

    if bucket is None and bucket_candidates:
        logger.warning("No accessible storage bucket found from candidates=%s", bucket_candidates)
        
    return db, bucket

def list_stories(settings: AppSettings):
    """Lists all stories from Firestore."""
    db, _ = _get_firebase_clients(settings)
    if db is None:
        return []
    
    stories_ref = db.collection("stories").order_by("createdAt", direction="DESCENDING")
    stories = []
    for doc in stories_ref.stream():
        data = doc.to_dict()
        data["id"] = doc.id
        
        # Safe defaults for older stories
        data.setdefault("storyMode", "live")
        data.setdefault("storySubMode", "default")
        data.setdefault("storyDurationMinutes", 0)
        data.setdefault("title", "Untitled Story")
        data.setdefault("isPublished", True)
        data.setdefault("autoDeployed", False)
        data.setdefault("autoDeploySource", None)
        
        # Convert datetime objects to ISO strings for JSON serialization
        for key in ["createdAt", "storyStartAt", "storyEndAt", "publishedAt"]:
            if key in data and isinstance(data[key], datetime):
                data[key] = data[key].isoformat()
            elif key not in data:
                data[key] = None
        
        stories.append(data)
    
    return stories

def delete_story(story_id: str, settings: AppSettings):
    """Deletes a story from Firestore and its assets from Storage."""
    db, bucket = _get_firebase_clients(settings)
    if db is None:
        logger.error("Firebase clients not initialized, cannot delete story.")
        return False
        
    story_ref = db.collection("stories").document(story_id)
    if not story_ref.get().exists:
        logger.info(f"Story {story_id} not found.")
        return False

    # 1. Delete blobs in storage folder: stories/{story_id}/
    if bucket:
        try:
            blobs = bucket.list_blobs(prefix=f"stories/{story_id}/")
            for blob in blobs:
                blob.delete()
            logger.info(f"Deleted storage assets for {story_id}")
        except Exception as e:
            logger.error(f"Failed to delete story assets in storage for {story_id}: {e}")

    # 2. Delete subcollections in Firestore (recursive)
    def _delete_doc_tree(doc_ref):
        for sub_collection in doc_ref.collections():
            for child in sub_collection.stream():
                _delete_doc_tree(child.reference)
        doc_ref.delete()

    for sub_collection in story_ref.collections():
        for doc in sub_collection.stream():
            _delete_doc_tree(doc.reference)
            
    # 3. Delete the parent document
    story_ref.delete()
    logger.info(f"Deleted story document {story_id}")
    return True


def cleanup_all_stories(settings: AppSettings) -> dict[str, Any]:
    """Deletes every story in Firebase and returns cleanup stats."""
    db, _ = _get_firebase_clients(settings)
    if db is None:
        raise RuntimeError("Firebase clients not initialized, cleanup aborted.")

    stories = list_stories(settings)
    total = len(stories)
    deleted = 0
    failed_ids: list[str] = []

    for story in stories:
        story_id = str(story.get("id") or "").strip()
        if not story_id:
            continue
        try:
            if delete_story(story_id, settings):
                deleted += 1
            else:
                failed_ids.append(story_id)
        except Exception:
            logger.exception("Failed deleting story during cleanup story_id=%s", story_id)
            failed_ids.append(story_id)

    return {
        "total": total,
        "deleted": deleted,
        "failed": len(failed_ids),
        "failed_ids": failed_ids,
    }


def make_story_live(story_id: str, settings: AppSettings) -> bool:
    """Marks a story as published/available to users."""
    db, _ = _get_firebase_clients(settings)
    if db is None:
        logger.error("Firebase clients not initialized, cannot publish story.")
        return False

    story_ref = db.collection("stories").document(story_id)
    snap = story_ref.get()
    if not snap.exists:
        logger.info("Story %s not found while publishing.", story_id)
        return False

    data = snap.to_dict() or {}
    now = datetime.now(timezone.utc)
    updates: dict[str, Any] = {
        "isPublished": True,
        "publishedAt": now,
    }
    # Guardrail: if a live story had no start time, start it when published.
    if (data.get("storyMode") or "live") == "live" and not data.get("storyStartAt"):
        updates["storyStartAt"] = now

    story_ref.set(updates, merge=True)
    logger.info("Published story story_id=%s", story_id)
    return True

def generate_story_packaging(
    result: RunResult,
    settings: AppSettings,
    pipeline: PipelineDefinition,
) -> StoryPackaging:
    """Generate story packaging metadata from a completed run using a cheap LLM pass."""
    story_data = result.final_output
    if not isinstance(story_data, dict):
        logger.warning("Cannot generate packaging: final_output is not a dict")
        return StoryPackaging()

    title = story_data.get("story_title", "Untitled")
    setup = result.setup or ""
    characters = [
        f"{c.name}: {c.background}" for c in (result.characters or [])
    ]

    # Gather artifact samples for context
    chats = story_data.get("chats", [])
    journals = story_data.get("journals", [])
    emails = story_data.get("emails", [])
    voice_notes = story_data.get("voice_notes", [])
    social_posts = story_data.get("social_posts", [])

    artifact_samples = []
    for chat in chats[:3]:
        text = chat.get("text", "") if isinstance(chat, dict) else ""
        if text:
            artifact_samples.append(f"[chat] {text[:120]}")
    for j in journals[:2]:
        body = j.get("body", "") if isinstance(j, dict) else ""
        if body:
            artifact_samples.append(f"[journal] {body[:120]}")
    for e in emails[:2]:
        subj = e.get("subject", "") if isinstance(e, dict) else ""
        if subj:
            artifact_samples.append(f"[email] {subj}")
    for vn in voice_notes[:1]:
        t = vn.get("transcript", "") if isinstance(vn, dict) else ""
        if t:
            artifact_samples.append(f"[voice_note] {t[:120]}")
    for sp in social_posts[:1]:
        c = sp.get("content", "") if isinstance(sp, dict) else ""
        if c:
            artifact_samples.append(f"[social_post] {c[:120]}")

    # Determine hero artifact type
    artifact_type_counts = {
        "chat": len(chats),
        "journal": len(journals),
        "email": len(emails),
        "voice_note": len(voice_notes),
        "social_post": len(social_posts),
    }
    hero_type = max(artifact_type_counts, key=artifact_type_counts.get) if any(artifact_type_counts.values()) else "chat"

    prompt = f"""You are a story marketing copywriter for a real-time epistolary thriller app.

Given this story, generate compelling packaging to hook new readers.

STORY TITLE: {title}
SETUP: {setup}
CHARACTERS: {', '.join(characters[:4]) if characters else 'Unknown'}
SAMPLE ARTIFACTS:
{chr(10).join(artifact_samples[:8])}

Generate a JSON object with these fields:
- "hook_line": One sentence (max 140 chars) that makes someone NEED to know what happens. Be specific, not generic. Avoid vague genre cliches like "A thrilling mystery unfolds..." or "A suspenseful tale of secrets...".
- "promise_line": One sentence (max 140 chars) describing what the reader will experience/discover. Use "you" to address the reader directly.
- "tone_tags": Array of 2-4 single-word mood tags (e.g. "obsessive", "romantic", "dangerous", "paranoid").
- "audience_hook_type": A hyphenated genre-mood label (e.g. "twisted-romance", "paranoid-thriller", "family-secrets").
- "hero_artifact_title": A short title for the most compelling artifact preview.
- "hero_artifact_body": One punchy line from or about the most compelling artifact (max 80 chars).

Return ONLY valid JSON, no markdown fences."""

    api_keys = {
        "GEMINI": settings.gemini_api_key,
        "OPENAI": settings.openai_api_key,
        "ANTHROPIC": settings.anthropic_api_key,
        "OPENROUTER": settings.openrouter_api_key,
    }

    # Use the cheapest available provider
    provider_type = ProviderType.GEMINI
    default_model = pipeline.default_models.get(ProviderType.GEMINI.value, "gemini-2.5-flash")
    if not api_keys.get("GEMINI"):
        provider_type = ProviderType.OPENAI
        default_model = pipeline.default_models.get(ProviderType.OPENAI.value, "gpt-5.4-mini")

    try:
        provider = get_provider(provider_type, api_keys)
        config = BlockConfig(
            provider=provider_type,
            model_name=default_model,
            temperature=0.8,
            system_instruction="You are a story marketing copywriter. Return only valid JSON.",
            prompt_template="{input}",
        )
        raw = provider.generate_content(config, prompt)
        # Parse the JSON response
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        data = json.loads(cleaned)

        hero_preview = None
        if data.get("hero_artifact_title") or data.get("hero_artifact_body"):
            hero_preview = HeroArtifactPreview(
                title=data.get("hero_artifact_title", ""),
                body=data.get("hero_artifact_body", ""),
            )

        return StoryPackaging(
            hook_line=data.get("hook_line", "")[:140],
            promise_line=data.get("promise_line", "")[:140],
            hero_artifact_type=hero_type,
            hero_artifact_preview=hero_preview,
            tone_tags=data.get("tone_tags", [])[:4],
            audience_hook_type=data.get("audience_hook_type", ""),
        )
    except Exception as exc:
        logger.error("Packaging generation failed: %s", exc)
        return StoryPackaging(
            hook_line=f"{title[:100]} — a story told through the artifacts left behind.",
            promise_line="Piece together the truth from messages, journals, and receipts.",
            hero_artifact_type=hero_type,
            tone_tags=["suspense"],
            audience_hook_type="found-phone-thriller",
        )


def upload_to_firestore(
    result: RunResult,
    settings: AppSettings,
    pipeline: PipelineDefinition,
    *,
    story_mode: str = "live",
    story_sub_mode: str = "default",
    scheduled_start_at: datetime | None = None,
    tts_tier: str = "premium",
    auto_deployed: bool = False,
    auto_deploy_source: str | None = None,
    packaging: StoryPackaging | None = None,
):
    story_data = result.final_output
    if not isinstance(story_data, dict):
        raise ValueError("final_output must be a dict")

    story_mode = (story_mode or "live").strip().lower()
    if story_mode not in {"live", "scheduled", "subscription"}:
        raise ValueError(f"Unsupported story_mode '{story_mode}'.")
    story_sub_mode = (story_sub_mode or "default").strip().lower()
    if story_sub_mode not in {"default", "on_demand"}:
        raise ValueError(f"Unsupported story_sub_mode '{story_sub_mode}'.")
    if story_mode != "subscription":
        story_sub_mode = "default"
    tts_tier = (tts_tier or "premium").strip().lower()
    if tts_tier not in {"premium", "cheap"}:
        raise ValueError(f"Unsupported tts_tier '{tts_tier}'.")

    scheduled_start_utc = _normalize_story_datetime_utc(scheduled_start_at)
    if story_mode == "scheduled" and scheduled_start_utc is None:
        raise ValueError("scheduled_start_at is required when story_mode is 'scheduled'.")

    logger.info(
        "Upload start story_title=%s mode=%s tts_tier=%s",
        story_data.get("story_title"),
        story_mode,
        tts_tier,
    )
    
    db, bucket = _get_firebase_clients(settings)
    if db is None:
        raise RuntimeError("Firebase clients not initialized, upload aborted.")

    import time # Keep time import as it's used for story_id and blob names

    created_at = datetime.now(timezone.utc)
    story_id = f"story_{int(time.time())}"
    story_ref = db.collection("stories").document(story_id)

    story_start_at = created_at
    if story_mode == "scheduled":
        story_start_at = scheduled_start_utc or created_at
    elif story_mode == "subscription":
        story_start_at = None
    story_duration_minutes = _story_duration_minutes(story_data)
    story_end_at = (
        story_start_at + timedelta(minutes=story_duration_minutes)
        if story_start_at is not None
        else None
    )
    on_demand_config = _on_demand_config() if story_sub_mode == "on_demand" else None
    theme_color_hex = _derive_theme_color_hex(story_id, str(story_data.get("story_title") or "Untitled"))
    voice_map = story_data.get("voice_map") if isinstance(story_data.get("voice_map"), dict) else {}

    headline_url = None
    headline_local_path = (
        story_data.get("headline_image_path")
        or getattr(result, "headline_image_path", None)
    )
    if headline_local_path and bucket:
        try:
            base_path = str(headline_local_path).split("?")[0]
            full_local_path = RUNS_DIR / result.run_id / base_path
            if full_local_path.exists():
                blob = bucket.blob(f"stories/{story_id}/headline_{int(time.time())}.jpg")
                blob.upload_from_filename(str(full_local_path), content_type="image/jpeg")
                blob.make_public()
                headline_url = blob.public_url
        except Exception as e:
            logger.error("Headline image upload failed: %s", e)

    # Generate packaging if not provided; use existing from run result as fallback
    if packaging is None:
        packaging = getattr(result, "packaging", None)
    if packaging is None or not packaging.hook_line:
        try:
            packaging = generate_story_packaging(result, settings, pipeline)
        except Exception as exc:
            logger.error("Auto-packaging generation failed during upload: %s", exc)
            packaging = StoryPackaging()

    packaging_doc = {}
    if packaging and packaging.hook_line:
        packaging_doc = {
            "hookLine": packaging.hook_line,
            "promiseLine": packaging.promise_line,
            "heroArtifactType": packaging.hero_artifact_type,
            "heroArtifactPreview": (
                {"title": packaging.hero_artifact_preview.title, "body": packaging.hero_artifact_preview.body}
                if packaging.hero_artifact_preview else None
            ),
            "toneTags": packaging.tone_tags,
            "audienceHookType": packaging.audience_hook_type,
        }

    story_ref.set(
        {
            "title": story_data.get("story_title", "Untitled"),
            "setup": result.setup,
            "tags": result.tags,
            "allowedLanguages": result.allowed_languages,
            "characters": [_serialize_output(c) for c in result.characters],
            "headlineImageUrl": headline_url,
            "createdAt": created_at,
            "storyMode": story_mode,
            "storySubMode": story_sub_mode,
            "storyStartAt": story_start_at,
            "storyEndAt": story_end_at,
            "storyDurationMinutes": story_duration_minutes,
            "themeColorHex": theme_color_hex,
            "ttsTier": tts_tier,
            "voiceMap": voice_map,
            "onDemandConfig": on_demand_config,
            "isPublished": False,
            "publishedAt": None,
            "autoDeployed": bool(auto_deployed),
            "autoDeploySource": (auto_deploy_source or "").strip() or None,
            "autoDeployedAt": created_at if auto_deployed else None,
            **packaging_doc,
        }
    )

    def _unlock_timestamp_for_offset(offset_minutes: int) -> datetime:
        base = story_start_at if story_start_at is not None else created_at
        return base + timedelta(minutes=offset_minutes)

    def upload_collection(collection_name, items):
        if not items:
            return

        batch = db.batch()
        for i, item in enumerate(items):
            doc_ref = story_ref.collection(collection_name).document()
            doc_data = item.copy()
            offset_minutes = _coerce_offset_minutes(
                doc_data.get("time_offset_minutes", doc_data.get("timeOffsetMinutes", 0))
            )
            unlock_time = _unlock_timestamp_for_offset(offset_minutes)
            doc_data["time_offset_minutes"] = offset_minutes
            doc_data["timeOffsetMinutes"] = offset_minutes
            doc_data["unlockTimestamp"] = unlock_time

            local_path = doc_data.pop("local_image_path", None)
            if local_path and bucket:
                try:
                    base_path = str(local_path).split("?")[0]
                    full_local_path = RUNS_DIR / result.run_id / base_path
                    if full_local_path.exists():
                        blob = bucket.blob(f"stories/{story_id}/{collection_name}_{i}_{int(time.time())}.jpg")
                        blob.upload_from_filename(str(full_local_path), content_type="image/jpeg")
                        blob.make_public()
                        doc_data["imageUrl"] = blob.public_url
                except Exception as e:
                    logger.error("Image upload failed: %s", e)

            if collection_name == "voice_notes":
                local_audio_path = doc_data.pop("local_audio_path", None)
                audio_url = None
                if local_audio_path and bucket:
                    try:
                        base_audio_path = str(local_audio_path).split("?")[0]
                        full_local_audio = RUNS_DIR / result.run_id / base_audio_path
                        if full_local_audio.exists():
                            blob = bucket.blob(f"stories/{story_id}/voice_note_{i}_{int(time.time())}.mp3")
                            blob.upload_from_filename(str(full_local_audio), content_type="audio/mpeg")
                            blob.make_public()
                            audio_url = blob.public_url
                    except Exception as e:
                        logger.error("Voice note audio upload failed: %s", e)
                if audio_url:
                    doc_data["audioUrl"] = audio_url
                    doc_data["audio_url"] = audio_url
                voice_id = doc_data.get("voice_id")
                if voice_id:
                    doc_data["voiceId"] = voice_id

            batch.set(doc_ref, doc_data)
        batch.commit()

    def upload_gallery(items):
        if not items:
            return
        batch = db.batch()
        for i, item in enumerate(items):
            doc_ref = story_ref.collection("gallery").document()
            offset_minutes = _coerce_offset_minutes(
                item.get("time_offset_minutes", item.get("timeOffsetMinutes", 0))
            )
            unlock_time = _unlock_timestamp_for_offset(offset_minutes)
            local_path = item.get("local_image_path")
            image_url = None
            if local_path and bucket:
                try:
                    base_path = local_path.split("?")[0]
                    full_local_path = RUNS_DIR / result.run_id / base_path
                    if full_local_path.exists():
                        blob = bucket.blob(f"stories/{story_id}/gallery_{i}_{int(time.time())}.jpg")
                        blob.upload_from_filename(str(full_local_path), content_type="image/jpeg")
                        blob.make_public()
                        image_url = blob.public_url
                except Exception as e:
                    logger.error("Gallery image upload failed: %s", e)
            doc_data = {
                "tier": item.get("tier", "diegetic"),
                "subject": item.get("subject", ""),
                "caption": item.get("caption"),
                "time_offset_minutes": offset_minutes,
                "timeOffsetMinutes": offset_minutes,
                "unlockTimestamp": unlock_time,
                "imageUrl": image_url,
            }
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
    upload_gallery(story_data.get("photo_gallery", []))

    logger.info("Upload complete story_id=%s", story_id)
    return story_id
