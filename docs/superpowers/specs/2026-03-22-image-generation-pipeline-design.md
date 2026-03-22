# Image Generation Pipeline Design

**Date:** 2026-03-22
**Status:** Approved (rev 2 — post spec-review)

## Overview

Integrate image generation as a first-class, narratively-motivated concern in the ML pipeline rather than a post-generation afterthought. Introduces a Visual Bible block that plans images top-down (with a shot list), an Image Prompt Director block that enforces consistency before rendering, a photo gallery artifact type, and richer image surfaces in both the Director Studio and Flutter app.

---

## Image Taxonomy — Three Tiers

| Tier | Description | Examples |
|---|---|---|
| `atmospheric` | Cinematic/mood images not tied to a character action | Headline image, scene establishing shots |
| `diegetic` | Photos characters actually took or shared | Instagram posts, camera roll photos, chat image attachments |
| `document` | Physical documents photographed | Scanned receipts, handwritten notes, printed emails |

---

## Pipeline Architecture

The default pipeline (`defaults.py`) gains two new blocks and two existing blocks gain new inputs.

### New: Stage 9 — Visual Bible (`visual_bible`)
- **Position:** After `scene_decomposition`, before `drop_director`
- **Inputs:** `council_plan_judge`, `scene_decomposition`
- **Provider:** Gemini (structured output)
- **BlockType:** `BlockType.VISUAL_BIBLE = "visual_bible"` — add to enum in `models.py`
- **Output schema:** `VisualBible` — add `"VisualBible": VisualBible` to `SCHEMA_MAP`
- **Template library entry required** in `_template_library()` with `VISUAL_BIBLE_PROMPT`, Gemini provider, temperature 0.5
- **Responsibility:** Produce the canonical visual canon for the story (character appearances, location aesthetics, overall style) and a planned shot list that downstream blocks fulfill.

### New: Stage 12 — Image Prompt Director (`image_prompt_director`)
- **Position:** After `final_artifact_generation`, before `image_generation`
- **Inputs:** `final_artifact_generation`, `visual_bible`
- **Provider:** Gemini (structured output)
- **BlockType:** `BlockType.IMAGE_PROMPT_DIRECTOR = "image_prompt_director"` — add to enum in `models.py`
- **Output schema:** `StoryGeneratedImagePatch` (see Data Models — NOT full `StoryGenerated`) — add `"StoryGeneratedImagePatch": StoryGeneratedImagePatch` to `SCHEMA_MAP`
- **Template library entry required** in `_template_library()` with `IMAGE_PROMPT_DIRECTOR_PROMPT`, Gemini provider, temperature 0.4
- **Responsibility:** Audit and refine all `image_prompt` fields. Replace character name references with canonical appearance prose. Fulfill unassigned `shot_list` entries as `photo_gallery` items. Output a **patch** (not the full story), which `logic.py` merges back into the original `StoryGenerated` output.

### Modified: `drop_director`
- Add `"visual_bible"` to `input_blocks`.
- Amend `prompt_template` to include:
  ```
  Visual Bible:\n{{visual_bible}}\n\n
  ```
  before the existing `StoryPlan` and `SceneList` sections.

### Modified: `final_artifact_generation` (GENERATOR)
- Add `"visual_bible"` to `input_blocks`.
- Amend `prompt_template` to include:
  ```
  Visual Bible (use for all image_prompt fields):\n{{visual_bible}}\n\n
  ```
  before the existing prompt sections.

### Modified: `image_generation`
- Change `input_blocks` from `["final_artifact_generation"]` to `["image_prompt_director"]`.
- `generate_block_images()` reads the merged `StoryGenerated`-shaped payload from the `image_prompt_director` output slot (after the merge step in `logic.py`).

**Pipeline order (complete, using actual block IDs):**
1. `creative_brainstorm`
2. `council_brainstorm_gemini_pro`, `council_brainstorm_gemini_flash`, `council_brainstorm_openai`, `council_brainstorm_claude` (parallel)
3. `council_brainstorm_judge`
4. `structural_plan`
5. `council_plan_gemini_pro`, `council_plan_gemini_flash`, `council_plan_openai`, `council_plan_claude` (parallel)
6. `council_plan_judge`
7. `continuity_audit`
8. `scene_decomposition`
9. `visual_bible` ← NEW
10. `drop_director` (gains `visual_bible` input)
11. `final_artifact_generation` (gains `visual_bible` input)
12. `image_prompt_director` ← NEW
13. `image_generation` (input changes to `image_prompt_director`)

