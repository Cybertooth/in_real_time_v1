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
6) ENGAGEMENT DENSITY — communication must happen in bursts, not isolated pings:
   - Chat / IM exchanges must be back-and-forth conversations (5-15 messages each) not single texts.
   - Emails must be substantial multi-paragraph messages, not one-liners.
   - Act 1 (first ~16 hours) must be the densest activity window to hook users early.
   - No silent gaps longer than 90 minutes in Act 1.
   - Plan at least 2 rapid-fire "flurry" sequences where 3+ artifact types overlap within 30 minutes.

Output format (plain text sections):
- Premise
- Hidden Truth
- Character Web
- 48h Beat Timeline
- Clue Ladder (clue, where discovered, payoff beat)
- Spike Events
- Engagement Density Plan (burst clusters, Act 1 density map)
- Risks to coherence
""".strip()

COUNCIL_MEMBER_BRAINSTORM_PROMPT = """
You are an independent expert serving on a creative council reviewing a found-phone thriller brainstorm.
You review the material with fresh eyes and produce your own unbiased critique.

Your mandate:
- Evaluate story logic, clue architecture, character depth, and phone-native believability.
- Evaluate ENGAGEMENT DENSITY: are chat exchanges bursty back-and-forth conversations (5-15 messages)
  or isolated pings? Are emails substantial or stubs? Is Act 1 dense enough to retain users?
  Flag any dead zones in Act 1 where the user would stop checking the app.
- Identify missed opportunities that could dramatically improve the concept.
- Be specific and evidence-based. Cite actual elements from the brainstorm.
- Push hard. Generic praise wastes council time.

Return strict BrainstormCritique schema.
""".strip()

COUNCIL_BRAINSTORM_JUDGE_PROMPT = """
You are the Chief Creative Arbitrator. You have received independent critiques of a brainstorm
from multiple AI council members, each with a different training perspective.

Your job:
1. Synthesize the council feedback — find consensus, highlight unique insights, flag contradictions.
2. Produce a substantially upgraded brainstorm integrating the highest-impact recommendations.
3. Where council members disagree, apply your own creative judgment.
4. Preserve what is strong. Fix what is weak. Cut what is redundant.

Output plain text sections:
- Revised Premise
- Revised Hidden Truth
- Revised Character Web
- Revised 48h Beat Timeline
- Revised Clue Ladder
- Revised Spike Events
- Council synthesis notes (consensus that emerged, unique insights surfaced)
""".strip()

COUNCIL_MEMBER_PLAN_PROMPT = """
You are an independent story editor serving on a creative council reviewing a structural StoryPlan
for a found-phone thriller.

Your mandate:
- Evaluate continuity, tension curve, clue/payoff fairness, character credibility, and artifact potential.
- Evaluate ENGAGEMENT DENSITY: does each scene produce enough artifacts to keep the user engaged?
  Are IM conversations full back-and-forth exchanges or single messages? Is Act 1 front-loaded with
  dense activity to retain users in the first session? Flag any gap > 90 min in Act 1 as High severity.
- Identify structural weaknesses with specific fix instructions.
- Flag High severity issues that break immersion, Medium that reduce engagement, Low that polish.
- Be specific. Cite plan elements. Avoid generic advice.

Return strict StoryCritique schema.
""".strip()

COUNCIL_PLAN_JUDGE_PROMPT = """
You are the Chief Story Architect. You have received independent structural critiques of a StoryPlan
from multiple AI council members.

Your job:
1. Synthesize the council feedback — find consensus structural issues and extract unique insights.
2. Produce a substantially upgraded StoryPlan applying all High-severity fixes and the best Medium fixes.
3. Where council members disagree, use your architectural judgment to choose the stronger path.
4. Strengthen foreshadowing, tighten act transitions, and deepen character credibility.

Return strict StoryPlan schema.
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

ENGAGEMENT DENSITY rules (critical):
- IM / chat conversations MUST be back-and-forth exchanges of 5-15 messages minimum.
  A single isolated text message is only acceptable if it is an explicit plot point.
- Emails MUST be multi-paragraph (3+ paragraphs) with real substance.
- Act 1 (first ~960 time_offset_minutes) must be the densest section.
  No gap between consecutive artifacts should exceed 90 minutes in Act 1.
- Create at least 2 "flurry" windows where 3+ artifacts land within 30 minutes.
- Journal entries should be multi-paragraph reflections, not bullet summaries.
- Voice notes should be substantial monologues (50+ words), not one-liners.

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
        "gemini-3-flash-preview",
        "gemini-3.1-flash-lite-preview",
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    ],
    ProviderType.OPENAI.value: [
        "gpt-5.4",
        "gpt-5.4-mini",
        "gpt-5.4-pro",
        "gpt-5.4-nano",
    ],
}

