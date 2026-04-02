# Feature Implementation Spec: Prompt Regression Testing Suite

## 1. Feature Overview
**Target Application:** Director Studio (Admin UI) & Backend (`python_director/`)
**Objective:** Provide engineers/writers a safety net by running automated "Smoke Tests" on prompt changes to ensure previous narrative beats and tone haven't degraded.

## 2. Architecture Context
- The backend has `smoke_test_images.py` and `test_director.py`, but it lacks an automated narrative grading test suite accessible from the frontend.

## 3. Detailed Requirements
- **Test Cases:** Define a static set of 5 benchmark inputs (e.g., "Standard Morning Routine", "High Tension Attack").
- **Baseline Outputs:** The system stores the "Gold Standard" output for each of those 5 inputs.
- **Run Smoke Test Action:** An admin clicks "Run Regression Tests" in the UI. The backend runs the current pipeline against the 5 benchmark inputs.
- **Similarity Grading:** An LLM grading prompt compares the New Output vs Baseline Output, scoring similarity, tone consistency, and schema adherence (0-100%).
- **UI Reporting:** The UI displays a pass/fail matrix.

## 4. Technical Implementation Steps
1. **Data Structures (`python_director/models.py`):**
   - Create models for `BenchmarkTestCase` and `RegressionReport`.
2. **Backend Regression Runner (`python_director/director.py`):**
   - Create a new class `RegressionSuite`.
   - Implement the grading logic using a strict `<grading_rubric>` prompt via LLM to assert tone matches.
3. **Admin API (`python_director/api.py`):**
   - Endpoints: `POST /pipeline/{id}/regression_test` (Trigger test, returns Job ID), `GET /pipeline/regression_test/{job_id}` (Poll status).
4. **Admin UI Modal (`admin_ui_v3/src/components/RegressionModal.tsx`):**
   - A modal with a "Run Tests" button.
   - Shows a loading state for each of the 5 tests.
   - Renders a color-coded table (Green > 90% match, Orange < 90% match).
   - Allows click-to-expand to view the raw diff (Baseline vs Candidate text side-by-side).

## 5. Testing & Verification
- **Deterministic Check:** Agent must prove that running the exact same pipeline configuration twice yields a 95%+ similarity score.
- **Diff Rendering:** Reviewer will manually change a prompt's instruction from "Write in a formal tone" to "Write explicitly like a teenager" and verify the Regression Test fails the tone check dramatically.
