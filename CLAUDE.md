# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A full-stack generative AI storytelling platform ("In Real Time") — an epistolary real-time thriller where narrative artifacts unlock on a schedule. Flutter mobile app for the reader experience, Python director backend for AI-powered content generation, Firebase/Firestore for real-time sync.

## Common Commands

### Python Director (Backend)
```bash
# Install dependencies (creates venv)
pip install -r python_director/requirements.txt

# Run admin UI + API server on localhost:8001
python -m uvicorn python_director.api:app --host 0.0.0.0 --port 8001 --reload

# Execute dry run (local artifacts only, no Firestore upload)
python -m python_director.director --dry-run

# Full pipeline run with Firestore upload
python -m python_director.director

# Run tests
pytest python_director/test_director.py -v

# Reset to defaults (clears logs, temp_artifacts, snapshots, pipelines, pipeline.json)
script/director-fresh-start.cmd
```

### Flutter App
```bash
flutter pub get
flutter run
flutter test
```

## Architecture

### Two-Part System
1. **Flutter app** (`lib/`) — Riverpod state management, Firestore-driven UI with time-gated content unlocking
2. **Python director** (`python_director/`) — FastAPI backend that orchestrates multi-stage AI content generation pipelines

### Pipeline Execution (python_director/logic.py)
The director runs a **block-based pipeline** where each block is an LLM call with dependencies on other blocks. Execution order is resolved via dependency graph. Pipeline stages: Brainstorm → Council Critique → Rewrite → Planning → Criticism → Revision → Continuity Audit → Scene Decomposition → Drop Director → Generation.

Key files:
- `logic.py` — Pipeline execution engine, dependency resolution, block runner
- `models.py` — Pydantic models for runs, blocks, schemas
- `providers.py` — AI provider abstraction (`GeminiProvider`, `OpenAIProvider`)
- `storage.py` — File I/O for pipelines, runs, settings, artifacts
- `defaults.py` — Default pipeline block definitions and prompt templates
- `api.py` — FastAPI endpoints, CORS, static file serving for admin UI

### Time-Gating (Core Mechanic)
Every story artifact has an `unlockTimestamp`. Flutter queries Firestore with `where('unlockTimestamp', isLessThanOrEqualTo: now)`. A `clockProvider` emits DateTime every minute to refresh. Locked content shows "ENCRYPTED_FILE_LOCKED" state.

### Provider Abstraction
Abstract `AIProvider` with `GeminiProvider` (google-genai SDK) and `OpenAIProvider` implementations. Supports text and structured JSON responses. Provider selected by `ProviderType` enum.

### Run Artifacts
Each run gets a unique `run_id`. Outputs stored in `python_director/temp_artifacts/<run_id>/` — per-block JSON/text files plus `run_result.json`. Runs can be compared side-by-side via the API.

### Admin UI
Standalone HTML/CSS/JS app in `python_director/admin_ui/`. Served as static files. Uses glassmorphic dark theme (BG `#0A0A0A`, accent `#00FF9C`). Three-panel layout for pipeline editing, run execution, and comparison.

## Configuration

- `python_director/settings.local.json` — API keys (gitignored)
- `python_director/pipeline.json` — Active pipeline definition
- `python_director/.env` — Environment vars including `GEMINI_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS`

## Tech Stack
- **Frontend**: Flutter/Dart, Riverpod, Firebase (Firestore, Messaging)
- **Backend**: Python 3.11+, FastAPI, Pydantic, google-genai, openai, firebase-admin
- **AI Models**: Gemini (primary), OpenAI (secondary)

## UI Theme
Both apps share a glassmorphic dark theme: BG `#0A0A0A`, surface `#1A1A1A`, accent mint `#00FF9C`, text `#E0E0E0`. Defined in `lib/theme.dart` (Flutter) and `python_director/admin_ui/styles.css` (web).
