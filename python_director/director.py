from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__:
    from .log_utils import get_logger
    from .logic import PipelineRunner, upload_to_firestore
    from .storage import load_pipeline, load_settings, load_run_result
else:
    from log_utils import get_logger
    from logic import PipelineRunner, upload_to_firestore
    from storage import load_pipeline, load_settings, load_run_result

logger = get_logger("python_director.director")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the found-phone Director pipeline.")
    parser.add_argument("--dry-run", action="store_true", help="Only generate local artifacts and skip Firestore upload.")
    parser.add_argument("--upload-only", action="store_true", help="Skip generation and only upload an existing run to Firestore.")
    parser.add_argument("--run-id", type=str, default=None, help="Optional run identifier for artifact folders.")
    args = parser.parse_args()
    logger.info("Director CLI start dry_run=%s upload_only=%s run_id=%s", args.dry_run, args.upload_only, args.run_id)

    settings = load_settings()

    if args.upload_only:
        if not args.run_id:
            raise ValueError("--run-id is required for --upload-only.")
        if not settings.google_application_credentials:
            raise ValueError("google_application_credentials is not configured.")
        
        # Resolve credential path absolutely
        cred_path = settings.google_application_credentials
        if not Path(cred_path).is_absolute():
            cred_path = str(Path(__file__).resolve().parent / cred_path)
            
        logger.info("Fetching existing run for upload: %s", args.run_id)
        print(f"DEBUG: cred_path={cred_path}")
        result = load_run_result(args.run_id)
        
        pipeline = load_pipeline()
        if not isinstance(result.final_output, dict):
            raise ValueError(f"Run '{args.run_id}' does not have a structured final story output.")
            
        story_id = upload_to_firestore(result, cred_path, settings, pipeline)
        logger.info("Manual upload complete story_id=%s", story_id)
        print(f"Manual upload complete. Story ID: {story_id}")
        return

    pipeline = load_pipeline()
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

    # Resolve credential path absolutely
    cred_path = settings.google_application_credentials
    if not Path(cred_path).is_absolute():
        cred_path = str(Path(__file__).resolve().parent / cred_path)

    story_id = upload_to_firestore(result, cred_path, settings, pipeline)
    logger.info("Upload complete story_id=%s", story_id)
    print(f"Upload complete. Story ID: {story_id}")


if __name__ == "__main__":
    main()
