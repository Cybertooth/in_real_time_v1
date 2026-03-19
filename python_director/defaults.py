from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

if __package__:
    from .models import (
        BlockConfig,
        BlockTemplate,
        BlockType,
        PipelineBlock,
        PipelineDefinition,
        ProviderType,
    )
else:
    from models import (
        BlockConfig,
        BlockTemplate,
        BlockType,
        PipelineBlock,
        PipelineDefinition,
        ProviderType,
    )

CREATIVE_OUTLINER_PROMPT = """
You are a visionary, unrestricted creative mastermind. Your goal is to brainstorm a massive, sprawling, multi-character 'found phone' thriller.
Forget about JSON structure. Burn all constraints. Write a long, immersive, and gritty story outline including:
- Deep background lore about a systemic conspiracy or cosmic horror.
- Multiple intersecting character journeys (at least 3-4 distinct POVs).
- Narrative beats that feel meaty and substantial, enough to fill hours of engagement.
- A mind-bending, paradigm-shifting twist that recontextualizes everything in the final 6 hours.
- Ideas for realistic digital artifacts: long chat threads, multi-paragraph journals, and emotionally raw voice notes.
Focus on atmosphere, tension, and world-building. Be as detailed and creative as possible.
""".strip()

PLANNER_PROMPT = """
You are an elite, masterful thrill-writer and narrative architect.
Given the Creative Outline provided, your task is to map this sprawling story into a structured StoryPlan.
Ensure you capture all characters, the core conflict, the background lore, and the act-based summaries accurately from the outline.
The final story must remain massive in scope and highly detailed.
""".strip()

CRITIC_PROMPT = """
You are a ruthless editor. Critique the provided Story Plan for a massive found-phone mystery.
Ensure that the story is expansive and meaty enough to hold attention for hours.
Focus intensely on character consistency across multiple POVs, whether the background lore is deep enough, and if the pacing balances extensive deep-dives with frantic bursts.
Are there enough distinct character journeys? Are voice notes utilized effectively? Let no superficial element pass. Be harsh. Provide actionable improvements.
""".strip()

PLAN_REVISION_PROMPT = """
You are revising the Story Plan based on the ruthless editor's critique.
Incorporate all actionable improvements. Deepen the character arcs, expand the subplots, fix pacing issues, and enhance the twist so it truly lands.
The resulting story plan must be significantly more expansive, complex, and meaty.
Output the upgraded StoryPlan.
""".strip()

SCENE_DECOMPOSITION_PROMPT = """
You are a master game narrative designer. Break the finalized, sprawling 48-hour Story Plan into detailed Scene Blocks.
A Scene Block represents a cluster of activity.
Crucially, you must schedule massive content chunks:
- Chat sequences must be extensive, representing minutes of continuous real-time texting.
- Journals and voice notes must represent deep, multi-paragraph reflections.
A scene must specify what artifacts (Journal, Chat, Email, Receipt, VoiceNote) are expected.
Leave large gaps of time between intense scenes to build tension.
""".strip()

ARTIFACT_GENERATION_PROMPT = """
You are the final execution writer tasked with generating an absolutely massive found-phone dataset.
Given the final Story Plan and the Scene List, write the actual digital artifacts.
Critical requirements:
- Chat threads must be extraordinarily long, representing a few minutes of continuous messaging.
- Journals must be extremely detailed, with multiple long paragraphs of deep introspection.
- Voice notes must contain realistic spoken-word transcripts with pauses, stuttering, and raw emotion.
- Emails must feel detailed and plausible, including longer threads when needed.
Ensure time_offset_minutes aligns with the scene list boundaries.
Output the final JSON strictly matching the target schema.
""".strip()