---

## Data Models

### New: `VisualBible`

```python
class CharacterVisual(BaseModel):
    name: str
    appearance: str  # one paragraph: age, build, hair, style, signature items

class LocationVisual(BaseModel):
    name: str
    visual_brief: str  # lighting, palette, mood, distinguishing details

class PlannedShot(BaseModel):
    shot_id: str
    tier: str                              # "atmospheric" | "diegetic" | "document"
    subject: str                           # e.g. "headline", character name, location name
    narrative_purpose: str
    artifact_hint: str                     # artifact type ("social_post", "journal", etc.) or "gallery"
    artifact_narrative_moment: str         # prose description of the story moment — used by GENERATOR and
                                           # Image Prompt Director to match shots to specific artifact instances
                                           # (best-effort; director reconciles unmatched shots)
    suggested_prompt: str

class VisualBible(BaseModel):
    aesthetic_style: str
    color_palette: str
    era_and_setting: str
    characters: list[CharacterVisual]
    key_locations: list[LocationVisual]
    shot_list: list[PlannedShot]
```

### New: `GalleryPhoto`

Must be defined **before** `StoryGenerated` in `models.py` (it is a nested model). Does **not** need a `SCHEMA_MAP` entry — it is embedded in `StoryGenerated`.

```python
class GalleryPhoto(BaseModel):
    photo_id: str
    tier: str                      # "atmospheric" | "diegetic" | "document"
    subject: str
    caption: Optional[str]         # character-voice caption if diegetic
    time_offset_minutes: int
    image_prompt: Optional[str]
    local_image_path: Optional[str]
```

### New: `StoryGeneratedImagePatch`

The `image_prompt_director` block outputs this lightweight patch, **not** a full `StoryGenerated`. This avoids the risk of the LLM truncating or paraphrasing story content when asked to reproduce the full payload.

```python
class ArtifactImagePatch(BaseModel):
    collection: str   # "journals" | "chats" | "emails" | "social_posts" | "receipts" | "voice_notes"
    index: int
    image_prompt: str

class StoryGeneratedImagePatch(BaseModel):
    headline_image_prompt: Optional[str] = None
    artifact_patches: list[ArtifactImagePatch] = Field(default_factory=list)
    photo_gallery: list[GalleryPhoto] = Field(default_factory=list)
```

`logic.py` merges the patch into the original `StoryGenerated` dict after `image_prompt_director` completes (see Backend Logic — Merge Step).

### Modified: `StoryGenerated`

Add `photo_gallery` field. `GalleryPhoto` must appear before this class in `models.py`.

```python
class StoryGenerated(BaseModel):
    # ... all existing fields unchanged ...
    photo_gallery: list[GalleryPhoto] = Field(default_factory=list)
```

### `SCHEMA_MAP` additions

```python
"VisualBible": VisualBible,
"StoryGeneratedImagePatch": StoryGeneratedImagePatch,
```

### `BlockType` additions (in `models.py` enum)

```python
VISUAL_BIBLE = "visual_bible"
IMAGE_PROMPT_DIRECTOR = "image_prompt_director"
```

---

## Backend Logic Changes

### Merge step for `image_prompt_director` in `logic.py`

After the `image_prompt_director` block executes and produces a `StoryGeneratedImagePatch`, `logic.py` must merge the patch into the `final_artifact_generation` output before storing the `image_prompt_director` output slot. Pseudocode:

```python
if block.type == BlockType.IMAGE_PROMPT_DIRECTOR:
    patch = output  # StoryGeneratedImagePatch
    base = copy.deepcopy(outputs["final_artifact_generation"])
    if hasattr(base, "model_dump"):
        base = base.model_dump()
    # Apply headline prompt
    if patch.headline_image_prompt:
        base["headline_image_prompt"] = patch.headline_image_prompt
    # Apply per-artifact patches
    for ap in patch.artifact_patches:
        items = base.get(ap.collection, [])
        if 0 <= ap.index < len(items):
            items[ap.index]["image_prompt"] = ap.image_prompt
    # Add gallery
    base["photo_gallery"] = [p.model_dump() for p in patch.photo_gallery]
    output = base  # merged StoryGenerated dict stored in outputs["image_prompt_director"]
```

The `image_generation` block reads `input_blocks[0]` = `"image_prompt_director"`, which now contains the merged payload. No other changes to the `IMAGE_GENERATOR` execution path.

