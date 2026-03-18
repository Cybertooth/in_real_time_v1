import os
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import firebase_admin
from firebase_admin import credentials, firestore

# Load environment variables
load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-pro-preview")
FIREBASE_SERVICE_ACCOUNT_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment")
if not FIREBASE_SERVICE_ACCOUNT_PATH:
    raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not found in environment")

# Initialize Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

# Firebase will be initialized on-demand

# --- NEW AGENTIC PIPELINE SCHEMAS ---

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

# --- EXISTING ARTIFACT SCHEMAS ---

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

# --- PROMPTS ---

CREATIVE_OUTLINER_PROMPT = """
You are a visionary, unrestricted creative mastermind. Your goal is to brainstorm a massive, sprawling, multi-character 'found phone' thriller.
Forget about JSON structure. Burn all constraints. Write a long, immersive, and gritty story outline including:
- Deep background lore about a systemic conspiracy or cosmic horror.
- Multiple intersecting character journeys (at least 3-4 distinct POVs).
- Narrative beats that feel 'meaty' and substantial, enough to fill hours of engagement.
- A mind-bending, paradigm-shifting twist that recontextualizes EVERYTHING in the final 6 hours.
- Ideas for realistic digital artifacts: long chat threads, multi-paragraph journals, and emotionally raw voice notes.
Focus on atmosphere, tension, and world-building. Be as detailed and creative as possible.
"""

PLANNER_PROMPT = """
You are an elite, masterful thrill-writer and narrative architect. 
Given the Creative Outline provided, your task is to map this sprawling story into a structured StoryPlan.
Ensure you capture all characters, the core conflict, the background lore, and the act-based summaries accurately from the outline.
The final story must remain massive in scope and highly detailed.
"""

CRITIC_PROMPT = """
You are a ruthless editor. Critique the provided Story Plan for a massive 'found phone' mystery.
Ensure that the story is expansive and 'meaty' enough to hold attention for hours.
Focus intensely on character consistency across multiple POVs, whether the background lore is deep enough, and if the pacing balances extensive deep-dives with frantic bursts.
Are there enough distinct character journeys? Are voice notes utilized effectively? Let no superficial element pass. Be harsh. Provide actionable improvements.
"""

PLAN_REVISION_PROMPT = """
You are revising the Story Plan based on the ruthless editor's critique.
Incorporate ALL actionable improvements. Deepen the character arcs, expand the subplots, fix any pacing issues, and enhance the twist to be truly mind-blowing.
The resulting story plan must be significantly more expansive, complex, and 'meaty'. Output the upgraded Story Plan.
"""

SCENE_DECOMPOSITION_PROMPT = """
You are a master game narrative designer. Break the finalized, sprawling 48-hour Story Plan into detailed distinct 'Scene Blocks'.
A Scene Block represents a cluster of activity.
Crucially, you must schedule massive content chunks:
- Chat sequences must be extensive, representing minutes of continuous real-time texting.
- Journals and voice notes must represent deep, multi-paragraph reflections.
A scene must specify what artifacts (Journal, Chat, Email, Receipt, VoiceNote) are expected.
Leave large gaps of time (dead air) between intense scenes to build tension.
"""

ARTIFACT_GENERATION_PROMPT = """
You are the final execution writer tasked with generating an absolutely massive 'found phone' dataset. Given the final Story Plan and the Scene List, write the actual digital artifacts.
CRITICAL REQUIREMENTS FOR MASSIVE SCALE:
- Chat threads MUST be extraordinarily long, representing a few minutes of continuous, back-and-forth messaging. Use typos, frantic thoughts, multiple messages in succession, and realistic texting cadence.
- Journals MUST be extremely detailed: multiple long paragraphs of deep introspection, observations, or descent into madness.
- VoiceNotes MUST contain highly realistic spoken-word transcripts, stuttering, pauses, and raw emotion, easily spanning 1-2 minutes of spoken audio.
- Emails MUST be highly detailed and realistic (corporate speak, long threads, forwards).
Remember: This must capture a user's attention for a few hours. Make every single artifact substantial and 'meaty'. 
Ensure `time_offset_minutes` perfectly matches the boundaries defined in the Scene List.
Output the final JSON strictly matching the schema.
"""

