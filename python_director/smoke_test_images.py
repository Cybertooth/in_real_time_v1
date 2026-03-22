import os
import sys
from pathlib import Path
import time

# Ensure we can import from the current directory
repo_root = Path(__file__).resolve().parent.parent
sys.path.append(str(repo_root / "python_director"))

from storage import load_settings
from providers import GeminiProvider, OpenAIProvider, OpenRouterProvider

def _short_error(exc: Exception, max_len: int = 260) -> str:
    message = " ".join(str(exc).split())
    if len(message) <= max_len:
        return message
    return message[:max_len].rstrip() + "..."


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
            "name": "OpenRouter",
            "provider_class": OpenRouterProvider,
            "models": [
                "bytedance-seed/seedream-4.5",
                "black-forest-labs/flux-1-schnell",
                "stabilityai/stable-diffusion-3.5-large",
            ],
            "api_key": api_keys["OPENROUTER_API_KEY"],
        },
        {
            "name": "OpenAI",
            "provider_class": OpenAIProvider,
            "models": ["gpt-image-1"],
            "api_key": api_keys["OPENAI_API_KEY"],
        },
        {
            "name": "Gemini",
            "provider_class": GeminiProvider,
            "models": ["gemini-3.1-flash-image-preview", "imagen-4.0-fast-generate-001"],
            "api_key": api_keys["GEMINI_API_KEY"],
        },
    ]

    # 3. Create output directory
    output_dir = Path(__file__).resolve().parent / "smoke_test_outputs"
    output_dir.mkdir(exist_ok=True)
    print(f"Saving outputs to: {output_dir}")

    # 4. Run tests
    for case in test_cases:
        print(f"\n--- Testing {case['name']} ---")
        
        if not case["api_key"]:
            print(f"SKIPPING: {case['name']} API key not configured in settings.local.json")
            continue
            
        try:
            # Initialize provider
            provider = case["provider_class"](api_key=case["api_key"])

            last_error = None
            generated = False
            for model_name in case["models"]:
                print(f"Trying model: {model_name}")
                try:
                    start_time = time.time()
                    img_bytes = provider.generate_image(test_prompt, model_name)
                    elapsed = time.time() - start_time
                    filename = f"smoke_{case['name'].lower()}_{model_name.replace('/', '_')}_{int(time.time())}.jpg"
                    file_path = output_dir / filename
                    file_path.write_bytes(img_bytes)
                    print(f"SUCCESS: Generated in {elapsed:.2f}s. Saved to {filename}")
                    generated = True
                    break
                except Exception as exc:
                    last_error = exc
                    print(f"Model failed: {model_name} -> {_short_error(exc)}")

            if not generated:
                if isinstance(last_error, Exception):
                    raise RuntimeError(_short_error(last_error))
                raise RuntimeError(f"{case['name']} failed with all models.")
        except Exception as e:
            print(f"FAILED: {case['name']} encountered an error: {_short_error(e)}")
            if os.getenv("SMOKE_DEBUG") == "1":
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    smoke_test_images()