**Critical insertion point:** The merge must happen **inside `_run_one_block()`**, after the `StoryGeneratedImagePatch` is deserialized from the LLM response but **before** `outputs[block.id] = output` is written. In practice this means adding an `elif block.type == BlockType.IMAGE_PROMPT_DIRECTOR:` branch (analogous to the existing `if block.type == BlockType.IMAGE_GENERATOR:` branch at line 614) that performs the merge and reassigns `output = base` before the common `outputs[block.id] = output` assignment executes. Placing the merge after that assignment would store the patch-only value in `outputs["image_prompt_director"]`, causing `image_generation` to receive an incomplete payload.

### `generate_block_images()` in `logic.py`

Extend the existing collection loop to also iterate `photo_gallery`:

```python
# Existing collections (unchanged)
for collection_name in ["journals", "chats", "emails", "receipts", "voice_notes", "social_posts"]:
    ...

# New: photo_gallery
for i, item in enumerate(story_payload.get("photo_gallery", [])):
    prompt = item.get("image_prompt")
    if prompt and not item.get("local_image_path"):
        path = _gen_and_save(prompt, f"gallery_{i}.jpg")
        if path:
            item["local_image_path"] = path
```

### `upload_to_firestore()` in `logic.py`

Add a dedicated `upload_gallery()` function — do **not** reuse `upload_collection()`, which maps to a flat artifact subcollection structure and computes `unlockTimestamp` from `time_offset_minutes`.

`photo_gallery` items **are** time-gated in Flutter (they participate in the existing `clockProvider` unlock mechanism). Therefore `upload_gallery()` must:
- Upload each image to Firebase Storage (`stories/{id}/gallery_{i}.jpg`).
- Compute `unlockTimestamp` from `time_offset_minutes` using the same logic as `upload_collection()`.
- Write each item to `stories/{id}/gallery` Firestore subcollection with **exactly** these fields:
  `{tier, subject, caption, time_offset_minutes, unlockTimestamp, imageUrl}`.
  - `time_offset_minutes` is written as-is from the model (snake_case, integer).
  - `unlockTimestamp` is computed from `time_offset_minutes` using the same start-time logic as `upload_collection()`.
  - `imageUrl` replaces `local_image_path`.
  - `photo_id` and `image_prompt` are **not** written to Firestore (not needed by Flutter).
  - Note: `GalleryPhoto` does not carry an `unlockTimestamp` field — it is computed exclusively at upload time. The Pydantic model is correct as-is.

### `regenerate-image` endpoint in `api.py`

Add `"gallery": "photo_gallery"` to the `collection_map`. The filename scheme for gallery images is `gallery_{index}.jpg`. The `target_item["image_prompt"]` pattern works as-is since `GalleryPhoto` has an `image_prompt` field.

### New prompts in `defaults.py`

**`VISUAL_BIBLE_PROMPT`** — instructs model to produce a lightweight visual canon + shot list from StoryPlan + SceneList. Must include instruction: "For each `PlannedShot`, set `artifact_narrative_moment` to a prose description of the specific story moment this image captures, so the generator can match it to the right artifact."

**`IMAGE_PROMPT_DIRECTOR_PROMPT`** — instructs model to:
1. Read the provided `StoryGeneratedImagePatch`-compatible output format description.
2. Review each artifact collection in the serialized `StoryGenerated` for existing `image_prompt` fields.
3. Refine prompts: replace character name references with their canonical appearance from the Visual Bible; enforce consistent aesthetic style, palette, and era.
4. Identify any unassigned `shot_list` entries (by matching `artifact_narrative_moment` to artifacts); add them as `photo_gallery` entries.
5. Output strictly as `StoryGeneratedImagePatch`.

### `ARTIFACT_GENERATION_PROMPT` amendment

Add section at the end of the existing prompt:

```
VISUAL BIBLE (authoritative source for all image_prompt fields):
{{visual_bible}}

IMAGE PROMPT RULES:
- When writing an `image_prompt`, describe the scene visually — never include character names, only physical descriptions from the Visual Bible.
- For each entry in the Visual Bible `shot_list` where `artifact_hint` matches the current artifact type, fulfill that shot in the matching artifact using `artifact_narrative_moment` to identify the correct artifact.
- Do NOT create `photo_gallery` entries — leave standalone shots (artifact_hint = "gallery") for the Image Prompt Director.
```

### Dry-run

