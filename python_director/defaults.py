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
You are developing a premium, real-time found-phone thriller for mobile delivery.
Goal: produce a high-potential narrative blueprint optimized for 48 hours of staggered reveal.

Requirements:
1) Define one central hidden truth that explains all major events.
2) Create 4-6 core characters with conflicting goals, private secrets, and relationship tensions.
3) Build a clue ladder with at least 10 clues, at least 3 red herrings, and at least 2 late-stage reversals.
4) Include real-time cadence: quiet windows, escalating interruptions, and 3 major spike events.
5) Ensure every major beat can manifest as believable phone artifacts (journal, chat, email, receipt, voice note).

Output format (plain text sections):
- Premise
- Hidden Truth
- Character Web
- 48h Beat Timeline
- Clue Ladder (clue, where discovered, payoff beat)
- Spike Events
- Risks to coherence
""".strip()

PLANNER_PROMPT = """
Convert the provided creative outline into a production-ready StoryPlan.
Preserve ambition, but prioritize coherence and payoff.

Non-negotiables:
- Character actions must match motivation and prior knowledge.
- Core conflict must escalate through the 3 acts.
- Twist must be foreshadowed by earlier signals.
- Background lore must directly pressure current events.
- Story must support serialized real-time delivery with anticipation between drops.

Before finalizing, self-check:
- Any timeline contradictions?
- Any character acting out-of-character?
- Any missing setup for major payoff?
If yes, repair before output.
""".strip()

CRITIC_PROMPT = """
You are a senior story editor doing a release-gate review.

Evaluate StoryPlan on:
- Continuity consistency
- Tension curve and pacing rhythm
- Clue/payoff fairness
- Character credibility
- Artifact potential (can this become compelling phone-native content?)

For each weakness, provide:
- Severity (High/Medium/Low)
- Why it damages user engagement
- Concrete fix instruction

Prioritize top 7 fixes by expected impact.
Reject generic advice.
""".strip()

PLAN_REVISION_PROMPT = """
Revise the StoryPlan using the critique.
Objective: structural upgrade, not cosmetic rewrite.

Rules:
- Apply all High severity fixes.
- Keep what already works; do not rewrite stable sections unnecessarily.
- Strengthen foreshadowing for twist and clue chain.
- Improve pacing by alternating pressure spikes and breathing windows.
- Preserve realism of character communication behaviors.

Final self-check:
- No unresolved High severity issue.
- No contradiction in character intent or chronology.
- Stronger act transitions than previous version.
""".strip()

SCENE_DECOMPOSITION_PROMPT = """
Break the final StoryPlan into scene blocks for real-time release design.

Constraints:
- Timeline must be strictly chronological across 48 hours.
- Mix calm investigative windows and high-intensity interruption windows.
- Every scene must specify artifact expectations that are plausible for that moment.
- Ensure at least 3 interruption spikes, 2 deceptive calm periods, and 1 pre-climax acceleration sequence.
- Scene descriptions must include narrative purpose (setup, pressure, reveal, misdirect, payoff).

Avoid filler scenes that do not move either conflict or clue chain.
""".strip()

CONTINUITY_AUDIT_PROMPT = """
Perform a continuity release check on the StoryPlan.

Objectives:
- Detect contradictions in timeline, character knowledge, and motivation.
- Detect clue setup/payoff breaks.
- Identify high-risk sections likely to reduce trust or immersion.

Output strict ContinuityAudit schema.
If no contradiction exists, return an empty contradictions list and a high continuity_score.
Do not invent issues just to fill fields.
""".strip()

DROP_DIRECTOR_PROMPT = """
Create a real-time delivery DropPlan from StoryPlan and SceneList.

Rules:
- Plan timed events that feel notification-worthy.
- Balance interruption spikes with quiet windows to preserve anticipation.
- Ensure cliffhanger targets are spread across the 48-hour arc.
- Keep event summaries concise and operational for CMS scheduling.