PROVIDER_MODELS: dict[str, list[str]] = {
    ProviderType.GEMINI.value: [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    ],
    ProviderType.OPENAI.value: [
        "gpt-5",
        "gpt-5-mini",
        "gpt-4.1",
        "gpt-4.1-mini",
    ],
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _template_library() -> dict[BlockType, BlockTemplate]:
    return {
        BlockType.CREATIVE_OUTLINER: BlockTemplate(
            type=BlockType.CREATIVE_OUTLINER,
            name="Creative Brainstorm",
            description="Produces the unconstrained story outline that seeds the rest of the pipeline.",
            config=BlockConfig(
                provider=ProviderType.GEMINI,
                model_name="gemini-2.5-flash",
                temperature=1.0,
                system_instruction=CREATIVE_OUTLINER_PROMPT,
                prompt_template="Brainstorm the initial massive story outline.",
            ),
        ),
        BlockType.PLANNER: BlockTemplate(
            type=BlockType.PLANNER,
            name="Structural Plan",
            description="Turns the brainstorm into a structured StoryPlan.",
            config=BlockConfig(
                provider=ProviderType.GEMINI,
                model_name="gemini-2.5-flash",
                temperature=0.7,
                system_instruction=PLANNER_PROMPT,
                prompt_template="Map this creative outline into a structured StoryPlan:\n\n{{creative_brainstorm}}",
                response_mime_type="application/json",
                response_schema_name="StoryPlan",
            ),
        ),
        BlockType.CRITIC: BlockTemplate(
            type=BlockType.CRITIC,
            name="Plan Critic",
            description="Applies editorial pressure and returns structured critique notes.",
            config=BlockConfig(
                provider=ProviderType.GEMINI,
                model_name="gemini-2.5-flash",
                temperature=0.7,
                system_instruction=CRITIC_PROMPT,
                prompt_template="Critique this plan:\n\n{{structural_plan}}",
                response_mime_type="application/json",
                response_schema_name="StoryCritique",
            ),
        ),
        BlockType.REVISER: BlockTemplate(
            type=BlockType.REVISER,
            name="Plan Revision",
            description="Revises the StoryPlan based on the previous critique block.",
            config=BlockConfig(
                provider=ProviderType.GEMINI,
                model_name="gemini-2.5-flash",
                temperature=0.8,
                system_instruction=PLAN_REVISION_PROMPT,
                prompt_template=(
                    "Original Plan:\n{{structural_plan}}\n\n"
                    "Critique to apply:\n{{plan_critique_pass_1}}"
                ),
                response_mime_type="application/json",
                response_schema_name="StoryPlan",
            ),
        ),
        BlockType.DECOMPOSER: BlockTemplate(
            type=BlockType.DECOMPOSER,
            name="Scene Decomposition",
            description="Breaks the final plan into scene clusters and expected artifact types.",
            config=BlockConfig(
                provider=ProviderType.GEMINI,
                model_name="gemini-2.5-flash",
                temperature=0.5,
                system_instruction=SCENE_DECOMPOSITION_PROMPT,
                prompt_template="Break this plan into a scene list:\n\n{{revised_plan_pass_2}}",
                response_mime_type="application/json",
                response_schema_name="SceneList",
            ),
        ),
        BlockType.GENERATOR: BlockTemplate(
            type=BlockType.GENERATOR,
            name="Final Artifact Generation",
            description="Generates the journals, chats, emails, receipts, and voice notes for the experience.",
            config=BlockConfig(
                provider=ProviderType.GEMINI,
                model_name="gemini-2.5-pro",
                temperature=0.7,
                system_instruction=ARTIFACT_GENERATION_PROMPT,
                prompt_template=(
                    "Final Plan:\n{{revised_plan_pass_2}}\n\n"
                    "Scenes:\n{{scene_decomposition}}\n\n"
                    "Write the final artifacts."
                ),
                response_mime_type="application/json",
                response_schema_name="StoryGenerated",
            ),
        ),
    }


def get_block_templates() -> list[BlockTemplate]:
    return [template.model_copy(deep=True) for template in _template_library().values()]


def build_block_from_template(
    block_type: BlockType,
    *,
    block_id: str,
    name: str | None = None,
    description: str | None = None,
    input_blocks: list[str] | None = None,
) -> PipelineBlock:
    template = _template_library()[block_type]
    return PipelineBlock(
        id=block_id,
        name=name or template.name,
        description=description or template.description,
        type=block_type,
        input_blocks=list(input_blocks or []),
        config=deepcopy(template.config),
    )


def get_default_pipeline() -> PipelineDefinition:
    return PipelineDefinition(
        name="Found Phone Director",
        description="Low-code story generation pipeline for found-phone narratives.",
        updated_at=utc_now_iso(),
        blocks=[
            build_block_from_template(
                BlockType.CREATIVE_OUTLINER,
                block_id="creative_brainstorm",
                description="Starts the pipeline with the broadest possible story thinking.",
            ),
            build_block_from_template(
                BlockType.PLANNER,
                block_id="structural_plan",
                input_blocks=["creative_brainstorm"],
            ),
            build_block_from_template(
                BlockType.CRITIC,
                block_id="plan_critique_pass_1",
                name="Plan Critique Pass 1",
                input_blocks=["structural_plan"],
            ),
            build_block_from_template(
                BlockType.REVISER,
                block_id="revised_plan_pass_1",
                name="Revision Pass 1",
                input_blocks=["structural_plan", "plan_critique_pass_1"],
            ),
            build_block_from_template(
                BlockType.CRITIC,
                block_id="plan_critique_pass_2",
                name="Plan Critique Pass 2",
                input_blocks=["revised_plan_pass_1"],
            ),
            build_block_from_template(
                BlockType.REVISER,
                block_id="revised_plan_pass_2",
                name="Revision Pass 2",
                input_blocks=["revised_plan_pass_1", "plan_critique_pass_2"],
            ),
            build_block_from_template(
                BlockType.DECOMPOSER,
                block_id="scene_decomposition",
                input_blocks=["revised_plan_pass_2"],
            ),
            build_block_from_template(
                BlockType.GENERATOR,
                block_id="final_artifact_generation",
                input_blocks=["revised_plan_pass_2", "scene_decomposition"],
            ),
        ],
    )
