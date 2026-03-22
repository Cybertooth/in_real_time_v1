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
5) Ensure every major beat can manifest as believable phone artifacts across ALL channel types:
   - journals (private reflections, diary entries)
   - direct chats / IM exchanges (back-and-forth conversations)
   - emails (formal or semi-formal communications)
   - receipts (transactions that reveal movement or purchases)
   - voice notes (recorded audio memos)
   - social media posts (Instagram, Twitter, Facebook, TikTok — public-facing character facades)
   - phone call transcripts (calls with caller, receiver, and dialogue lines)
   - group chat threads (WhatsApp/Telegram/iMessage group conversations)
6) ENGAGEMENT DENSITY — communication must happen in bursts, not isolated pings:
   - Chat / IM exchanges must be back-and-forth conversations (5-15 messages each) not single texts.
   - Group chats should have 8-15 messages from multiple participants, showing social dynamics.
   - Emails must be substantial multi-paragraph messages, not one-liners.
   - Social posts reveal the public character facade vs private reality — contrast is key.
   - Phone calls expose confrontations, revelations, or key plot turns through dialogue.
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
- Social Media Strategy (which characters post publicly and what facade they maintain)
- Group Chat Dynamics (which group chats exist, who is in them, key revelations)
- Phone Call Moments (calls that must happen and why)
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

You MUST populate ALL of the following fields in your JSON response:
- title: the story title
- characters: list of characters (each with name, background, arc_summary)
- core_conflict: the central dramatic conflict driving the story
- background_lore: world-building and backstory that pressures current events
- the_twist: the major reveal or turn — must be foreshadowed from the start
- act_1_summary: setup, introduction of characters and conflict (first third)
- act_2_summary: escalation, complications, mid-point turn (middle third)
- act_3_summary: climax, resolution, aftermath (final third)

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
Generate a LARGE, RICH set of phone-native artifacts from StoryPlan, SceneList, ContinuityAudit, and DropPlan.
Target: ~5,000 words of story content spread across ALL artifact types.

MANDATORY QUANTITY TARGETS (minimum, more is better):
- journals: 8+ entries, each 200-400 words (multi-paragraph reflections, not bullet lists)
- chats: 3+ conversations of 10-15 back-and-forth messages each
- emails: 6+ emails with 3+ substantial paragraphs each
- receipts: 4+ receipts (reveal character movement, spending, or secret activities)
- voice_notes: 4+ voice notes, each 80-150 words (spoken monologue realism)
- social_posts: 8+ posts across Instagram/Twitter/Facebook/TikTok from different characters
  (contrast public facade with private reality)
- phone_calls: 3+ calls with full dialogue transcripts (10-20 lines each)
  (use calls for confrontations, urgent revelations, or key plot turns)
- group_chats: 2+ group chat threads (WhatsApp/Telegram/iMessage) with 10-15 messages each
  from multiple participants (show group dynamics, rumors, panic, coordination)

QUALITY RULES:
- Each character must have distinct voice and language patterns.
- Direct chats feel like real texting: short bursts, typos, emojis where appropriate.
- Emails match sender role (formal cop = formal email; teenager = casual/brief).
- Journals show psychological progression — fear, suspicion, grief, denial, resolve.
- Voice notes capture spoken hesitation, self-correction, emotional rawness.
- Social posts reveal the public facade characters maintain while private reality unravels.
- Phone calls expose raw confrontations that characters wouldn't commit to text.
- Group chats show social pressure, gossip, collective panic or denial.
- All artifact content must align with chronology and character knowledge at that point in time.
- Embed discoverable clues without blunt exposition.
- Each major drop should reveal, reframe, or raise risk.

ENGAGEMENT DENSITY RULES (critical):
- Act 1 (first ~960 time_offset_minutes) must be the DENSEST section — hook users in session 1.
- No gap between consecutive artifacts should exceed 90 minutes in Act 1.
- Create at least 3 "flurry" windows where 4+ artifacts land within 30 minutes.
- IM / chat conversations MUST be back-and-forth (10-15 messages). Never isolated single texts.
- Group chats must have real multi-person dynamics, not monologues.

IMAGE GENERATION RULES:
- Include an `image_prompt` for at least 30% of social media posts, describing the exact photograph.
- Add an `image_prompt` for key journals or emails where a visual clue or attached document is mentioned.
- You MUST provide a `headline_image_prompt` attribute at the root of your response describing the overarching atmospheric header image for the story.
- The `image_prompt` and `headline_image_prompt` must strictly be visual high-quality literal descriptions of the image content.