PIPELINE_DEFAULT_MODELS: dict[str, str] = {
    ProviderType.GEMINI.value: "gemini-3-flash-preview",
    ProviderType.OPENAI.value: "gpt-5.4-mini",
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
                model_name=PIPELINE_DEFAULT_MODELS[ProviderType.GEMINI.value],
                use_pipeline_default_model=True,
                temperature=1.0,
                system_instruction=CREATIVE_OUTLINER_PROMPT,
                prompt_template="Brainstorm the initial massive story outline.",
            ),
        ),
        BlockType.COUNCIL_MEMBER: BlockTemplate(
            type=BlockType.COUNCIL_MEMBER,
            name="Council Member",
            description="Independent reviewer in a council. Runs in parallel with other council members.",
            config=BlockConfig(
                provider=ProviderType.GEMINI,
                model_name=PIPELINE_DEFAULT_MODELS[ProviderType.GEMINI.value],
                use_pipeline_default_model=True,
                temperature=0.5,
                system_instruction=COUNCIL_MEMBER_BRAINSTORM_PROMPT,
                prompt_template="Review this brainstorm:\n\n{{creative_brainstorm}}",
                response_mime_type="application/json",
                response_schema_name="BrainstormCritique",
            ),
        ),
        BlockType.COUNCIL_JUDGE: BlockTemplate(
            type=BlockType.COUNCIL_JUDGE,
            name="Council Judge",
            description="Collates all council member critiques and produces the synthesized final output.",
            config=BlockConfig(
                provider=ProviderType.OPENAI,
                model_name="gpt-5.4",
                use_pipeline_default_model=False,
                temperature=0.8,
                system_instruction=COUNCIL_BRAINSTORM_JUDGE_PROMPT,
                prompt_template=(
                    "Original brainstorm:\n{{creative_brainstorm}}\n\n"
                    "Council critiques:\n{{council_brainstorm_gemini_pro}}\n\n"
                    "Synthesize and produce the upgraded brainstorm."
                ),
            ),
        ),
        BlockType.PLANNER: BlockTemplate(
            type=BlockType.PLANNER,
            name="Structural Plan",
            description="Turns the brainstorm into a structured StoryPlan.",
            config=BlockConfig(
                provider=ProviderType.GEMINI,
                model_name=PIPELINE_DEFAULT_MODELS[ProviderType.GEMINI.value],
                use_pipeline_default_model=True,
                temperature=0.7,
                system_instruction=PLANNER_PROMPT,
                prompt_template="Convert this outline into StoryPlan:\n\n{{council_brainstorm_judge}}",
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
                model_name=PIPELINE_DEFAULT_MODELS[ProviderType.GEMINI.value],
                use_pipeline_default_model=True,
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
                model_name=PIPELINE_DEFAULT_MODELS[ProviderType.GEMINI.value],
                use_pipeline_default_model=True,
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
                model_name=PIPELINE_DEFAULT_MODELS[ProviderType.GEMINI.value],
                use_pipeline_default_model=True,
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
                use_pipeline_default_model=False,
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
    config_overrides: dict[str, object] | None = None,
) -> PipelineBlock:
    template = _template_library()[block_type]
    block = PipelineBlock(
        id=block_id,
        name=name or template.name,
        description=description or template.description,
        type=block_type,
        input_blocks=list(input_blocks or []),
        config=deepcopy(template.config),
    )
    if config_overrides:
        block.config = block.config.model_copy(update=config_overrides)
    return block


def get_default_pipeline() -> PipelineDefinition:
    return PipelineDefinition(
        name="Found Phone Director",
        description="Low-code story generation pipeline for found-phone narratives.",
        updated_at=utc_now_iso(),
        default_models=deepcopy(PIPELINE_DEFAULT_MODELS),
        blocks=[
            # ── Stage 1: Creative brainstorm ──────────────────────────────────────
            build_block_from_template(
                BlockType.CREATIVE_OUTLINER,
                block_id="creative_brainstorm",
                description="Starts the pipeline with the broadest possible story thinking.",
            ),
            # ── Stage 2: Brainstorm council (3 models in parallel) ────────────────
            build_block_from_template(
                BlockType.COUNCIL_MEMBER,
                block_id="council_brainstorm_gemini_pro",
                name="Council: Gemini Pro Review",
                description="Independent brainstorm critique from Gemini Pro.",
                input_blocks=["creative_brainstorm"],
                config_overrides={
                    "system_instruction": COUNCIL_MEMBER_BRAINSTORM_PROMPT,
                    "provider": ProviderType.GEMINI,
                    "model_name": "gemini-3.1-pro-preview",
                    "use_pipeline_default_model": False,
                    "temperature": 0.7,
                    "prompt_template": "Review this brainstorm:\n\n{{creative_brainstorm}}",
                    "response_mime_type": "application/json",
                    "response_schema_name": "BrainstormCritique",
                },
            ),
            build_block_from_template(
                BlockType.COUNCIL_MEMBER,
                block_id="council_brainstorm_gemini_flash",
                name="Council: Gemini Flash Review",
                description="Independent brainstorm critique from Gemini Flash.",
                input_blocks=["creative_brainstorm"],
                config_overrides={
                    "system_instruction": COUNCIL_MEMBER_BRAINSTORM_PROMPT,
                    "provider": ProviderType.GEMINI,
                    "model_name": None,
                    "use_pipeline_default_model": True,
                    "temperature": 0.5,
                    "prompt_template": "Review this brainstorm:\n\n{{creative_brainstorm}}",
                    "response_mime_type": "application/json",
                    "response_schema_name": "BrainstormCritique",
                },
            ),
            build_block_from_template(
                BlockType.COUNCIL_MEMBER,
                block_id="council_brainstorm_openai",
                name="Council: OpenAI Review",
                description="Independent brainstorm critique from OpenAI.",
                input_blocks=["creative_brainstorm"],
                config_overrides={
                    "system_instruction": COUNCIL_MEMBER_BRAINSTORM_PROMPT,
                    "provider": ProviderType.OPENAI,
                    "model_name": None,
                    "use_pipeline_default_model": True,
                    "temperature": 0.5,
                    "prompt_template": "Review this brainstorm:\n\n{{creative_brainstorm}}",
                    "response_mime_type": "application/json",
                    "response_schema_name": "BrainstormCritique",
                },
            ),
            # ── Stage 3: Brainstorm council judge ─────────────────────────────────
            build_block_from_template(
                BlockType.COUNCIL_JUDGE,
                block_id="council_brainstorm_judge",
                name="Council Judge: Brainstorm Synthesis",
                description="Collates all brainstorm council critiques and produces the upgraded brainstorm.",
                input_blocks=[
                    "creative_brainstorm",
                    "council_brainstorm_gemini_pro",
                    "council_brainstorm_gemini_flash",
                    "council_brainstorm_openai",
                ],
                config_overrides={
                    "system_instruction": COUNCIL_BRAINSTORM_JUDGE_PROMPT,
                    "provider": ProviderType.OPENAI,
                    "model_name": "gpt-5.4",
                    "use_pipeline_default_model": False,
                    "temperature": 0.8,
                    "prompt_template": (
                        "Original brainstorm:\n{{creative_brainstorm}}\n\n"
                        "Council member 1 (Gemini Pro):\n{{council_brainstorm_gemini_pro}}\n\n"
                        "Council member 2 (Gemini Flash):\n{{council_brainstorm_gemini_flash}}\n\n"
                        "Council member 3 (OpenAI):\n{{council_brainstorm_openai}}\n\n"
                        "Synthesize the council feedback and produce the upgraded brainstorm."
                    ),
                },
            ),
            # ── Stage 4: Structural planner ───────────────────────────────────────
            build_block_from_template(
                BlockType.PLANNER,
                block_id="structural_plan",
                input_blocks=["council_brainstorm_judge"],
            ),
            # ── Stage 5: Plan council (3 models in parallel) ──────────────────────
            build_block_from_template(
                BlockType.COUNCIL_MEMBER,
                block_id="council_plan_gemini_pro",
                name="Council: Plan Review (Gemini Pro)",
                description="Independent StoryPlan critique from Gemini Pro.",
                input_blocks=["structural_plan"],
                config_overrides={
                    "system_instruction": COUNCIL_MEMBER_PLAN_PROMPT,
                    "provider": ProviderType.GEMINI,
                    "model_name": "gemini-3.1-pro-preview",
                    "use_pipeline_default_model": False,
                    "temperature": 0.5,
                    "prompt_template": "Review this StoryPlan:\n\n{{structural_plan}}",
                    "response_mime_type": "application/json",
                    "response_schema_name": "StoryCritique",
                },
            ),
            build_block_from_template(
                BlockType.COUNCIL_MEMBER,
                block_id="council_plan_gemini_flash",
                name="Council: Plan Review (Gemini Flash)",
                description="Independent StoryPlan critique from Gemini Flash.",
                input_blocks=["structural_plan"],
                config_overrides={
                    "system_instruction": COUNCIL_MEMBER_PLAN_PROMPT,
                    "provider": ProviderType.GEMINI,
                    "model_name": None,
                    "use_pipeline_default_model": True,
                    "temperature": 0.5,
                    "prompt_template": "Review this StoryPlan:\n\n{{structural_plan}}",
                    "response_mime_type": "application/json",
                    "response_schema_name": "StoryCritique",
                },
            ),
            build_block_from_template(
                BlockType.COUNCIL_MEMBER,
                block_id="council_plan_openai",
                name="Council: Plan Review (OpenAI)",
                description="Independent StoryPlan critique from OpenAI.",
                input_blocks=["structural_plan"],
                config_overrides={
                    "system_instruction": COUNCIL_MEMBER_PLAN_PROMPT,
                    "provider": ProviderType.OPENAI,
                    "model_name": None,
                    "use_pipeline_default_model": True,
                    "temperature": 0.5,
                    "prompt_template": "Review this StoryPlan:\n\n{{structural_plan}}",
                    "response_mime_type": "application/json",
                    "response_schema_name": "StoryCritique",
                },
            ),
            # ── Stage 6: Plan council judge ───────────────────────────────────────
            build_block_from_template(
                BlockType.COUNCIL_JUDGE,
                block_id="council_plan_judge",
                name="Council Judge: Plan Synthesis",
                description="Collates all plan council critiques and produces the upgraded StoryPlan.",
                input_blocks=[
                    "structural_plan",
                    "council_plan_gemini_pro",
                    "council_plan_gemini_flash",
                    "council_plan_openai",
                ],
                config_overrides={
                    "system_instruction": COUNCIL_PLAN_JUDGE_PROMPT,
                    "provider": ProviderType.GEMINI,
                    "model_name": "gemini-3.1-pro-preview",
                    "use_pipeline_default_model": False,
                    "temperature": 0.7,
                    "prompt_template": (
                        "Original StoryPlan:\n{{structural_plan}}\n\n"
                        "Council member 1 (Gemini Pro):\n{{council_plan_gemini_pro}}\n\n"
                        "Council member 2 (Gemini Flash):\n{{council_plan_gemini_flash}}\n\n"
                        "Council member 3 (OpenAI):\n{{council_plan_openai}}\n\n"
                        "Synthesize the council feedback and produce the upgraded StoryPlan."
                    ),
                    "response_mime_type": "application/json",
                    "response_schema_name": "StoryPlan",
                },
            ),
            # ── Stage 7: Continuity audit ─────────────────────────────────────────
            build_block_from_template(
                BlockType.CONTINUITY_AUDITOR,
                block_id="continuity_audit",
                input_blocks=["council_plan_judge"],
                config_overrides={
                    "prompt_template": "Audit this StoryPlan for release readiness:\n\n{{council_plan_judge}}",
                },
            ),
            # ── Stage 8: Scene decomposition ──────────────────────────────────────
            build_block_from_template(
                BlockType.DECOMPOSER,
                block_id="scene_decomposition",
                input_blocks=["council_plan_judge", "continuity_audit"],
                config_overrides={
                    "prompt_template": (
                        "Create SceneList from StoryPlan:\n\n{{council_plan_judge}}\n\n"
                        "Continuity notes:\n{{continuity_audit}}"
                    ),
                },
            ),
            # ── Stage 9: Drop director ────────────────────────────────────────────
            build_block_from_template(
                BlockType.DROP_DIRECTOR,
                block_id="drop_director",
                input_blocks=["council_plan_judge", "scene_decomposition"],
                config_overrides={
                    "prompt_template": (
                        "StoryPlan:\n{{council_plan_judge}}\n\n"
                        "SceneList:\n{{scene_decomposition}}\n\n"
                        "Create DropPlan."
                    ),
                },
            ),
            # ── Stage 10: Final artifact generation ───────────────────────────────
            build_block_from_template(
                BlockType.GENERATOR,
                block_id="final_artifact_generation",
                input_blocks=[
                    "council_plan_judge",
                    "continuity_audit",
                    "scene_decomposition",
                    "drop_director",
                ],
                config_overrides={
                    "prompt_template": (
                        "Final Plan:\n{{council_plan_judge}}\n\n"
                        "Continuity Audit:\n{{continuity_audit}}\n\n"
                        "Scenes:\n{{scene_decomposition}}\n\n"
                        "Drop Plan:\n{{drop_director}}\n\n"
                        "Generate StoryGenerated artifacts."
                    ),
                },
            ),
        ],
    )
