# Feature Implementation Spec: Semantic Asset Injector Rules

## 1. Feature Overview
**Target Application:** Director Studio (Admin UI) & Backend (`python_director/`)
**Objective:** Replace unpredictable or slow AI-based image generation by automatically mapping LLM text outputs to a curated bank of premium, pre-made multimedia assets (photos, audio clips) using semantic keyword triggers.

## 2. Architecture Context
- The app uses `IMAGE_GENERATOR` blocks or relies on `storage.py` and `api.py` for dealing with assets.
- Instead of using DALL-E/Midjourney, we want a rule-engine that reads the LLM text output and binds an existing asset URL based on exact word matches or semantic similarity.

## 3. Detailed Requirements
- **Asset Library UI:** A new tab in the Library (left panel) where an Admin can upload a batch of media files to a Google Cloud Storage / Firebase bucket.
- **Rule Engine Table:** Admins define rules: `Asset = gs://bucket/receipt.png`, `Triggers = ["motel", "receipt", "paid", "credit card"]`.
- **Backend Injector (`python_director/logic.py`):**
  - Once a text block generates `OutputText`, the logic runs a fast keyword intersection check against the active Rules.
  - If a rule hits, the system updates the payload to attach the URL as an image block or attaches the media directly to the text artifact.

## 4. Technical Implementation Steps
1. **Database Schema (`python_director/models.py`):**
   - Create a model `AssetRule(asset_url: str, tags: List[str], require_all: bool)`.
2. **Backend Logic integration:**
   - In the pipeline execution method, after extracting JSON payload, write a `match_asset_rules` function.
   - If `require_all` is true, all tags must be present in the text (case-insensitive substring match).
   - If met, append `[ATTACHMENT: gs://...]` to the payload going to Firestore.
3. **Frontend UI `admin_ui_v3/src/views/AssetsView.tsx`:**
   - Upload UI utilizing standard `multipart/form-data` hitting an upload endpoint in `api.py`.
   - Data grid mapping uploaded URLs to editable text input fields for "Semantic Tags".

## 5. Testing & Verification
- **Matching Coverage:** Agent must write a unit test (`test_director.py`) ensuring "The suspect bought a coffee at the motel" successfully triggers the `motel_receipt.jpg` rule based on the tags `["motel"]`.
- **Multiple Rules:** Verify tie-breaking logic. If two rules match, just return the first one based on an ordered priority index or append both assets.