ANTI-GENERIC RULES:
- No repetitive phrasing across artifacts.
- No summary-narrator tone inside artifacts. Stay in character voice.
- No contradictory knowledge leaks (character can't know something they haven't learned yet).
- Avoid clichés: "I can't believe this is happening", "Everything changed that day", etc.

VISUAL BIBLE (authoritative source for all image_prompt fields):
{{visual_bible}}

IMAGE PROMPT RULES (applies when writing any image_prompt field):
- Describe the scene visually and literally — never include character names, only their physical
  descriptions from the Visual Bible above.
- Enforce the aesthetic_style, color_palette, and era_and_setting from the Visual Bible.
- For each entry in the Visual Bible shot_list where artifact_hint matches the current artifact type,
  use the artifact_narrative_moment to identify the correct artifact and fulfill that shot.
- Do NOT create photo_gallery entries — leave standalone shots (artifact_hint = "gallery") for the
  Image Prompt Director block that runs after you.

Output must strictly match StoryGenerated schema.
time_offset_minutes must fit scene boundaries across the 48-hour arc.
""".strip()

VISUAL_BIBLE_PROMPT = """
You are the Visual Director for a found-phone thriller. Given the final StoryPlan and SceneList,
produce a lightweight but precise visual canon that will govern all image generation for this story.

Your output must be strict VisualBible schema.

Guidelines:
- `aesthetic_style`: one sentence — overall cinematic tone (e.g. "gritty iPhone vérité, underexposed, muted greens").
- `color_palette`: dominant mood colors and lighting quality (2-3 sentences max).
- `era_and_setting`: time period, geography, and environment (1-2 sentences).
- `characters`: for each main character, write ONE dense paragraph covering age, build, hair color/style,
  typical clothing style, and 1-2 signature physical details. Be specific and visual — no vague adjectives.
- `key_locations`: for each significant location, describe its lighting, texture, and mood in 2-3 sentences.
- `shot_list`: plan 15-25 images that tell the visual story. For each shot:
  - `shot_id`: short slug (e.g. "headline_dusk", "alex_cafe_photo", "evidence_note")
  - `tier`: "atmospheric" (cinematic mood), "diegetic" (character took this photo), or "document"
  - `subject`: what/who is the main subject
  - `narrative_purpose`: why this image exists in the story
  - `artifact_hint`: which artifact type this belongs to ("social_post", "journal", "email", "chat",
    "receipt", "voice_note") or "gallery" for standalone camera-roll / atmospheric images
  - `artifact_narrative_moment`: a precise prose description of the story moment this image captures —
    specific enough that the artifact generator can match it to the right artifact instance
  - `suggested_prompt`: a visual description suitable for an image generation model — describe the scene
    literally, never use character names, only physical descriptions

Ensure a mix of tiers. Include at least one "atmospheric" headline shot, 5+ "diegetic" photos
(things characters would post on Instagram or share in chat), and 2+ "document" shots.
""".strip()

IMAGE_PROMPT_DIRECTOR_PROMPT = """
You are the Image Prompt Director. You receive a fully-generated StoryGenerated payload (as JSON)
and the VisualBible for this story. Your job is a focused visual consistency pass.

Output must strictly match StoryGeneratedImagePatch schema.

Your tasks:
1. Review EVERY artifact that has an `image_prompt` field (journals, chats, emails, social_posts,
   receipts, voice_notes). For each one:
   - Replace any character name references with their canonical appearance from the VisualBible.
   - Enforce the aesthetic_style, color_palette, and era_and_setting from the VisualBible.
   - Make prompts literal and visual — no abstract concepts, no story spoilers, just what the camera sees.
   - Add these as `artifact_patches` entries in your output.

2. Review the VisualBible shot_list for any shots with `artifact_hint = "gallery"` that are NOT already
   covered by existing artifact image_prompts. Add each as a `photo_gallery` entry with:
   - `photo_id`: the shot's `shot_id`
   - `tier`: from the PlannedShot
   - `subject`: from the PlannedShot
   - `caption`: a brief character-voice caption if diegetic (e.g. what the character might write on Instagram),
     null for atmospheric/document
   - `time_offset_minutes`: estimate based on the narrative_purpose and story arc (0-2880 minutes)
   - `image_prompt`: an improved version of `suggested_prompt` refined against the VisualBible

