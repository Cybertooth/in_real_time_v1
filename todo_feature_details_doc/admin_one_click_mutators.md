# Feature Implementation Spec: One-Click Scenario Mutators

## 1. Feature Overview
**Target Application:** Director Studio (Admin UI) & Backend (`python_director/`)
**Objective:** Allow a writer to rapidly re-generate a block with a specific stylistic twist without needing to manually rewrite the core System Instructions or Prompt template.

## 2. Architecture Context
- Blocks have standard string fields for `system_instruction` and `prompt_template`.
- A "Mutator" is a temporary string literal that is appended to the prompt payload implicitly at runtime.

## 3. Detailed Requirements
- **UI Mutator Dropdown:** In the Editor Panel for a specific block, next to the "Re-run Block" button, add a "Mutate" dropdown.
- **Hardcoded Styles:** The dropdown contains preset values: "More Exhausted", "More Cryptic", "More Aggressive", "More Academic".
- **Runtime Append:** When triggered, the frontend hits an execution endpoint, passing `mutator="More Aggressive"`.
- **Backend Integration:** The `providers.py` layer intercepts the standard prompt, and explicitly appends a footer: `[CRITICAL STYLE OVERRIDE: Rewrite the following task but make the tone extremely <mutator>]` before calling the LLM.

## 4. Technical Implementation Steps
1. **API Update (`python_director/api.py` & `logic.py`):**
   - The execution endpoints (e.g., `/run_block`) need to accept an optional `mutator` query parameter or body field.
2. **Prompt Builder Update (`python_director/providers.py`):**
   - In `execute_prompt()`, if `mutator` is present, construct a wrapper string around the original prompt. Example structure: 
     `Original Prompt: {prompt} \n\n REQUIRED STYLE MODIFIER: Execute the above instructions, but format your output with a {mutator} tone.`
3. **React UI (`admin_ui_v3/src/components/EditorView.tsx`):**
   - Add a split button widget or a prominent dropdown menu.
   - Wire the "On Click" handler to execute the block with the corresponding mutator string sent via Axios.
4. **Side-by-Side Verification:**
   - Integrate with the existing A/B compare view, so the writer can immediately compare the "Standard Tone" vs "Mutated Tone".

## 5. Testing & Verification
- **LLM Adherence:** Provide a standard instruction: "Write a 3 sentence email asking for the quarterly report." Send a `/run_block` request with `mutator="Aggressive and angry"`. Agent must visually verify the output shifts from polite to hostile.
