# Director Studio: Product Requirements Document (PRD)

## 1. Product Vision & Principles
**Director Studio** is a low-code, pipeline-based AI orchestrator designed primarily for iterative narrative generation, prompt engineering, and multi-actor simulation (the "Creative Workspace"). 

**Core Principles:**
- **Iterative Refinement**: Prioritize the ability to rapidly test, tweak, and retest complex multi-step prompt pipelines.
- **Real-time Observability**: Provide high visibility into pipeline execution (what block is running, what it output, and timeline plotting).
- **High Signal-to-Noise UI**: Maintain a premium, decluttered, "glassmorphic" dark theme that groups related controls without overwhelming the user.
- **Version Control via Artifacts**: Every run generates persistent artifacts allowing for strict side-by-side A/B comparisons of prompt efficacy.

---

## 2. Core Layout Architecture
The interface fundamentally relies on a dense, three-panel layout to separate concerns: **Library (Left) > Command Center (Center) > Monitor (Right)**.

### Panel 1: Pipeline Library (Left Sidebar)
Responsible for global state and structural composition.
- **Pipeline Meta**: Editable Pipeline Name and Description.
- **Saved Pipelines**: Dropdown to select, load, and "Save As Named" existing pipelines from the catalog.
- **Global Defaults**: Top-level model selections (e.g., `Gemini Default Model`, `OpenAI Default Model`) that blocks can inherit to easily swap the engine for an entire pipeline.
- **Dependency Flow**: A visual, vertical list of active blocks indicating their execution order, type (e.g., `brainstorm_critic`), provider badge, and status (Pending/Running/Success/Failed/Skipped).
- **Template Rail (Bottom)**: A quick-add rail mapping to backend block templates (e.g., `Narrative`, `Critic`, `Summary`) that appends new blocks to the pipeline.

### Panel 2: Command Center (Center Editor)
Responsible for fine-tuning a single, selected block. It must function as a comprehensive inspector without wasting screen horizontal/vertical space (utilizing a dense CSS Grid format).
**Required Block Fields:**
- **Identity**: Block ID (editable, auto-cascades renames to dependents), Block Name, Block Type (disabled).
- **Execution Config**: Enabled/Disabled toggle, Model Provider (Gemini/OpenAI), Model Source (Inherit Pipeline Default vs Custom Override), Model Override (Dropdown auto-filtered by provider), Temperature, and Response Schema selection.
- **Prompts**: Dedicated text areas for `System Instruction` and `Prompt Template`.
- **Dependency Graph**: A checklist of all other blocks in the pipeline allowing the user to explicitly define prerequisites and edge dependencies.
- **Controls**: Move Up / Move Down, Duplicate Block, Delete Block.

**Active Run Banner (Top of Center Panel):**
- Real-time progress bar computing global pipeline completion percentage.
- Visible only during execution.

### Panel 3: Lab & Monitor (Right Sidebar)
Responsible for post-execution and live-execution analysis, structured via Tabs:
1. **Monitor (Active Tab during run):** 
   - **Topline Stats**: Real-time Quality Score proxy and Total Word Count.
   - **Live Artifact Feed**: A chronological stream rendering raw output payloads (JSON/Text) as blocks succeed.
2. **Timeline:** 
   - Translates narrative events (derived from the outputs) into visual milestones (e.g., "Day 1 - 09:00", "Character Action").
3. **History (Past Runs):** 
   - A list of historical dry-runs detailing timestamp, block count, and quality score. Clicking a run loads its details into the active monitor.
4. **Logs (UI Activity):** 
   - Client-side event stream tracking user interaction, HTTP request success/failures, and state changes for easy debugging. Must include "Copy" and "Clear" actions.

---

## 3. Essential Features & Workflows

### A. The Dry Run Cycle
1. **Trigger**: User clicks "Dry Run" from the top bar. 
2. **Save State**: The UI automatically saves the pipeline definition to the backend.
3. **Execution**: The backend begins asynchronous execution, tracking dependencies. 
4. **Polling**: The Frontend polls (`/runs/{run_id}/status`) every second.
5. **Updates**: The active block in the Pipeline Library gets a "spinning" or glowing status dot. The Progress Banner calculates the percentage. The Artifact Feed pushes new blocks as they finish.

### B. A/B Quality Comparison Overlay
- A modal or full-screen overlay (accessible via "Compare Runs").
- **Inputs**: User selects a `Baseline Run` (Previous) and `Candidate Run` (Current).
- **Action**: Fetch comparative metrics from the backend.
- **Output**: 
  - A matrix of numeric deltas (e.g., `Word Count: 1500 vs 1800 (+300)`).
  - Side-by-side `<pre>` blocks rendering the final aggregated artifact payload from both runs for visual inspection of improvements/regressions.

### C. Pipeline Persistence & Snapshots
- **"Save Design"**: Updates the active pipeline JSON.
- **"Snapshot Prompts"**: Creates a hardlink/copy of the current pipeline state in the filesystem (preventing accidental loss of a structurally sound pipeline config).
- **"Reset Default"**: Wipes the current pipeline structure back to a backend-defined hardcoded default template.

### D. Settings Management
- A dedicated modal (accessed via "Settings" top bar button).
- Controls API keys natively (Gemini, OpenAI) and local paths (Google Credentials).
- Values must sync with the Backend securely via HTTP PUT, but also persist in browser `localStorage` to survive refreshes.
- Must include a "Fresh Start" button that explicitly zeroes out localStorage cache, clears UI logs, resets the active pipeline, and re-bootstraps the frontend.

---

## 4. UI/UX Aesthetic Standards
- **Theme**: Premium Dark (`--bg: #0a0a0a`).
- **Glassmorphism**: Panels should leverage translucent surfaces (`rgba(255, 255, 255, 0.05)`) against soft, blurred background gradient orbs (`blur(20px)`).
- **Typography**: `Inter` for primary UI elements (font weights 400/500/600), `JetBrains Mono` for JSON/Artifact outputs. 
- **Feedback**: 
    - Every constructive action (Save, Snapshot, Run Complete) triggers a Toast notification.
    - Status badges/dots strictly adhere to color schema: `Mint (#0fe6b0)` for Success/Active, `Amber (#ffb74d)` for Warnings/Pending, `Danger (#ff5252)` for Errors/Deleted.
    - Buttons employ a hierarchy: `.btn.primary` (solid, actions leading to execution), `.btn` (standard panel actions), `.btn.ghost` (secondary/destructive/utility).