3. Set `headline_image_prompt` to a refined version of the story's headline image prompt if the
   VisualBible or existing StoryGenerated has one, applying Visual Bible style rules.

CRITICAL: Do NOT reproduce the story content. Only output the patch fields described above.
""".strip()

PROVIDER_MODELS: dict[str, list[str]] = {
    ProviderType.GEMINI.value: [
        "gemini-3.1-pro-preview",
        "gemini-3-flash-preview",
        "gemini-3.1-flash-lite-preview",
        "gemini-3.1-flash-image-preview",
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    ],
    ProviderType.OPENAI.value: [
        "gpt-5.4",
        "gpt-5.4-mini",
        "gpt-5.4-pro",
        "gpt-5.4-nano",
        "gpt-image-1.5-2025-12-16",
    ],
    ProviderType.ANTHROPIC.value: [
        "claude-opus-4-6",
        "claude-sonnet-4-6",
        "claude-haiku-4-5-20251001",
        "claude-opus-4-5",
        "claude-sonnet-4-5",
    ],
    ProviderType.OPENROUTER.value: [
        "moonshotai/kimi-k2.5",
        "minimax/minimax-m2.5",
        "qwen/qwen3.5-122b-a10b",
        "qwen/qwen3-235b-a22b",
        "deepseek/deepseek-chat-v3-0324",
        "deepseek/deepseek-r1",
        "mistralai/mistral-large",
        "mistralai/mistral-nemo",
        "nvidia/nemotron-3-super-120b-a12b:free",
        "x-ai/grok-4.1-fast",
        "z-ai/glm-4.5-air:free",
        "bytedance-seed/seedream-4.5",
    ],
}

PIPELINE_DEFAULT_MODELS: dict[str, str] = {
    ProviderType.GEMINI.value: "gemini-3-flash-preview",
    ProviderType.OPENAI.value: "gpt-5.4-mini",
    ProviderType.ANTHROPIC.value: "claude-sonnet-4-6",
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
                model_name="gemini-3.1-pro-preview",
                use_pipeline_default_model=False,
                temperature=1.0,
                system_instruction=CREATIVE_OUTLINER_PROMPT,
                prompt_template="Brainstorm the initial massive story outline. Avoid sci-fi and extra-terrestrial themes. Story should have a lot of inter-personal drama and conflict. There should be opportunity to have lots of conversations.",
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
                model_name=PIPELINE_DEFAULT_MODELS[ProviderType.GEMINI.value],
                use_pipeline_default_model=True,
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
        BlockType.IMAGE_GENERATOR: BlockTemplate(
            type=BlockType.IMAGE_GENERATOR,
            name="Artifact Image Renderer",
            description="Locally generates realistic artifact images using the AI Image models.",
            config=BlockConfig(
                provider=ProviderType.GEMINI,
                model_name="gemini-3.1-flash-image-preview",
                use_pipeline_default_model=False,
                temperature=0.7,
                system_instruction="N/A",
                prompt_template="[Handled dynamically by node payload]",
            ),
        ),
        BlockType.VISUAL_BIBLE: BlockTemplate(
            type=BlockType.VISUAL_BIBLE,
            name="Visual Bible",
            description="Produces the canonical visual canon (character appearances, aesthetic style, shot list) that governs all image generation.",
            config=BlockConfig(
                provider=ProviderType.GEMINI,
                model_name=None,
                use_pipeline_default_model=True,
                temperature=0.5,
                system_instruction=VISUAL_BIBLE_PROMPT,
                prompt_template=(
                    "StoryPlan:\n{{council_plan_judge}}\n\n"
                    "SceneList:\n{{scene_decomposition}}\n\n"
                    "Produce the VisualBible."
                ),
                response_mime_type="application/json",
                response_schema_name="VisualBible",
            ),
        ),
        BlockType.IMAGE_PROMPT_DIRECTOR: BlockTemplate(
            type=BlockType.IMAGE_PROMPT_DIRECTOR,
            name="Image Prompt Director",
            description="Refines all image prompts for character consistency, applies the Visual Bible, and adds standalone gallery shots.",
            config=BlockConfig(
                provider=ProviderType.GEMINI,
                model_name=None,
                use_pipeline_default_model=True,
                temperature=0.4,
                system_instruction=IMAGE_PROMPT_DIRECTOR_PROMPT,
                prompt_template=(
                    "Visual Bible:\n{{visual_bible}}\n\n"
                    "StoryGenerated (full JSON):\n{{final_artifact_generation}}\n\n"
                    "Produce the StoryGeneratedImagePatch."
                ),
                response_mime_type="application/json",
                response_schema_name="StoryGeneratedImagePatch",
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
            build_block_from_template(
                BlockType.COUNCIL_MEMBER,
                block_id="council_brainstorm_claude",
                name="Council: Claude Review",
                description="Independent brainstorm critique from Claude.",
                input_blocks=["creative_brainstorm"],
                config_overrides={
                    "system_instruction": COUNCIL_MEMBER_BRAINSTORM_PROMPT,
                    "provider": ProviderType.ANTHROPIC,
                    "model_name": "claude-sonnet-4-6",
                    "use_pipeline_default_model": False,
                    "temperature": 0.6,
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
                    "council_brainstorm_claude",
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
                        "Council member 4 (Claude):\n{{council_brainstorm_claude}}\n\n"
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
            build_block_from_template(
                BlockType.COUNCIL_MEMBER,
                block_id="council_plan_claude",
                name="Council: Plan Review (Claude)",
                description="Independent StoryPlan critique from Claude.",
                input_blocks=["structural_plan"],
                config_overrides={
                    "system_instruction": COUNCIL_MEMBER_PLAN_PROMPT,
                    "provider": ProviderType.ANTHROPIC,
                    "model_name": "claude-sonnet-4-6",
                    "use_pipeline_default_model": False,
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
                    "council_plan_claude",
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
                        "Council member 4 (Claude):\n{{council_plan_claude}}\n\n"
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
            # ── Stage 9: Visual Bible ─────────────────────────────────────────────
            build_block_from_template(
                BlockType.VISUAL_BIBLE,
                block_id="visual_bible",
                input_blocks=["council_plan_judge", "scene_decomposition"],
                config_overrides={
                    "prompt_template": (
                        "StoryPlan:\n{{council_plan_judge}}\n\n"
                        "SceneList:\n{{scene_decomposition}}\n\n"
                        "Produce the VisualBible."
                    ),
                },
            ),
            # ── Stage 10: Drop director ───────────────────────────────────────────
            build_block_from_template(
                BlockType.DROP_DIRECTOR,
                block_id="drop_director",
                input_blocks=["council_plan_judge", "scene_decomposition", "visual_bible"],
                config_overrides={
                    "prompt_template": (
                        "StoryPlan:\n{{council_plan_judge}}\n\n"
                        "SceneList:\n{{scene_decomposition}}\n\n"
                        "Visual Bible:\n{{visual_bible}}\n\n"
                        "Create DropPlan."
                    ),
                },
            ),
            # ── Stage 11: Final artifact generation ───────────────────────────────
            build_block_from_template(
                BlockType.GENERATOR,
                block_id="final_artifact_generation",
                input_blocks=[
                    "council_plan_judge",
                    "continuity_audit",
                    "scene_decomposition",
                    "drop_director",
                    "visual_bible",
                ],
                config_overrides={
                    "prompt_template": (
                        "Final Plan:\n{{council_plan_judge}}\n\n"
                        "Continuity Audit:\n{{continuity_audit}}\n\n"
                        "Scenes:\n{{scene_decomposition}}\n\n"
                        "Drop Plan:\n{{drop_director}}\n\n"
                        "Visual Bible (use for all image_prompt fields):\n{{visual_bible}}\n\n"
                        "Generate StoryGenerated artifacts."
                    ),
                },
            ),
            # ── Stage 12: Image Prompt Director ───────────────────────────────────
            build_block_from_template(
                BlockType.IMAGE_PROMPT_DIRECTOR,
                block_id="image_prompt_director",
                input_blocks=["final_artifact_generation", "visual_bible"],
                config_overrides={
                    "prompt_template": (
                        "Visual Bible:\n{{visual_bible}}\n\n"
                        "StoryGenerated (full JSON):\n{{final_artifact_generation}}\n\n"
                        "Produce the StoryGeneratedImagePatch."
                    ),
                },
            ),
            # ── Stage 13: Image rendering ─────────────────────────────────────────
            build_block_from_template(
                BlockType.IMAGE_GENERATOR,
                block_id="image_generation",
                input_blocks=[
                    "image_prompt_director",
                ],
            ),
        ],
    )