No behavior change — images already render locally in dry-run. Both new blocks (`visual_bible`, `image_prompt_director`) are text-only LLM calls.

---

## Director Studio (Admin UI)

### New: Images tab in RunDetail

Three sections:
1. **Headline** — single large image with prompt + regenerate button.
2. **Gallery** — grid of all `photo_gallery` items. Each tile: tier badge (`atmospheric` / `diegetic` / `document`), caption, prompt, regenerate button.
3. **Artifact images** — flat list of per-artifact images grouped by type (social posts, journals, emails, chats).

### Regenerate endpoint extension

`POST /runs/{run_id}/regenerate-image` — add `"gallery": "photo_gallery"` to `collection_map`. Gallery image filename scheme: `gallery_{index}.jpg`.

### Timeline inline image improvement

Artifact cards with a `local_image_path` render the image full-width **above** the artifact content (not in the small footer slot). `InlineImageEditor` moves above content body.

---

## Flutter App Changes

### Per-artifact images

`JournalWidget`, `SocialPostWidget`, `EmailWidget`, `ChatBubble` — check for `imageUrl` field from Firestore. If present, render above artifact content using `CachedNetworkImage`.

### Camera Roll / Gallery tab

- New tab in the story experience.
- `GridView` of all `photo_gallery` docs from Firestore (`stories/{id}/gallery` subcollection), filtered by `unlockTimestamp <= now` (same `clockProvider` mechanism as all other artifacts).
- Tapping opens full-screen viewer with caption.
- Tab strip filter:

| Label | Tier filter |
|---|---|
| All | no filter |
| Photos | `tier == "atmospheric"` OR `tier == "diegetic"` |
| Documents | `tier == "document"` |

---

## Explicit Code Change Checklist

- [ ] `models.py` — add `VISUAL_BIBLE`, `IMAGE_PROMPT_DIRECTOR` to `BlockType` enum
- [ ] `models.py` — define `GalleryPhoto` (before `StoryGenerated`), `StoryGeneratedImagePatch`, `CharacterVisual`, `LocationVisual`, `PlannedShot`, `VisualBible`
- [ ] `models.py` — add `photo_gallery` field to `StoryGenerated`
- [ ] `models.py` — add `"VisualBible"` and `"StoryGeneratedImagePatch"` to `SCHEMA_MAP`
- [ ] `defaults.py` — add `VISUAL_BIBLE_PROMPT`, `IMAGE_PROMPT_DIRECTOR_PROMPT`
- [ ] `defaults.py` — add `VISUAL_BIBLE` and `IMAGE_PROMPT_DIRECTOR` entries to `_template_library()`
- [ ] `defaults.py` — add `visual_bible` block to `get_default_pipeline()` (after `scene_decomposition`, before `drop_director`)
- [ ] `defaults.py` — add `image_prompt_director` block to `get_default_pipeline()` (after `final_artifact_generation`, before `image_generation`)
- [ ] `defaults.py` — update `drop_director` `input_blocks` and `prompt_template` to include `visual_bible`
- [ ] `defaults.py` — update `final_artifact_generation` `input_blocks` and `prompt_template` to include `visual_bible`
- [ ] `defaults.py` — update `image_generation` `input_blocks` from `["final_artifact_generation"]` to `["image_prompt_director"]`
- [ ] `defaults.py` — amend `ARTIFACT_GENERATION_PROMPT` with visual bible injection instructions
- [ ] `logic.py` — add merge step for `image_prompt_director` block in `_run_one_block()`
- [ ] `logic.py` — extend `generate_block_images()` to handle `photo_gallery`
- [ ] `logic.py` — add `upload_gallery()` function in `upload_to_firestore()` with `unlockTimestamp` computation
- [ ] `api.py` — add `"gallery": "photo_gallery"` to `collection_map` in `regenerate-image` endpoint
- [ ] `admin_ui_v3` — new Images tab in RunDetail with headline/gallery/artifact sections
- [ ] `admin_ui_v3` — inline image moved above artifact content in timeline cards
- [ ] `lib/` (Flutter) — per-artifact `imageUrl` rendering with `CachedNetworkImage`
- [ ] `lib/` (Flutter) — Camera Roll gallery tab with `unlockTimestamp` gating and tier filter

---

## Out of Scope
- Video generation
- Audio/voice note waveform visualization
- Image moderation/safety filtering (relies on provider defaults)
- Per-shot aspect ratio control (all images 1:1 square for now)
