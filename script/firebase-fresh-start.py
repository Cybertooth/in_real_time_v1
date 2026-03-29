import sys
import os
from pathlib import Path

# Add project root to sys.path for proper imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from python_director.storage import load_settings
from python_director.logic import list_stories, delete_story
from python_director.log_utils import get_logger

logger = get_logger("firebase_fresh_start")

def main():
    print("--- Firebase Fresh Start: Deleting All Stories ---")
    settings = load_settings()
    
    # Fix the service account key path if it's relative
    creds_path = settings.google_application_credentials
    if creds_path and not os.path.isabs(creds_path):
        # Look in python_director/
        potential_path = PROJECT_ROOT / "python_director" / creds_path
        if potential_path.exists():
            settings.google_application_credentials = str(potential_path)
            print(f"Using credentials from: {settings.google_application_credentials}")
        else:
            print(f"Warning: Could not find credentials at {potential_path}")
    
    if not settings.google_application_credentials:
        print("Error: Google application credentials not found in settings.")
        sys.exit(1)
        
    stories = list_stories(settings)
    
    if not stories:
        print("No stories found in Firebase.")
        return
        
    print(f"Found {len(stories)} stories. Deleting...")
    
    deleted_count = 0
    for story in stories:
        story_id = story.get("id")
        title = story.get("title", "Untitled")
        print(f"Deleting story: {story_id} ('{title}')...")
        if delete_story(story_id, settings):
            deleted_count += 1
            print(f"Success: {story_id} deleted.")
        else:
            print(f"Failed to delete: {story_id}.")
            
    print(f"\nFinished! Deleted {deleted_count} of {len(stories)} stories.")

if __name__ == "__main__":
    main()
