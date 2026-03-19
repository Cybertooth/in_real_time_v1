from __future__ import annotations

import json
from pathlib import Path

import pytest

from python_director.defaults import get_default_pipeline
from python_director.logic import PipelineRunner, compare_final_outputs
from python_director.models import (
    AppSettings,
    BlockConfig,
    BlockType,
    CompareRunsRequest,
    PipelineBlock,
    PipelineDefinition,
    ProviderType,
    RunResult,
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
            model_name="gemini-2.5-flash",
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
    assert "creative_brainstorm_rewrite" in ids
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
    assert "brainstorm_council_logic" in ids
    assert "brainstorm_council_audience" in ids
    assert "brainstorm_council_artifacts" in ids
    assert "creative_brainstorm_rewrite" in ids
    assert pipeline.default_models["GEMINI"] == "gemini-2.5-flash"


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
