# Feature Implementation Spec: Continuous Lore Graph & Truth Editor

## 1. Feature Overview
**Target Application:** Director Studio (Admin UI) & Backend (`python_director/`)
**Objective:** Prevent LLM hallucinations over long stories by creating a definitive, human-editable "Truth Database" that is dynamically injected into all generation prompts. 

## 2. Architecture Context
- Currently, the AI generates outputs based on the `sample_story.json` history.
- The pipeline needs a new extraction block at the end of every daily run that parses the output for "hard facts" and saves them to a structured state.

## 3. Detailed Requirements
- **Backend Fact Extraction:** After a story artifact is generated, run a background LLM call with a `FactExtractor` prompt that returns `[{ "entity": "Character Name", "fact": "Information", "confidence": 0.95 }]`.
- **Lore Graph Storage:** Save these facts in a new Firestore collection `story_{id}_lore`.
- **Admin UI Panel:** A new tab in the right sidebar "Lore / Truth". It displays a table of extracted facts.
- **Human Curation:** Admins can Edit, Delete, or Pin facts manually.
- **Prompt Injection:** Before the next block generates, the backend fetches all "Pinned" lore and injects it into the system prompt: `[FACTS YOU MUST NOT CONTRADICT: ...]`.

## 4. Technical Implementation Steps
1. **Backend Extraction Loop (`python_director/logic.py`):**
   - Create a `extract_lore(artifact_text)` function using OpenAI/Gemini structured JSON outputs.
   - Insert logic into the block execution router so it triggers asynchronously on success.
2. **Lore API Endpoints (`python_director/api.py`):**
   - Create `GET /stories/{id}/lore`, `POST /stories/{id}/lore`, `DELETE /stories/{id}/lore/{fact_id}`.
3. **Admin UI Knowledge Tab (`admin_ui_v3/src/views/LoreView.tsx`):**
   - Create a new view (or tab inside EditorView).
   - Render a data table with columns: `Entity`, `Fact`, `Auto-Extracted?`, `Status`.
   - Add inline editing capabilities.
4. **Context Window Injection (`python_director/providers.py`):**
   - Modify the prompt construction builder to prepend the active Lore table payload to the `System Instructions` before sending it to the model.

## 5. Testing & Verification
- **Test Generation:** Provide the extraction pipeline with text: "I bought a red car today." Agent must verify the API successfully parses and stores `{ entity: "Protagonist", fact: "Has a red car" }`.
- **System Prompt Integrity:** Agent must dump the raw prompt sent to the LLM during a Dry Run to verify the red car fact was successfully injected.
