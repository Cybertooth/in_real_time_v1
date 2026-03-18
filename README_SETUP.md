# In Real-time Setup Guide

Follow these steps to get the 'In Real-time' MVP up and running.

## 1. Firebase Project Setup
1.  Go to the [Firebase Console](https://console.firebase.google.com/).
2.  Create a new project named 'In Real-time'.
3.  **Enable Firestore Database:**
    - Choose 'Start in test mode' for initial development.
    - Set the location closest to you.
4.  **Register Apps:**
    - **Android:** Register your app with package name `com.antigravity.inrealtime`. Download `google-services.json` and place it in `android/app/`.
5.  **Enable Firebase Cloud Messaging:**
    - No additional steps needed for basic foreground notifications in this MVP.
6.  **Service Account for Python:**
    - Go to **Project Settings** > **Service accounts**.
    - Click **Generate new private key**.
    - Rename the file to `serviceAccountKey.json` and place it in the `python_director/` folder.

## 2. Python AI Director Setup
1.  Navigate to the `python_director/` directory.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configure environment variables:
    - Edit `.env` and add your `OPENAI_API_KEY`.
    - Ensure `GOOGLE_APPLICATION_CREDENTIALS` points to your `serviceAccountKey.json`.
4.  **Run the Director:**
    ```bash
    python director.py
    ```
    - Check the terminal for the Story ID generated.
    - NOTE: For this MVP, you must update `activeStoryId` in `lib/providers/story_provider.dart` with the ID printed by the script, or keep it as `story_latest` and modify the script to always use that ID.

## 3. Flutter App Setup
1.  Ensure you have Flutter installed.
2.  Run `flutter pub get` in the root directory.
3.  Run the app on an Android emulator or device:
    ```bash
    flutter run
    ```

## Core Mechanic: Time-Gating
The app only displays content where `unlockTimestamp <= current time`.
- If you just ran the Python director, most content will likely be in the future (0 to 48 hours).
- You will see "Locked" states in the Journal.
- To test immediate unlock, you can manually adjust timestamps in the Firestore console or the Python script's `time_offset_minutes` logic.
