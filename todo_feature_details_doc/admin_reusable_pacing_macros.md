# Feature Implementation Spec: Re-usable Sub-Pipeline "Pacing Macros"

## 1. Feature Overview
**Target Application:** Director Studio (Admin UI)
**Objective:** Reduce prompt engineering fatigue by allowing writers to save a specific chain of 4-5 blocks (e.g., "Standard Morning Routine") into a reusable "Macro Node" that can be dropped onto the canvas.

## 2. Architecture Context
- The timeline is made of primitive blocks (`StoryBeat`, `ImageGeneration`, etc.) defined in `pipeline.json`.
- A macro is fundamentally just copying a subset array of JSON objects and recalculating their internal `depends_on` IDs to link up with the new parent timeline context.

## 3. Detailed Requirements
- **Save Macro Action:** An admin can multi-select blocks (or select a parent node in a 2D canvas), right-click, and "Save as Macro".
- **Macro Library UI:** The left sidebar gets a "Macros" list below the primitive templates.
- **Insert Macro Action:** Dragging a macro into the timeline un-collapses it into the primitive blocks, inserting them into the current JSON array, while automatically assigning them fresh UUIDs and re-linking their internal pointers.

## 4. Technical Implementation Steps
1. **Macro Storage (`python_director/api.py`):**
   - Create endpoints for `GET /macros` and `POST /macros`. A macro is defined as just a `List[BlockConfig]`.
2. **UI Implementation (`admin_ui_v3/src/components/LibraryPanel.tsx`):**
   - Implement the new list view.
   - Implement a `uuid()` generator client-side.
3. **The Unfurl Logic (Critical Step):**
   - When importing `List[BlockConfig]` into the active pipeline:
     - Map every old `block.id` to a `new_id = uuid()`.
     - Iterate through the blocks. For any ID inside the `depends_on` list that matches the macro's internal nodes, rewrite it to the `new_id`.
     - Splice the updated blocks into the master pipeline JSON array.

## 5. Testing & Verification
- **Identity Integrity:** The core failure point is pointer collision. Agent must verify that pasting the exact same Macro twice does not cause the second macro's blocks to depend on the first macro's blocks. Their UUIDs must be strictly isolated.
