from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ProviderType(str, Enum):
    GEMINI = "GEMINI"
    OPENAI = "OPENAI"


class BlockType(str, Enum):
    CREATIVE_OUTLINER = "creative_outliner"
    PLANNER = "planner"
    CRITIC = "critic"
    REVISER = "reviser"
    DECOMPOSER = "decomposer"
    GENERATOR = "generator"


class BlockConfig(BaseModel):
    provider: ProviderType = ProviderType.GEMINI
    model_name: str = "gemini-2.5-flash"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    system_instruction: str
    prompt_template: str
    response_mime_type: Optional[str] = None
    response_schema_name: Optional[str] = None


class PipelineBlock(BaseModel):
    id: str
    name: str
    description: str = ""
    type: BlockType
    enabled: bool = True
    config: BlockConfig
    input_blocks: list[str] = Field(default_factory=list)


class PipelineDefinition(BaseModel):
    name: str = "Found Phone Director"
    description: str = ""
    updated_at: Optional[str] = None
    blocks: list[PipelineBlock] = Field(default_factory=list)


class AppSettings(BaseModel):
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    google_application_credentials: Optional[str] = None


class SettingsStatus(BaseModel):
    gemini_configured: bool
    openai_configured: bool
    google_credentials_configured: bool


class SettingsPayload(BaseModel):
    settings: AppSettings
    status: SettingsStatus


class ArtifactFile(BaseModel):
    name: str
    relative_path: str
    size_bytes: int
    content_type: str


class BlockTrace(BaseModel):
    block_id: str
    block_name: str
    block_type: BlockType
    provider: ProviderType
    model_name: str
    response_schema_name: Optional[str] = None
    temperature: float
    input_blocks: list[str] = Field(default_factory=list)
    resolved_prompt: str


class RunSummary(BaseModel):
    run_id: str
    timestamp: str
    pipeline_name: str
    final_title: Optional[str] = None
    block_count: int = 0
    provider_summary: dict[str, int] = Field(default_factory=dict)
    artifact_counts: dict[str, float | int] = Field(default_factory=dict)
    final_metrics: dict[str, float | int] = Field(default_factory=dict)
    mode: str = "dry_run"


class RunResult(RunSummary):
    outputs: dict[str, Any] = Field(default_factory=dict)
    final_output: Optional[Any] = None
    block_sequence: list[str] = Field(default_factory=list)
    block_traces: dict[str, BlockTrace] = Field(default_factory=dict)
    artifacts: list[ArtifactFile] = Field(default_factory=list)


class RunPipelineRequest(BaseModel):
    run_id: Optional[str] = None
    pipeline: Optional[PipelineDefinition] = None
    persist_pipeline: bool = True


class PipelineSnapshotRequest(BaseModel):
    pipeline: PipelineDefinition
    label: Optional[str] = None


class CompareRunsRequest(BaseModel):
    baseline_run_id: str
    candidate_run_id: str


class MetricDelta(BaseModel):
    label: str
    baseline: float | int
    candidate: float | int
    delta: float | int


class RunComparison(BaseModel):
    baseline_run_id: str
    candidate_run_id: str
    baseline_title: Optional[str] = None
    candidate_title: Optional[str] = None
    metrics: list[MetricDelta] = Field(default_factory=list)
    quality_notes: list[str] = Field(default_factory=list)
    baseline_output: Optional[Any] = None
    candidate_output: Optional[Any] = None


class BlockTemplate(BaseModel):
    type: BlockType
    name: str
    description: str
    config: BlockConfig


class StudioBootstrap(BaseModel):
    pipeline: PipelineDefinition
    settings: SettingsPayload
    run_summaries: list[RunSummary]
    schemas: list[str]
    block_types: list[BlockType]
    block_templates: list[BlockTemplate]
    provider_models: dict[str, list[str]]


class CharacterInfo(BaseModel):
    name: str
    background: str
    arc_summary: str


class StoryPlan(BaseModel):
    title: str
    characters: list[CharacterInfo]
    core_conflict: str
    background_lore: str
    the_twist: str
    act_1_summary: str
    act_2_summary: str
    act_3_summary: str


class StoryCritique(BaseModel):
    strengths: list[str]
    weaknesses: list[str]
    pacing_issues: str
    character_consistency_issues: str
    twist_impact_analysis: str
    actionable_improvements: list[str]


class SceneBlock(BaseModel):
    scene_id: str
    start_time_minutes: int
    end_time_minutes: int
    description: str
    expected_artifacts: list[str]


class SceneList(BaseModel):
    scenes: list[SceneBlock]


class JournalEntry(BaseModel):
    title: str
    body: str
    time_offset_minutes: int


class ChatMessage(BaseModel):
    senderId: str
    text: str
    isProtagonist: bool
    time_offset_minutes: int


class EmailMessage(BaseModel):
    sender: str
    subject: str
    body: str
    time_offset_minutes: int


class ReceiptItem(BaseModel):
    merchantName: str
    amount: float
    description: str
    time_offset_minutes: int


class VoiceNote(BaseModel):
    speaker: str
    transcript: str
    time_offset_minutes: int


class StoryGenerated(BaseModel):
    story_title: str
    journals: list[JournalEntry]
    chats: list[ChatMessage]
    emails: list[EmailMessage]
    receipts: list[ReceiptItem]
    voice_notes: list[VoiceNote]


SCHEMA_MAP = {
    "StoryPlan": StoryPlan,
    "StoryCritique": StoryCritique,
    "SceneList": SceneList,
    "StoryGenerated": StoryGenerated,
}
