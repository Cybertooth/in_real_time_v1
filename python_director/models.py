from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


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
    BRAINSTORM_CRITIC = "brainstorm_critic"
    BRAINSTORM_REWRITER = "brainstorm_rewriter"
    PLANNER = "planner"
    CRITIC = "critic"
    REVISER = "reviser"
    CONTINUITY_AUDITOR = "continuity_auditor"
    DECOMPOSER = "decomposer"
    DROP_DIRECTOR = "drop_director"
    GENERATOR = "generator"
    COUNCIL_MEMBER = "council_member"
    COUNCIL_JUDGE = "council_judge"
    IMAGE_GENERATOR = "image_generator"
    TTS_GENERATOR = "tts_generator"
    VISUAL_BIBLE = "visual_bible"
    IMAGE_PROMPT_DIRECTOR = "image_prompt_director"


class StoryMode(str, Enum):
    LIVE = "live"
    SCHEDULED = "scheduled"
    SUBSCRIPTION = "subscription"


class TTSTier(str, Enum):
    PREMIUM = "premium"
    CHEAP = "cheap"


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
    image_provider: ProviderType = ProviderType.GEMINI
    default_image_models: dict[str, str] = Field(
        default_factory=lambda: {
            ProviderType.GEMINI.value: "gemini-3.1-flash-image-preview",
            ProviderType.OPENAI.value: "gpt-image-1.5-2025-12-16",
            ProviderType.OPENROUTER.value: "bytedance-seed/seedream-4.5",
            ProviderType.ANTHROPIC.value: "",
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
    local_image_path: Optional[str] = None


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
    seed_prompt: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    setup: str = ""
    characters: list[CharacterInfo] = Field(default_factory=list)
    headline_image_prompt: Optional[str] = None
    headline_image_path: Optional[str] = None
    story_id: Optional[str] = None


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
    story_id: Optional[str] = None


class RunPipelineRequest(BaseModel):
    run_id: Optional[str] = None
    pipeline: Optional[PipelineDefinition] = None
    persist_pipeline: bool = True
    seed_prompt: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class UploadRunRequest(BaseModel):
    story_mode: StoryMode = StoryMode.LIVE
    scheduled_start_at: Optional[datetime] = None
    tts_tier: TTSTier = TTSTier.PREMIUM

    @model_validator(mode="after")
    def _validate_schedule_requirements(self) -> "UploadRunRequest":
        if self.story_mode == StoryMode.SCHEDULED and self.scheduled_start_at is None:
            raise ValueError("scheduled_start_at is required when story_mode is 'scheduled'.")
        if self.story_mode != StoryMode.SCHEDULED:
            self.scheduled_start_at = None
        return self


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


class PipelineResetRequest(BaseModel):
    template_key: str = "full_fledged"


class RerunRequest(BaseModel):
    seed_prompt: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    use_original_seed: bool = True  # if True and no override, use stored seed/tags


class CompareRunsRequest(BaseModel):
    baseline_run_id: str
    candidate_run_id: str


class MetricDelta(BaseModel):
    label: str
    baseline: float | int
    candidate: float | int
    delta: float | int


class RegenerateImageRequest(BaseModel):
    event_type: str
    index: int = 0
    new_prompt: str


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


class ResetTemplateInfo(BaseModel):
    key: str
    name: str
    description: str


class StudioBootstrap(BaseModel):
    pipeline: PipelineDefinition
    pipeline_catalog: list[PipelineCatalogItem] = Field(default_factory=list)
    settings: SettingsPayload
    run_summaries: list[RunSummary]
    schemas: list[str]
    block_types: list[BlockType]
    block_templates: list[BlockTemplate]
    reset_templates: list[ResetTemplateInfo] = Field(default_factory=list)
    provider_models: dict[str, list[str]]


class CharacterInfo(BaseModel):
    name: str
    background: str
    arc_summary: str


class StoryPlan(BaseModel):
    title: str
    characters: list[CharacterInfo] = Field(default_factory=list)
    core_conflict: str = ""
    background_lore: str = ""
    the_twist: str = ""
    act_1_summary: str = ""
    act_2_summary: str = ""
    act_3_summary: str = ""


class StoryCritique(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    pacing_issues: str = ""
    character_consistency_issues: str = ""
    twist_impact_analysis: str = ""
    actionable_improvements: list[str] = Field(default_factory=list)


class SceneBlock(BaseModel):
    scene_id: str
    start_time_minutes: int = 0
    end_time_minutes: int = 0
    description: str = ""
    expected_artifacts: list[str] = Field(default_factory=list)


class SceneList(BaseModel):
    scenes: list[SceneBlock] = Field(default_factory=list)


class BrainstormCritique(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    missed_opportunities: list[str] = Field(default_factory=list)
    realism_risks: list[str] = Field(default_factory=list)
    twist_opportunities: list[str] = Field(default_factory=list)
    artifact_opportunities: list[str] = Field(default_factory=list)
    actionable_rewrites: list[str] = Field(default_factory=list)


class ContinuityIssue(BaseModel):
    severity: str
    category: str
    description: str
    evidence: str
    fix_instruction: str


class ContinuityAudit(BaseModel):
    continuity_score: int = 0
    contradictions: list[ContinuityIssue] = Field(default_factory=list)
    unresolved_clues: list[str] = Field(default_factory=list)
    motivation_breaks: list[str] = Field(default_factory=list)
    high_risk_notes: list[str] = Field(default_factory=list)
    release_recommendation: str = ""


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
    events: list[DropEvent] = Field(default_factory=list)
    quiet_windows: list[QuietWindow] = Field(default_factory=list)
    cliffhanger_targets: list[str] = Field(default_factory=list)


class JournalEntry(BaseModel):
    title: str
    body: str
    time_offset_minutes: int
    is_locked: bool = False
    unlock_password: Optional[str] = None
    image_prompt: Optional[str] = None
    local_image_path: Optional[str] = None


class ChatMessage(BaseModel):
    senderId: str
    text: str
    isProtagonist: bool
    time_offset_minutes: int
    image_prompt: Optional[str] = None
    local_image_path: Optional[str] = None


class EmailMessage(BaseModel):
    sender: str
    subject: str
    body: str
    time_offset_minutes: int
    is_locked: bool = False
    unlock_password: Optional[str] = None
    image_prompt: Optional[str] = None
    local_image_path: Optional[str] = None


class ReceiptItem(BaseModel):
    merchantName: str
    amount: float
    description: str
    time_offset_minutes: int


class VoiceNote(BaseModel):
    speaker: str
    transcript: str
    time_offset_minutes: int
    image_prompt: Optional[str] = None
    local_image_path: Optional[str] = None
    voice_id: Optional[str] = None
    local_audio_path: Optional[str] = None
    audio_url: Optional[str] = None


class SocialPost(BaseModel):
    platform: str  # "instagram", "twitter", "facebook", "tiktok"
    author: str
    handle: str
    content: str
    likes: int = 0
    comments: int = 0
    time_offset_minutes: int
    image_prompt: Optional[str] = None
    local_image_path: Optional[str] = None


class PhoneCallLine(BaseModel):
    speaker: str
    text: str


class PhoneCall(BaseModel):
    caller: str
    receiver: str
    duration_seconds: int = 0
    lines: list[PhoneCallLine] = Field(default_factory=list)
    time_offset_minutes: int = 0


class GroupChatMessage(BaseModel):
    sender: str
    text: str
    time_offset_minutes: int = 0


class GroupChatThread(BaseModel):
    platform: str  # "whatsapp", "telegram", "imessage"
    group_name: str
    members: list[str] = Field(default_factory=list)
    messages: list[GroupChatMessage] = Field(default_factory=list)
    time_offset_minutes: int = 0  # time of first message


class GalleryPhoto(BaseModel):
    photo_id: str
    tier: str  # "atmospheric" | "diegetic" | "document"
    subject: str
    caption: Optional[str] = None
    time_offset_minutes: int = 0
    image_prompt: Optional[str] = None
    local_image_path: Optional[str] = None


class StoryGenerated(BaseModel):
    story_title: str
    headline_image_prompt: Optional[str] = None
    headline_image_path: Optional[str] = None
    journals: list[JournalEntry] = Field(default_factory=list)
    chats: list[ChatMessage] = Field(default_factory=list)
    emails: list[EmailMessage] = Field(default_factory=list)
    receipts: list[ReceiptItem] = Field(default_factory=list)
    voice_notes: list[VoiceNote] = Field(default_factory=list)
    social_posts: list[SocialPost] = Field(default_factory=list)
    phone_calls: list[PhoneCall] = Field(default_factory=list)
    group_chats: list[GroupChatThread] = Field(default_factory=list)
    photo_gallery: list[GalleryPhoto] = Field(default_factory=list)


class CharacterVisual(BaseModel):
    name: str
    appearance: str  # canonical description: age, build, hair, style, signature items


class LocationVisual(BaseModel):
    name: str
    visual_brief: str  # lighting, palette, mood, distinguishing details


class PlannedShot(BaseModel):
    shot_id: str
    tier: str  # "atmospheric" | "diegetic" | "document"
    subject: str
    narrative_purpose: str
    artifact_hint: str  # artifact type ("social_post", "journal", etc.) or "gallery"
    artifact_narrative_moment: str  # prose description of the story moment for matching
    suggested_prompt: str


class VisualBible(BaseModel):
    aesthetic_style: str
    color_palette: str
    era_and_setting: str
    characters: list[CharacterVisual] = Field(default_factory=list)
    key_locations: list[LocationVisual] = Field(default_factory=list)
    shot_list: list[PlannedShot] = Field(default_factory=list)


class ArtifactImagePatch(BaseModel):
    collection: str  # "journals" | "chats" | "emails" | "social_posts" | "receipts" | "voice_notes"
    index: int
    image_prompt: str


class StoryGeneratedImagePatch(BaseModel):
    headline_image_prompt: Optional[str] = None
    artifact_patches: list[ArtifactImagePatch] = Field(default_factory=list)
    photo_gallery: list[GalleryPhoto] = Field(default_factory=list)


SCHEMA_MAP = {
    "BrainstormCritique": BrainstormCritique,
    "StoryPlan": StoryPlan,
    "StoryCritique": StoryCritique,
    "SceneList": SceneList,
    "ContinuityAudit": ContinuityAudit,
    "DropPlan": DropPlan,
    "StoryGenerated": StoryGenerated,
    "VisualBible": VisualBible,
    "StoryGeneratedImagePatch": StoryGeneratedImagePatch,
}

# Re-export new artifact types for use in other modules
__all__ = [
    "SocialPost", "PhoneCallLine", "PhoneCall", "GroupChatMessage", "GroupChatThread",
    "GalleryPhoto", "CharacterVisual", "LocationVisual", "PlannedShot", "VisualBible",
    "ArtifactImagePatch", "StoryGeneratedImagePatch",
]
