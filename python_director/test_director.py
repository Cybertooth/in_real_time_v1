from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from python_director.defaults import get_default_pipeline, get_pipeline_reset_template, get_reset_template_catalog
from python_director.logic import PipelineRunner, compare_final_outputs, generate_block_tts
from python_director.models import (
    AppSettings,
    BlockConfig,
    BlockType,
    CompareRunsRequest,
    PipelineBlock,
    PipelineDefinition,
    ProviderType,
    RunResult,
    StoryMode,
    TTSTier,
    UploadRunRequest,
)
from python_director.storage import (
    list_named_pipelines,
    list_run_summaries,
    load_named_pipeline,
    load_pipeline,
    save_pipeline,
    save_named_pipeline,
)


def _block(
    block_id: str,
    *,
    block_type: BlockType,
    prompt: str,
    inputs: list[str] | None = None,
) -> PipelineBlock:
    return PipelineBlock(
        id=block_id,
        name=block_id,
        description="",
        type=block_type,
        enabled=True,
        input_blocks=inputs or [],
        config=BlockConfig(
            provider=ProviderType.GEMINI,
            model_name="gemini-3-flash-preview",
            temperature=0.4,
            system_instruction="system",
            prompt_template=prompt,
        ),
    )


class FakeProvider:
    def __init__(self):
        self.content_calls = []

    def generate_content(self, config, contents):
        self.content_calls.append((config, contents))
        return f"generated::{contents}"

    def generate_structured_output(self, config, contents, response_schema):
        return response_schema.model_validate({})


