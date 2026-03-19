from __future__ import annotations

from pathlib import Path

import pytest

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
    def generate_content(self, config, contents):
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
