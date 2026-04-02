# Feature Implementation Spec: Visual 2D Node-Canvas Orchestration

## 1. Feature Overview
**Target Application:** Director Studio (Admin UI)
**Objective:** Replace the linear list of pipeline blocks with an infinite 2D drag-and-drop canvas (nodes and wires). This is crucial for managing complex, branching, `IF/ELSE` story logic.

## 2. Architecture Context
- The frontend (`EditorView.tsx`) currently renders blocks as a stack.
- The pipeline JSON is actually an array of blocks with implicit execution order and explicit `depends_on` lists.

## 3. Detailed Requirements
- **Node Implementation:** Use `React Flow`. Render each pipeline block as a custom Node.
- **Edges (Wires):** Wires represent execution order and data passing.
- **Drag & Drop Logic:** Dragging from an output handle of Node A to the input handle of Node B automatically adds "Node A" to Node B's `depends_on` array.
- **Mini-Map & Panning:** Standard infinite canvas features for navigating large architectures.

## 4. Technical Implementation Steps
1. **Dependency Installation (`admin_ui_v3/package.json`):**
   - Standard React app: `npm install reactflow`.
2. **Canvas Component (`admin_ui_v3/src/components/PipelineCanvas.tsx`):**
   - Initialize `ReactFlowProvider`.
   - Write state translators: convert the backend's JSON array into `nodes` and `edges` compatible with React Flow format (`{ id: 'string', position: {x,y}, data: {...} }`).
3. **Custom Node (`src/components/BlockNode.tsx`):**
   - Design a compact UI for the node. It needs an icon signifying its type, its Name, and a status indicator (Success/Running).
   - Add `<Handle type="target">` (top) and `<Handle type="source">` (bottom).
4. **Auto-Layout (Optional MVP refinement):**
   - Integrate `dagre.js` to automatically layout nodes hierarchically when a pipeline first loads so they don't stack on top of each other at initialized coordinates (0,0).
5. **JSON Syncing:**
   - On wire connection/disconnection, update the master `Pipeline` state object and `PUT` to the API.

## 5. Testing & Verification
- **Bidirectional State:** Intern agent must prove that connecting a wire visually correctly updates the raw JSON definition, and that fetching a fresh complex JSON file from the backend renders the wires correctly based on the `depends_on` array.
- **Event Handling:** The canvas must not block standard actions (clicking a node should still open the existing Editor Panel on the right for fine-tuning).
