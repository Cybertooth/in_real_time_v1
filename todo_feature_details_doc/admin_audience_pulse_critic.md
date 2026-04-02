# Feature Implementation Spec: "Audience Pulse" & The AI Critic Loop

## 1. Feature Overview
**Target Application:** Director Studio (Admin UI)
**Objective:** Provide visual feedback to human writers on the quality, pacing, and tension of the generated story to prevent boring streaks.

## 2. Architecture Context
- The system currently generates text blocks.
- We need an asynchronous evaluation loop appended to the generation process and a charting library in the frontend.

## 3. Detailed Requirements
- **Critic Evaluation:** Every time a block completes, a fast, cheap model (e.g., Gemini 3 Flash) reads the output and scores it 1-10 on `Tension`, `Mystery`, and `Action`.
- **Plotting:** The backend stores these scores mapped to the timeline.
- **Pulse Chart UI:** A line chart overlay in the Director Studio Monitor panel that visualizes the scores across the story's days.
- **Alert Flags:** If `Tension` is <= 3 for 4 consecutive blocks, the UI flags a red warning icon indicating "Pacing Slump: Inject Event".

## 4. Technical Implementation Steps
1. **Scoring Logic (`python_director/logic.py`):**
   - Create an LLM prompt: "Read this story artifact. Output a JSON object grading Tension, Mystery, and Action from 1 to 10."
   - Execute this instantly after the main block generation succeeds. Save scores to the `Run` state.
2. **API Extension (`python_director/api.py`):**
   - Serve the scores appended to the `/runs/{id}` timeline metadata.
3. **Frontend Charting (`admin_ui_v3/src/views/MonitorView.tsx`):**
   - Import `recharts` or `chart.js` (React wrapper).
   - Create a `PacingGraph` component. X-axis = Block sequential index. Y-axis = Score (1-10). Plot 3 lines for Tension, Mystery, and Action.
4. **Slump Detection (Client-side):**
   - Calculate moving averages. Render a toast notification if the pacing conditions (slow streak) trigger.

## 5. Testing & Verification
- **Manual Input Bias:** Provide the pipeline with an extremely boring text ("I woke up and stared at the wall for 5 hours"). Agent must prove the Critic LLM accurately scores it a 1 or 2 for Action/Tension.
- **Graph Vis:** Verify `recharts` correctly plots multiple series without crashing on large timeline datasets (50+ points).
