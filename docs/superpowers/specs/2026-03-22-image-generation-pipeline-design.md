# Image Generation Pipeline Design

**Date:** 2026-03-22
**Status:** Approved

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

The default pipeline (`defaults.py`) gains two new blocks and one input change:

### New: Stage 8.5 — Visual Bible (`visual_bible`)
- **Position:** After `scene_decomposition`, before `drop_director`
- **Inputs:** `council_plan_judge`, `scene_decomposition`
- **Provider:** Gemini (structured output)
- **Output schema:** `VisualBible`
- **Responsibility:** Produce the canonical visual canon for the story — character appearances, location aesthetics, overall style — and a planned shot list that downstream blocks fulfill.

### New: Stage 11 — Image Prompt Director (`image_prompt_director`)
- **Position:** After `final_artifact_generation`, before `image_generation`
- **Inputs:** `final_artifact_generation`, `visual_bible`
- **Provider:** Gemini (structured output)
- **Output schema:** `StoryGenerated` (enriched)
- **Responsibility:** Audit and refine all `image_prompt` fields in `StoryGenerated` against the Visual Bible. Replace character name references with canonical appearance prose (so image models see descriptions, not names). Fulfill any unassigned `shot_list` entries as `photo_gallery` items.

### Modified: `drop_director`
- Adds `visual_bible` as an input so drop timing can reference planned spike shots.

### Modified: `final_artifact_generation` (GENERATOR)
- Receives `visual_bible` as an additional input.
- Instructed to fulfill `shot_list` entries with matching `artifact_hint` when writing `image_prompt` fields inline. Standalone shots (`artifact_hint = "gallery"`) are left for the Image Prompt Director.

### Stage 12 — Image Generation (`image_generation`) — unchanged
- Now consumes from `image_prompt_director` instead of `final_artifact_generation`.

**Pipeline order (complete):**
1. `creative_brainstorm`
2. `council_brainstorm_*` (parallel)
3. `council_brainstorm_judge`
4. `structural_plan`
5. `council_plan_*` (parallel)
6. `council_plan_judge`
7. `continuity_audit`
8. `scene_decomposition`
9. `visual_bible` ← NEW
10. `drop_director`
11. `final_artifact_generation`
12. `image_prompt_director` ← NEW
13. `image_generation`

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
    tier: str            # "atmospheric" | "diegetic" | "document"
    subject: str         # e.g. "headline", character name, location name
    narrative_purpose: str
    artifact_hint: str   # artifact type ("social_post", "journal", etc.) or "gallery"
    suggested_prompt: str

class VisualBible(BaseModel):
    aesthetic_style: str
    color_palette: str
    era_and_setting: str
    characters: list[CharacterVisual]
    key_locations: list[LocationVisual]
    shot_list: list[PlannedShot]
```

### New: `GalleryPhoto` + modified `StoryGenerated`

```python
class GalleryPhoto(BaseModel):
    photo_id: str
    tier: str                      # "atmospheric" | "diegetic" | "document"
    subject: str
    caption: Optional[str]         # character-voice caption if diegetic
    time_offset_minutes: int
    image_prompt: Optional[str]
    local_image_path: Optional[str]

class StoryGenerated(BaseModel):
    # ... all existing fields unchanged ...
    photo_gallery: list[GalleryPhoto] = Field(default_factory=list)
```

### New `BlockType` values
```python
VISUAL_BIBLE = "visual_bible"
IMAGE_PROMPT_DIRECTOR = "image_prompt_director"
```

### `SCHEMA_MAP` additions
```python
"VisualBible": VisualBible,
```

---

## Backend Logic Changes

### `generate_block_images()` in `logic.py`
- Extend to iterate `photo_gallery` items and generate images, saving as `gallery_{i}.jpg`.
- Existing collections (journals, chats, emails, social_posts, receipts, voice_notes) unchanged.

### `upload_to_firestore()` in `logic.py`
- Upload `photo_gallery` images to Firebase Storage.
- Write gallery items as `stories/{id}/gallery` subcollection: `{tier, subject, caption, timeOffsetMinutes, imageUrl}`.

### New prompts in `defaults.py`
- `VISUAL_BIBLE_PROMPT` — instructs model to produce lightweight visual canon + shot list from StoryPlan + SceneList.
- `IMAGE_PROMPT_DIRECTOR_PROMPT` — instructs model to audit/refine all `image_prompt` fields, replace character names with canonical appearance descriptions, fulfill unassigned shots as `photo_gallery` entries, output full enriched `StoryGenerated`.

### `ARTIFACT_GENERATION_PROMPT` amendment
- Receives Visual Bible context.
- Instructed to fulfill `shot_list` entries where `artifact_hint` matches the current artifact type.
- Standalone gallery shots (`artifact_hint = "gallery"`) are explicitly excluded from GENERATOR responsibility.

### Dry-run
- No behavior change — images already render locally in dry-run. New blocks are text-only LLM calls.

---

## Director Studio (Admin UI)

### New: Images tab in RunDetail
Three sections:
1. **Headline** — single large image with prompt + regenerate button.
2. **Gallery** — grid of all `photo_gallery` items. Each tile: tier badge, caption, prompt, regenerate button.
3. **Artifact images** — flat list of per-artifact images grouped by type (social posts, journals, emails, chats).

### Regenerate endpoint extension
`POST /runs/{run_id}/regenerate-image` extended to handle `event_type = "gallery"` with an `index`.

### Timeline inline image improvement
Artifact cards with a `local_image_path` render the image full-width above the artifact content (not in the small footer slot). `InlineImageEditor` moves above content.

---

## Flutter App Changes

### Per-artifact images
`JournalWidget`, `SocialPostWidget`, `EmailWidget`, `ChatBubble` — check for `imageUrl` field from Firestore. If present, render above artifact content using `CachedNetworkImage`.

### Camera Roll / Gallery tab
- New tab in the story experience.
- `GridView` of all `photo_gallery` docs from Firestore (`stories/{id}/gallery` subcollection).
- Tapping opens full-screen viewer with caption.
- Tab strip filter: **All / Photos / Documents** (maps to tier).

---

## Out of Scope
- Video generation
- Audio/voice note waveform visualization
- Image moderation/safety filtering (relies on provider defaults)
- Per-shot aspect ratio control (all images 1:1 square for now)
