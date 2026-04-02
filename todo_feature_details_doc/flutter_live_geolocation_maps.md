# Feature Implementation Spec: Live Geolocation Ping Maps & "Idling" Tension

## 1. Feature Overview
**Target Application:** Flutter Client (`lib/`)
**Objective:** Provide an ambient, real-time "Radar" screen to maintain engagement during periods when no new story text is being generated. Users can watch a pulsing dot (the protagonist) move on a map.

## 2. Architecture Context
- The app needs a new screen accessible from the `HubScreen` or Bottom Navigation.
- Requires map rendering (either static styled images with plotted overlays or an active `google_maps_flutter` / `flutter_map` implementation utilizing dark/hacker themes).

## 3. Detailed Requirements
- **The Map View:** A stark, minimalist dark-mode map (no street names, just grid lines, water, and major arteries).
- **The Tracking Dot:** A neon green (`AppTheme.accentNeon`) pulsing dot indicating the protagonist.
- **Interpolated Movement:** The backend won't stream location every second. It will send `{ start: [lat, lng], target: [lat, lng], eta_minutes: 45 }`. The Flutter client must smoothly interpolate the dot moving toward the target over 45 minutes.

## 4. Technical Implementation Steps
1. **Map Integration (`lib/screens/radar_screen.dart`):**
   - Add `flutter_map` (OpenStreetMap integration is lighter/easier without API keys for MVP) or use custom Canvas drawing if the map is purely fictional grid coordinates. Let's design for a custom `Canvas` drawing over a static grid background to avoid third-party API dependencies initially.
2. **Coordinate Interpolation Provider (`lib/providers/radar_provider.dart`):**
   - State should listen for `MovementEvent` from the backend.
   - Create a `Ticker` or `Timer.periodic` that calculates the current X/Y pixel position based on elapsed time vs total `eta_minutes`.
3. **Radar UI Widget (`lib/widgets/radar_display.dart`):**
   - Implement `CustomPainter`. Draw concentric sweeping radar lines.
   - Render the `Tracking Dot` with an expanding/fading `ScaleTransition` to simulate a "ping".
   - Draw a dotted red line from current position to target if the target is known to the user (e.g., "Heading to Safehouse").

## 5. Testing & Verification
- **Simulation:** Agent must write a mock function in `radar_provider.dart` that triggers a 60-second movement across the screen.
- **Performance:** Verify the `CustomPainter` does not drop below 60fps while animating the sweeping radar arc and the pulsing dot simultaneously.
