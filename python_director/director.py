from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__:
    from .log_utils import get_logger
    from .logic import PipelineRunner, upload_to_firestore
    from .storage import load_pipeline, load_settings
else:
    from log_utils import get_logger
    from logic import PipelineRunner, upload_to_firestore
    from storage import load_pipeline, load_settings

logger = get_logger("python_director.director")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the found-phone Director pipeline.")
    parser.add_argument("--dry-run", action="store_true", help="Only generate local artifacts and skip Firestore upload.")
    parser.add_argument("--run-id", type=str, default=None, help="Optional run identifier for artifact folders.")
    args = parser.parse_args()
    logger.info("Director CLI start dry_run=%s run_id=%s", args.dry_run, args.run_id)

    pipeline = load_pipeline()
    settings = load_settings()
    result = PipelineRunner(settings).run_pipeline(pipeline, run_id=args.run_id)

    if args.dry_run:
        output_file = Path(__file__).resolve().parent / "sample_story.json"
        output_file.write_text(json.dumps(result.final_output, indent=2), encoding="utf-8")
        logger.info("Dry run complete output_file=%s", output_file)
        print(f"Dry run complete. Final story saved to {output_file}")
        return

    if not settings.google_application_credentials:
        raise ValueError("google_application_credentials is not configured. Use settings or --dry-run.")
    if not isinstance(result.final_output, dict):
        raise ValueError("Final output is not a structured story artifact.")

    story_id = upload_to_firestore(result.final_output, settings.google_application_credentials)
    logger.info("Upload complete story_id=%s", story_id)
    print(f"Upload complete. Story ID: {story_id}")


if __name__ == "__main__":
    main()
