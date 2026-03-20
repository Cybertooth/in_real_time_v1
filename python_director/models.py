from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ProviderType(str, Enum):
    GEMINI = "GEMINI"
    OPENAI = "OPENAI"
    ANTHROPIC = "ANTHROPIC"
    OPENROUTER = "OPENROUTER"


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class BlockExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class BlockType(str, Enum):
    CREATIVE_OUTLINER = "creative_outliner"
    PLANNER = "planner"
    CONTINUITY_AUDITOR = "continuity_auditor"
    DECOMPOSER = "decomposer"
    DROP_DIRECTOR = "drop_director"
    GENERATOR = "generator"
    COUNCIL_MEMBER = "council_member"
    COUNCIL_JUDGE = "council_judge"


class BlockConfig(BaseModel):
    provider: ProviderType = ProviderType.GEMINI
    model_name: Optional[str] = None
    use_pipeline_default_model: bool = False
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
    default_models: dict[str, str] = Field(
        default_factory=lambda: {
            ProviderType.GEMINI.value: "gemini-2.5-flash",
            ProviderType.OPENAI.value: "gpt-5.4-mini",
        }
    )
    blocks: list[PipelineBlock] = Field(default_factory=list)


class PipelineCatalogItem(BaseModel):
    key: str
    name: str
    description: str = ""
    updated_at: Optional[str] = None
    block_count: int = 0


class AppSettings(BaseModel):
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    google_application_credentials: Optional[str] = None


class SettingsStatus(BaseModel):
    gemini_configured: bool
    openai_configured: bool
    anthropic_configured: bool
    openrouter_configured: bool
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
    status: BlockExecutionStatus = BlockExecutionStatus.PENDING
    response_schema_name: Optional[str] = None
    temperature: float
    input_blocks: list[str] = Field(default_factory=list)
    resolved_prompt: str = ""
    resolved_inputs: dict[str, Any] = Field(default_factory=dict)
    output: Optional[Any] = None
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    elapsed_ms: Optional[float] = None


class RunTimelineEntry(BaseModel):
    block_id: str
    event_type: str = "artifact_drop"  # e.g., journal, email, chat, receipt
    story_day: int = 1
    story_time: str = "09:00 AM"
    title: str = ""
    content: Optional[dict[str, Any]] = None


class RunStats(BaseModel):
    total_words: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    block_count: int = 0
    success_rate: float = 0.0
    average_tension_score: float | None = None
    character_mentions: dict[str, int] = Field(default_factory=dict)


class RunSummary(BaseModel):
    run_id: str
    timestamp: str
    pipeline_name: str
    status: RunStatus = RunStatus.SUCCEEDED
    final_title: Optional[str] = None
    block_count: int = 0
    provider_summary: dict[str, int] = Field(default_factory=dict)
    artifact_counts: dict[str, float | int] = Field(default_factory=dict)
    final_metrics: dict[str, float | int] = Field(default_factory=dict)
    mode: str = "dry_run"
    error_message: Optional[str] = None


class RunResult(RunSummary):
    current_block_id: Optional[str] = None
    outputs: dict[str, Any] = Field(default_factory=dict)
    final_output: Optional[Any] = None
    block_sequence: list[str] = Field(default_factory=list)
    block_traces: dict[str, BlockTrace] = Field(default_factory=dict)
    artifacts: list[ArtifactFile] = Field(default_factory=list)
    timeline: list[RunTimelineEntry] = Field(default_factory=list)
    stats: RunStats = Field(default_factory=RunStats)


class RunProgress(BaseModel):
    run_id: str
    timestamp: str
    pipeline_name: str
    status: RunStatus
    mode: str = "dry_run"
    block_count: int = 0
    current_block_id: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    final_title: Optional[str] = None
    final_metrics: dict[str, float | int] = Field(default_factory=dict)
    block_sequence: list[str] = Field(default_factory=list)
    block_traces: dict[str, BlockTrace] = Field(default_factory=dict)
    timeline: list[RunTimelineEntry] = Field(default_factory=list)
    stats: RunStats = Field(default_factory=RunStats)


class RunPipelineRequest(BaseModel):
    run_id: Optional[str] = None
    pipeline: Optional[PipelineDefinition] = None
    persist_pipeline: bool = True
    seed_prompt: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class PipelineSnapshotRequest(BaseModel):
    pipeline: PipelineDefinition
    label: Optional[str] = None


class NamedPipelineSaveRequest(BaseModel):
    name: str
    pipeline: PipelineDefinition
    set_active: bool = True


class NamedPipelineLoadRequest(BaseModel):
    name: str
    set_active: bool = True


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
    pipeline_catalog: list[PipelineCatalogItem] = Field(default_factory=list)
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


class BrainstormCritique(BaseModel):
    strengths: list[str]
    missed_opportunities: list[str]
    realism_risks: list[str]
    twist_opportunities: list[str]
    artifact_opportunities: list[str]
    actionable_rewrites: list[str]


class ContinuityIssue(BaseModel):
    severity: str
    category: str
    description: str
    evidence: str
    fix_instruction: str


class ContinuityAudit(BaseModel):
    continuity_score: int
    contradictions: list[ContinuityIssue]
    unresolved_clues: list[str]
    motivation_breaks: list[str]
    high_risk_notes: list[str]
    release_recommendation: str


class QuietWindow(BaseModel):
    start_time_minutes: int
    end_time_minutes: int
    purpose: str


class DropEvent(BaseModel):
    event_id: str
    time_offset_minutes: int
    intensity: str
    channel: str
    summary: str
    objective: str


class DropPlan(BaseModel):
    events: list[DropEvent]
    quiet_windows: list[QuietWindow]
    cliffhanger_targets: list[str]


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


class SocialPost(BaseModel):
    platform: str  # "instagram", "twitter", "facebook", "tiktok"
    author: str
    handle: str
    content: str
    likes: int = 0
    comments: int = 0
    time_offset_minutes: int


class PhoneCallLine(BaseModel):
    speaker: str
    text: str


class PhoneCall(BaseModel):
    caller: str
    receiver: str
    duration_seconds: int = 0
    lines: list[PhoneCallLine]
    time_offset_minutes: int


class GroupChatMessage(BaseModel):
    sender: str
    text: str
    time_offset_minutes: int = 0


class GroupChatThread(BaseModel):
    platform: str  # "whatsapp", "telegram", "imessage"
    group_name: str
    members: list[str]
    messages: list[GroupChatMessage]
    time_offset_minutes: int  # time of first message


class StoryGenerated(BaseModel):
    story_title: str
    journals: list[JournalEntry]
    chats: list[ChatMessage]
    emails: list[EmailMessage]
    receipts: list[ReceiptItem]
    voice_notes: list[VoiceNote]
    social_posts: list[SocialPost] = Field(default_factory=list)
    phone_calls: list[PhoneCall] = Field(default_factory=list)
    group_chats: list[GroupChatThread] = Field(default_factory=list)


SCHEMA_MAP = {
    "BrainstormCritique": BrainstormCritique,
    "StoryPlan": StoryPlan,
    "StoryCritique": StoryCritique,
    "SceneList": SceneList,
    "ContinuityAudit": ContinuityAudit,
    "DropPlan": DropPlan,
    "StoryGenerated": StoryGenerated,
}

# Re-export new artifact types for use in other modules
__all__ = [
    "SocialPost", "PhoneCallLine", "PhoneCall", "GroupChatMessage", "GroupChatThread",
]