def save_intermediate(filename: str, data: BaseModel):
    try:
        os.makedirs("temp_artifacts", exist_ok=True)
        filepath = os.path.join("temp_artifacts", filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(data.model_dump_json(indent=2))
        print(f"[LOG] Saved {filepath}")
    except Exception as e:
        print(f"[ERROR] Failed to save {filename}: {e}")

def save_text_artifact(filename: str, text: str):
    try:
        os.makedirs("temp_artifacts", exist_ok=True)
        filepath = os.path.join("temp_artifacts", filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[LOG] Saved {filepath}")
    except Exception as e:
        print(f"[ERROR] Failed to save {filename}: {e}")

def run_agentic_pipeline(critique_loops: int = 2) -> StoryGenerated:
    print(f"\n[PHASE 0] Creative Brainstorming...")
    creative_response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents="Brainstorm the initial massive story outline.",
        config=types.GenerateContentConfig(
            system_instruction=CREATIVE_OUTLINER_PROMPT,
            temperature=1.0,
            # max_output_tokens=4000, # Adjusting for 'thinking' budget-like behavior
        ),
    )
    creative_outline = creative_response.text
    save_text_artifact("intermediate_00_creative_outline.txt", creative_outline)

    print(f"[PHASE 1] Structural Planning...")
    plan_response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=f"Map this creative outline into a structured StoryPlan:\n\n{creative_outline}",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=StoryPlan,
            system_instruction=PLANNER_PROMPT,
            temperature=0.7,
        ),
    )
    current_plan = StoryPlan.model_validate_json(plan_response.text)
    save_intermediate("intermediate_01_initial_plan.json", current_plan)

    for i in range(critique_loops):
        print(f"\n[PHASE 1.CRITIQUE] loop {i+1}/{critique_loops}...")
        critique_response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=f"Critique this plan:\n{current_plan.model_dump_json()}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=StoryCritique,
                system_instruction=CRITIC_PROMPT,
                temperature=0.7,
            ),
        )
        critique = StoryCritique.model_validate_json(critique_response.text)
        save_intermediate(f"intermediate_02_critique_loop_{i+1}.json", critique)

        print(f"[PHASE 1.REVISION] loop {i+1}...")
        revision_response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=f"Original Plan:\n{current_plan.model_dump_json()}\n\nCritique to apply:\n{critique.model_dump_json()}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=StoryPlan,
                system_instruction=PLAN_REVISION_PROMPT,
                temperature=0.8,
            ),
        )
        current_plan = StoryPlan.model_validate_json(revision_response.text)
        save_intermediate(f"intermediate_03_revised_plan_loop_{i+1}.json", current_plan)

    print(f"\n[PHASE 2] Scene Decomposition...")
    scene_response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=f"Break this plan into a scene list:\n{current_plan.model_dump_json()}",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SceneList,
            system_instruction=SCENE_DECOMPOSITION_PROMPT,
            temperature=0.5,
        ),
    )
    scenes = SceneList.model_validate_json(scene_response.text)
    save_intermediate("intermediate_04_scene_list.json", scenes)

    print(f"\n[PHASE 3] Artifact Generation...")
    final_story_response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=f"Final Plan:\n{current_plan.model_dump_json()}\n\nScenes:\n{scenes.model_dump_json()}\n\nWrite the final artifacts.",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=StoryGenerated,
            system_instruction=ARTIFACT_GENERATION_PROMPT,
            temperature=0.7,
        ),
    )
    final_story = StoryGenerated.model_validate_json(final_story_response.text)
    save_intermediate("intermediate_05_final_story.json", final_story)
    
    print(f"\n[LOG] Pipeline complete.")
    return final_story.model_dump()

def upload_to_firestore(story_data):
    if not story_data:
        return None

    # Initialize Firebase
    cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT_PATH)
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(cred)
    db = firestore.client()

    start_time = datetime.now()
    story_id = f"story_{int(time.time())}"
    
    print(f"Uploading story: {story_data['story_title']} (ID: {story_id})")
    
    story_ref = db.collection('stories').document(story_id)
    story_ref.set({
        "title": story_data['story_title'],
        "createdAt": start_time
    })

    # Helper function to upload subcollections
    def upload_collection(collection_name, items):
        print(f"Uploading {len(items)} {collection_name}...")
        batch = db.batch()
        for item in items:
            doc_ref = story_ref.collection(collection_name).document()
            
            # Calculate unlock timestamp
            unlock_time = start_time + timedelta(minutes=item['time_offset_minutes'])
            
            # Prepare data
            doc_data = item.copy()
            del doc_data['time_offset_minutes']
            doc_data['unlockTimestamp'] = unlock_time
            
            batch.set(doc_ref, doc_data)
        batch.commit()

    upload_collection('journals', story_data.get('journals', []))
    upload_collection('chats', story_data.get('chats', []))
    upload_collection('emails', story_data.get('emails', []))
    upload_collection('receipts', story_data.get('receipts', []))
    upload_collection('voice_notes', story_data.get('voice_notes', []))

    print(f"Successfully uploaded story {story_id}")
    return story_id

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate 'In Real-time' story.")
    parser.add_argument("--dry-run", action="store_true", help="Generate story and save to local JSON instead of Firestore.")
    args = parser.parse_args()

    story = run_agentic_pipeline(critique_loops=2)
    if story:
        if args.dry_run:
            output_file = "sample_story.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(story, f, indent=2, ensure_ascii=False)
            print(f"Dry run complete. Final story saved to {output_file}")
        else:
            upload_to_firestore(story)
    else:
        print("Failed to generate story.")
