# Feature Implementation Spec: Interactive "Decryption" Boot Sequence

## 1. Feature Overview
**Target Application:** Flutter Client (`lib/`)
**Objective:** Create a highly tactile, immersive "Security Override" mini-game that runs immediately on the first app launch, establishing the hacker/voyeur roleplay before the user ever sees a menu.

## 2. Architecture Context
- Currently, `main.dart` likely routes to the `HubScreen` or `TimelineScreen` on launch.
- Needs a new dedicated `BootScreen` that acts as a middleware router strictly for first-time sessions and occasionally for high-tension in-app artifacts.

## 3. Detailed Requirements
- **First Launch Intercept:** The standard splash screen transitions into a dark terminal UI.
- **Biometric / Tactile Interaction:** A blinking prompt asks for a thumbprint to "Decrypt Payload." The user must hold their finger on a touch zone for ~3 seconds while haptic feedback escalates.
- **System Unlock:** Progress bar completes, terminal spews fake success logs, and navigates to the Hub.
- **Reusable Widget:** The decryption logic should be abstracted into a `DecryptionOverlay` widget so it can be reused later for opening specific encrypted Emails or Chat payloads within the timeline.

## 4. Technical Implementation Steps
1. **Create `BootScreen` (`lib/screens/boot_screen.dart`):**
   - Build a full-screen dark container. Define a `GestureDetector` that listens for `onLongPressStart` and `onLongPressEnd`.
   - Use `flutter_vibrate` or `haptic_feedback` plugins. Pulse the vibration every 500ms while the press holds, speeding up as it nears 100%.
2. **Animation Loop:**
   - Implement an `AnimationController` for a circular progress indicator or a custom "fingerprint scanner" sweeping line.
   - If the user lifts their finger before 3 seconds, reset the animation and play an 'Error' haptic buzz.
3. **Routing (`lib/main.dart`):**
   - Check `SharedPreferences` for a `has_booted` flag. If false, route to `BootScreen`. If true, bypass to `MainNavigation`.
4. **Abstract to `DecryptionOverlay` (`lib/widgets/decryption_overlay.dart`):**
   - Extract the long-press and haptic logic into a reusable widget wrapped around an obfuscated child (e.g., blurring out an Email body using `ImageFilter.blur`).

## 5. Testing & Verification
- **User Flow:** Agent must prove a fresh install lands on the Boot Screen. Next launches bypass it.
- **Haptics:** Verify hardware vibration fires on actual devices (emulator testing requires mocking).
- **Interrupt Handling:** Ensure lifting the finger cleanly cancels the decryption progress visually and programmatically.
