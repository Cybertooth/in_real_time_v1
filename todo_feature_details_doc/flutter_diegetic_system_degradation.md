# Feature Implementation Spec: Diegetic System Degradation & OS Mimicry

## 1. Feature Overview
**Target Application:** Flutter Client (`lib/`)
**Objective:** The app's UI elements (brightness, stability, styling) should dynamically react to the protagonist's current physical state using metadata passed from the backend, making the app feel like a physical extension of the story.

## 2. Architecture Context
- The app relies on the `AppTheme` (`lib/theme.dart`) to style components.
- The `AppState` or `StoryState` needs to ingest global metadata representing the "Victim's Phone State" (e.g., Battery level, Signal strength).

## 3. Detailed Requirements
- **Global Metadata Sync:** The backend (`python_director/api.py`) sends a `system_state` payload with story updates containing `{ "battery": 15, "signal": "low", "status": "running" }`.
- **UI Corruptions:**
  - If `battery < 20`, the global Flutter theme dims (`Opacity` layer over scaffold).
  - If `signal == "low"`, fake typing indicators stutter, and loading spinners jitter artificially.
  - If `status == "running"`, the UI introduces slight camera shake/translation animations periodically.

## 4. Technical Implementation Steps
1. **Extend Models (`lib/models/system_state.dart`):**
   - Create a model parsing `{ battery: int, signal: String, panic_mode: bool }`.
2. **State Management (`lib/providers/system_state_provider.dart`):**
   - Create a global listener that updates `SystemState` whenever a new timeline artifact drops containing metadata.
3. **Theme & Filter Integration (`lib/main_navigation.dart` / Root Scaffold):**
   - Wrap the main application structure in a stack containing an `IgnorePointer` overlay container.
   - If `SystemState.battery < 15`, transition the overlay container to `Colors.black.withOpacity(0.3)`.
   - If `SystemState.panic_mode == true`, use an `AnimationController` on a `Transform.translate` to shake the entire `Scaffold` child by +/- 2 pixels on X/Y axes periodically.
4. **Typing Simulators (`lib/widgets/typing_indicator.dart`):**
   - Modify standard smooth dots to randomly pause or skip frames if `SystemState.signal == 'low'`, mimicking packet loss.

## 5. Testing & Verification
- **Mocking:** Agent must provide a developer debug menu within the Flutter app (or a script invoking the backend) to artificially trigger `battery=5%` and `panic=true`.
- **Visual:** Reviewer will confirm the UI actually dims and physically shakes on the emulator without crashing the app.