Output strict DropPlan schema.
""".strip()

ARTIFACT_GENERATION_PROMPT = """
Generate final phone-native artifacts from StoryPlan, SceneList, ContinuityAudit, and DropPlan.

Quality rules:
- Each character must have distinct language patterns.
- Chats should feel like real texting cadence.
- Emails should match sender role and context.
- Journals should reflect psychological progression over time.
- Voice notes should carry spoken realism and emotional texture.
- Artifact content must align with chronology and known facts.
- Embed discoverable clues without blunt exposition.
- Each major drop should reveal, reframe, or raise risk.

Anti-generic rules:
- No repetitive phrasing across artifacts.
- No summary-narrator tone inside artifacts.
- No contradictory knowledge leaks.

Output must strictly match StoryGenerated schema.
time_offset_minutes must fit scene boundaries.
""".strip()

PROVIDER_MODELS: dict[str, list[str]] = {
    ProviderType.GEMINI.value: [
        "gemini-3.1-pro-preview",
        "gemini-3.0-flash-preview",
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    ],
    ProviderType.OPENAI.value: [
        "gpt-5.4",
        "gpt-5.4-mini",
        "gpt-5.4-pro",
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
                prompt_template="Convert this outline into StoryPlan:\n\n{{creative_brainstorm}}",
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
                prompt_template="Review this StoryPlan:\n\n{{structural_plan}}",
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
        BlockType.CONTINUITY_AUDITOR: BlockTemplate(
            type=BlockType.CONTINUITY_AUDITOR,
            name="Continuity Auditor",
            description="Checks timeline, clue chain, and character consistency before generation.",
            config=BlockConfig(
                provider=ProviderType.GEMINI,
                model_name="gemini-2.5-flash",
                temperature=0.2,
                system_instruction=CONTINUITY_AUDIT_PROMPT,
                prompt_template="Audit this StoryPlan for release readiness:\n\n{{revised_plan_pass_2}}",
                response_mime_type="application/json",
                response_schema_name="ContinuityAudit",
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
                prompt_template=(
                    "Create SceneList from StoryPlan:\n\n{{revised_plan_pass_2}}\n\n"
                    "Continuity notes:\n{{continuity_audit}}"
                ),
                response_mime_type="application/json",
                response_schema_name="SceneList",
            ),
        ),
        BlockType.DROP_DIRECTOR: BlockTemplate(
            type=BlockType.DROP_DIRECTOR,
            name="Drop Director",
            description="Designs notification-worthy drop cadence and quiet windows.",
            config=BlockConfig(
                provider=ProviderType.GEMINI,
                model_name="gemini-2.5-flash",
                temperature=0.4,
                system_instruction=DROP_DIRECTOR_PROMPT,
                prompt_template=(
                    "StoryPlan:\n{{revised_plan_pass_2}}\n\n"
                    "SceneList:\n{{scene_decomposition}}\n\n"
                    "Create DropPlan."
                ),
                response_mime_type="application/json",
                response_schema_name="DropPlan",
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
                    "Continuity Audit:\n{{continuity_audit}}\n\n"
                    "Scenes:\n{{scene_decomposition}}\n\n"
                    "Drop Plan:\n{{drop_director}}\n\n"
                    "Generate StoryGenerated artifacts."
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
                BlockType.CONTINUITY_AUDITOR,
                block_id="continuity_audit",
                input_blocks=["revised_plan_pass_2"],
            ),
            build_block_from_template(
                BlockType.DECOMPOSER,
                block_id="scene_decomposition",
                input_blocks=["revised_plan_pass_2", "continuity_audit"],
            ),
            build_block_from_template(
                BlockType.DROP_DIRECTOR,
                block_id="drop_director",
                input_blocks=["revised_plan_pass_2", "scene_decomposition"],
            ),
            build_block_from_template(
                BlockType.GENERATOR,
                block_id="final_artifact_generation",
                input_blocks=[
                    "revised_plan_pass_2",
                    "continuity_audit",
                    "scene_decomposition",
                    "drop_director",
                ],
            ),
        ],
    )