def test_runner_writes_block_outputs_and_traces(tmp_path: Path, monkeypatch):
    pipeline = PipelineDefinition(
        name="test",
        blocks=[
            _block("a", block_type=BlockType.CREATIVE_OUTLINER, prompt="first"),
            _block("b", block_type=BlockType.PLANNER, prompt="second {{a}}", inputs=["a"]),
        ],
    )
    monkeypatch.setattr("python_director.logic.RUNS_DIR", tmp_path)
    monkeypatch.setattr("python_director.logic.save_run_result", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("python_director.logic.get_provider", lambda *_args, **_kwargs: FakeProvider())

    result = PipelineRunner(AppSettings(gemini_api_key="test")).run_pipeline(pipeline, run_id="run_x")
    run_dir = tmp_path / "run_x"

    assert result.block_sequence == ["a", "b"]
    assert "a" in result.outputs
    assert "generated::second generated::first" in result.outputs["b"]
    assert "a" in result.block_traces
    assert result.block_traces["b"].resolved_prompt.startswith("second")
    assert (run_dir / "a.txt").exists()
    assert (run_dir / "b.prompt.txt").exists()


def test_cycle_detection(tmp_path: Path, monkeypatch):
    pipeline = PipelineDefinition(
        name="bad",
        blocks=[
            _block("a", block_type=BlockType.CREATIVE_OUTLINER, prompt="a", inputs=["b"]),
            _block("b", block_type=BlockType.PLANNER, prompt="b", inputs=["a"]),
        ],
    )
    monkeypatch.setattr("python_director.logic.RUNS_DIR", tmp_path)
    monkeypatch.setattr("python_director.logic.get_provider", lambda *_args, **_kwargs: FakeProvider())
    runner = PipelineRunner(AppSettings(gemini_api_key="x"))
    with pytest.raises(ValueError, match="cycle"):
        runner.run_pipeline(pipeline, run_id="run_cycle")


def test_compare_final_outputs_includes_quality_proxy_score():
    baseline = RunResult(
        run_id="run_a",
        timestamp="2026-01-01T00:00:00Z",
        pipeline_name="p",
        outputs={},
        final_output={
            "story_title": "A",
            "journals": [{"body": "one two three"}],
            "chats": [{"text": "hi"}],
            "emails": [],
            "receipts": [],
            "voice_notes": [],
        },
    )
    candidate = RunResult(
        run_id="run_b",
        timestamp="2026-01-01T00:00:01Z",
        pipeline_name="p",
        outputs={},
        final_output={
            "story_title": "B",
            "journals": [{"body": "one two three four five six"}],
            "chats": [{"text": "hi there"}],
            "emails": [],
            "receipts": [],
            "voice_notes": [{"transcript": "voice words here"}],
        },
    )
    comparison = compare_final_outputs(
        CompareRunsRequest(baseline_run_id="run_a", candidate_run_id="run_b"),
        baseline,
        candidate,
    )
    labels = {metric.label for metric in comparison.metrics}
    assert "quality_proxy_score" in labels
    assert comparison.quality_notes
    assert comparison.baseline_title == "A"
    assert comparison.candidate_title == "B"


def test_named_pipeline_save_and_load(tmp_path: Path, monkeypatch):
    from python_director import storage

    monkeypatch.setattr(storage, "PIPELINES_DIR", tmp_path / "pipelines")
    monkeypatch.setattr(storage, "PIPELINE_FILE", tmp_path / "pipeline.json")

    pipeline = PipelineDefinition(
        name="Working Pipeline",
        description="test",
        blocks=[_block("a", block_type=BlockType.CREATIVE_OUTLINER, prompt="seed")],
    )

    saved, catalog_item = save_named_pipeline("Council Iteration V1", pipeline, set_active=True)
    assert saved.name == "Council Iteration V1"
    assert catalog_item.key == "council_iteration_v1"
    assert (tmp_path / "pipeline.json").exists()

    catalog = list_named_pipelines()
    assert len(catalog) == 1
    assert catalog[0].name == "Council Iteration V1"

    loaded = load_named_pipeline("council_iteration_v1")
    assert loaded.name == "Council Iteration V1"


def test_invalid_pipeline_file_resets_to_default(tmp_path: Path, monkeypatch):
    from python_director import storage

    pipeline_path = tmp_path / "pipeline.json"
    pipeline_path.write_text('{"name":"broken","blocks":[{"id":"x"}]}', encoding="utf-8")
    monkeypatch.setattr(storage, "PIPELINE_FILE", pipeline_path)

    loaded = load_pipeline()
    ids = [block.id for block in loaded.blocks]
    assert "creative_brainstorm" in ids
    assert "council_brainstorm_judge" in ids
    assert pipeline_path.exists()
    archived = list(tmp_path.glob("pipeline.invalid.*.json"))
    assert archived


def test_invalid_run_result_file_is_skipped(tmp_path: Path, monkeypatch):
    from python_director import storage

    runs_dir = tmp_path / "temp_artifacts"
    bad_run = runs_dir / "run_bad"
    bad_run.mkdir(parents=True, exist_ok=True)
    (bad_run / "run_result.json").write_text('{"run_id":"x","bad":true}', encoding="utf-8")
    monkeypatch.setattr(storage, "RUNS_DIR", runs_dir)

    summaries = list_run_summaries()
    assert summaries == []


def test_default_pipeline_includes_brainstorm_council_blocks():
    pipeline = get_default_pipeline()
    ids = [block.id for block in pipeline.blocks]

    assert "creative_brainstorm" in ids
    # Brainstorm council: 3 parallel members + judge
    assert "council_brainstorm_gemini_pro" in ids
    assert "council_brainstorm_gemini_flash" in ids
    assert "council_brainstorm_openai" in ids
    assert "council_brainstorm_judge" in ids
    # Plan council: 3 parallel members + judge
    assert "council_plan_gemini_pro" in ids
    assert "council_plan_gemini_flash" in ids
    assert "council_plan_openai" in ids
    assert "council_plan_judge" in ids
    assert pipeline.default_models["GEMINI"] == "gemini-3-flash-preview"


def test_runner_uses_pipeline_default_model_when_block_inherits(tmp_path: Path, monkeypatch):
    pipeline = PipelineDefinition(
        name="test-default-model",
        default_models={
            "GEMINI": "gemini-2.5-pro",
            "OPENAI": "gpt-5.4",
        },
        blocks=[
            PipelineBlock(
                id="a",
                name="a",
                description="",
                type=BlockType.CREATIVE_OUTLINER,
                enabled=True,
                input_blocks=[],
                config=BlockConfig(
                    provider=ProviderType.GEMINI,
                    model_name=None,
                    use_pipeline_default_model=True,
                    temperature=0.4,
                    system_instruction="system",
                    prompt_template="first",
                ),
            )
        ],
    )
    provider = FakeProvider()
    monkeypatch.setattr("python_director.logic.RUNS_DIR", tmp_path)
    monkeypatch.setattr("python_director.logic.save_run_result", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("python_director.logic.get_provider", lambda *_args, **_kwargs: provider)

    result = PipelineRunner(AppSettings(gemini_api_key="test")).run_pipeline(pipeline, run_id="run_default_model")

    assert provider.content_calls
    config, _contents = provider.content_calls[0]
    assert config.model_name == "gemini-2.5-pro"
    assert result.block_traces["a"].model_name == "gemini-2.5-pro"


def test_delete_named_pipeline(tmp_path, monkeypatch):
    """Test deleting a named pipeline"""
    from python_director import storage

    monkeypatch.setattr(storage, "PIPELINES_DIR", tmp_path)
    # Create a fake pipeline file
    (tmp_path / "test_pipeline.json").write_text('{"name":"Test","blocks":[]}')
    assert storage.delete_named_pipeline("test_pipeline") is True
    assert not (tmp_path / "test_pipeline.json").exists()
    assert storage.delete_named_pipeline("nonexistent") is False


def test_derive_story_timeline_all_types():
    from python_director.logic import derive_story_timeline

    final_output = {
        "story_title": "Test Story",
        "journals": [{"title": "Entry 1", "body": "Journal body", "time_offset_minutes": 0}],
        "chats": [{"senderId": "Alex", "text": "Hey", "isProtagonist": False, "time_offset_minutes": 30}],
        "emails": [{"sender": "test@example.com", "subject": "Alert", "body": "Email body", "time_offset_minutes": 60}],
        "receipts": [{"merchantName": "Coffee Shop", "amount": 4.50, "description": "Latte", "time_offset_minutes": 90}],
        "voice_notes": [{"speaker": "Unknown", "transcript": "Hello there", "time_offset_minutes": 120}],
    }
    timeline = derive_story_timeline(final_output)
    types = [e.event_type for e in timeline]
    assert "journal" in types
    assert "chat" in types
    assert "email" in types
    assert "receipt" in types
    assert "voice_note" in types
    assert len(timeline) == 5
    # Verify content is populated
    journal_entry = next(e for e in timeline if e.event_type == "journal")
    assert journal_entry.content is not None
    assert journal_entry.content["body"] == "Journal body"
    # Verify sorted by time
    times = [e.story_time for e in timeline]
    assert times == sorted(times)


def test_save_pipeline_persists_model_name_for_inherited_blocks(tmp_path: Path, monkeypatch):
    from python_director import storage

    monkeypatch.setattr(storage, "PIPELINE_FILE", tmp_path / "pipeline.json")
    pipeline = PipelineDefinition(
        name="normalize",
        default_models={"GEMINI": "gemini-2.5-pro", "OPENAI": "gpt-5.4-mini"},
        blocks=[
            PipelineBlock(
                id="a",
                name="a",
                description="",
                type=BlockType.CREATIVE_OUTLINER,
                enabled=True,
                input_blocks=[],
                config=BlockConfig(
                    provider=ProviderType.GEMINI,
                    model_name=None,
                    use_pipeline_default_model=True,
                    temperature=0.4,
                    system_instruction="system",
                    prompt_template="first",
                ),
            )
        ],
    )

    saved = save_pipeline(pipeline)

    assert saved.blocks[0].config.model_name == "gemini-2.5-pro"


def test_burstiness_metrics_computed_on_final_output():
    from python_director.logic import _story_metrics

    # 3 chats in a tight burst (0, 2, 4 min), then a long gap, then an email at 200 min
    final_output = {
        "story_title": "Burst Test",
        "journals": [],
        "chats": [
            {"senderId": "A", "text": "hi", "isProtagonist": False, "time_offset_minutes": 0},
            {"senderId": "B", "text": "hey", "isProtagonist": True, "time_offset_minutes": 2},
            {"senderId": "A", "text": "ok", "isProtagonist": False, "time_offset_minutes": 4},
        ],
        "emails": [{"sender": "x@x.com", "subject": "S", "body": "B", "time_offset_minutes": 200}],
        "receipts": [],
        "voice_notes": [],
    }
    metrics = _story_metrics(final_output)

    assert "burstiness_score" in metrics
    assert "total_pause_minutes" in metrics
    assert "max_pause_minutes" in metrics
    assert "act1_pause_minutes" in metrics
    assert "avg_chat_burst_length" in metrics
    # 4 items total at t=0,2,4,200 → gaps=[2,2,196], total_pause=200
    assert metrics["total_pause_minutes"] == 200
    assert metrics["max_pause_minutes"] == 196
    # All items within act1 (<= 960 min)
    assert metrics["act1_pause_minutes"] == 200
    # Chats 0,2,4 are within 5-min window (1 burst of 3)
    assert metrics["avg_chat_burst_length"] == 3.0
    # Score must be a non-negative float
    assert isinstance(metrics["burstiness_score"], (int, float))
    assert 0 <= metrics["burstiness_score"] <= 100


def test_burstiness_score_perfect_vs_irregular():
    from python_director.logic import _story_metrics

    def _make_output(times: list[int]):
        return {
            "story_title": "Test",
            "journals": [{"title": "t", "body": "b", "time_offset_minutes": t} for t in times],
            "chats": [], "emails": [], "receipts": [], "voice_notes": [],
        }

    # Perfectly even gaps → high burstiness score
    even = _make_output([0, 10, 20, 30, 40])
    even_score = _story_metrics(even)["burstiness_score"]

    # Very uneven gaps → lower burstiness score
    uneven = _make_output([0, 1, 2, 500, 501])
    uneven_score = _story_metrics(uneven)["burstiness_score"]

    assert even_score > uneven_score, (
        f"Even spacing should score higher than uneven: {even_score} vs {uneven_score}"
    )


def test_upload_request_validates_scheduled_mode():
    with pytest.raises(ValueError, match="scheduled_start_at is required"):
        UploadRunRequest(story_mode=StoryMode.SCHEDULED, scheduled_start_at=None)

    req = UploadRunRequest(
        story_mode=StoryMode.SCHEDULED,
        scheduled_start_at=datetime(2026, 3, 22, 12, 0, tzinfo=timezone.utc),
        tts_tier=TTSTier.CHEAP,
    )
    assert req.story_mode == StoryMode.SCHEDULED
    assert req.tts_tier == TTSTier.CHEAP

    live_req = UploadRunRequest(
        story_mode=StoryMode.LIVE,
        scheduled_start_at=datetime(2026, 3, 22, 12, 0, tzinfo=timezone.utc),
    )
    assert live_req.scheduled_start_at is None


def test_reset_templates_catalog_and_profiles():
    catalog = get_reset_template_catalog()
    keys = [item.key for item in catalog]
    assert keys == ["full_fledged", "cheap_full", "cheap_short"]

    full = get_pipeline_reset_template("full_fledged")
    cheap_full = get_pipeline_reset_template("cheap_full")
    cheap_short = get_pipeline_reset_template("cheap_short")

    assert full.name == "Found Phone Director"
    assert cheap_full.image_provider == ProviderType.OPENROUTER
    assert cheap_full.default_image_models[ProviderType.OPENROUTER.value] == "bytedance-seed/seedream-4.5"
    assert any(b.id == "tts_generation" for b in full.blocks)
    assert any(not b.enabled for b in cheap_short.blocks if b.id.startswith("council_"))

    with pytest.raises(ValueError, match="Unknown reset template_key"):
        get_pipeline_reset_template("does_not_exist")


def test_generate_block_tts_assigns_deterministic_voice_map(tmp_path: Path, monkeypatch):
    from python_director import logic

    monkeypatch.setattr(logic, "RUNS_DIR", tmp_path)
    monkeypatch.setattr(logic, "_generate_tts_bytes", lambda *_args, **_kwargs: b"fake-mp3")

    payload = {
        "story_title": "Voice Story",
        "voice_notes": [
            {"speaker": "Alex", "transcript": "First line", "time_offset_minutes": 10},
            {"speaker": "Jordan", "transcript": "Second line", "time_offset_minutes": 20},
        ],
    }
    settings = AppSettings(openai_api_key="x")
    first = generate_block_tts(
        run_id="run_voice",
        story_payload=json.loads(json.dumps(payload)),
        settings=settings,
        tts_tier="cheap",
        story_id_seed="story_seed",
    )
    second = generate_block_tts(
        run_id="run_voice_2",
        story_payload=json.loads(json.dumps(payload)),
        settings=settings,
        tts_tier="cheap",
        story_id_seed="story_seed",
    )

    assert first["voice_map"] == second["voice_map"]
    assert first["tts_tier"] == "cheap"
    assert first["voice_notes"][0]["voice_id"] == first["voice_map"]["Alex"]
    assert first["voice_notes"][1]["voice_id"] == first["voice_map"]["Jordan"]
    assert first["voice_notes"][0]["local_audio_path"].endswith(".mp3")
