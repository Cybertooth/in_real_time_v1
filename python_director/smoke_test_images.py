
import os
import sys
from pathlib import Path
import time

# Ensure we can import from the current directory
repo_root = Path(__file__).resolve().parent.parent
sys.path.append(str(repo_root / "python_director"))

from storage import load_settings
from providers import GeminiProvider, OpenAIProvider, OpenRouterProvider
from models import ProviderType

def smoke_test_images():
    print("Starting Image Generation Smoke Test...")
    
    # 1. Load settings (API keys)
    settings = load_settings()
    api_keys = {
        "GEMINI_API_KEY": settings.gemini_api_key,
        "OPENAI_API_KEY": settings.openai_api_key,
        "OPENROUTER_API_KEY": settings.openrouter_api_key,
    }

    # 2. Define test models and prompt
    test_prompt = "A cinematic, atmospheric shot of a discarded smartphone lying on a rain-slicked neon street at midnight. The screen is cracked and glowing with a mysterious notification. Hyper-realistic, 4k, moody lighting."
    
    test_cases = [
        {
            "name": "Gemini",
            "provider_class": GeminiProvider,
            "model_name": "gemini-3.1-flash-image-preview",
            "api_key": api_keys["GEMINI_API_KEY"],
        },
        {
            "name": "OpenAI",
            "provider_class": OpenAIProvider,
            "model_name": "gpt-image-1.5-2025-12-16",
            "api_key": api_keys["OPENAI_API_KEY"],
        },
        # OpenRouter currently does not support the /images/generations endpoint.
        # It's primarily for text/vision models. 
        # Skipping for now to avoid the 404.
    ]

    # 3. Create output directory
    output_dir = Path(__file__).resolve().parent / "smoke_test_outputs"
    output_dir.mkdir(exist_ok=True)
    print(f"Saving outputs to: {output_dir}")

    # 4. Run tests
    for case in test_cases:
        print(f"\n--- Testing {case['name']} ({case['model_name']}) ---")
        
        if not case["api_key"]:
            print(f"SKIPPING: {case['name']} API key not configured in settings.local.json")
            continue
            
        try:
            # Initialize provider
            provider = case["provider_class"](api_key=case["api_key"])
            
            # Generate image
            start_time = time.time()
            img_bytes = provider.generate_image(test_prompt, case["model_name"])
            elapsed = time.time() - start_time
            
            # Save to file
            filename = f"smoke_{case['name'].lower()}_{int(time.time())}.jpg"
            file_path = output_dir / filename
            file_path.write_bytes(img_bytes)
            
            print(f"SUCCESS: Generated in {elapsed:.2f}s. Saved to {filename}")
            
        except Exception as e:
            print(f"FAILED: {case['name']} encountered an error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    smoke_test_images()
