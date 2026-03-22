from __future__ import annotations

from abc import ABC, abstractmethod
import os

from pydantic import BaseModel

if __package__:
    from .log_utils import get_logger
    from .models import BlockConfig, ProviderType
else:
    from log_utils import get_logger
    from models import BlockConfig, ProviderType

logger = get_logger("python_director.providers")


class AIProvider(ABC):
    @abstractmethod
    def generate_content(self, config: BlockConfig, contents: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_structured_output(
        self,
        config: BlockConfig,
        contents: str,
        response_schema: type[BaseModel],
    ) -> BaseModel:
        raise NotImplementedError

    @abstractmethod
    def generate_image(self, prompt: str, model_name: str) -> bytes:
        raise NotImplementedError


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str):
        try:
            from google import genai
        except ImportError as exc:
            raise ImportError("google-genai is not installed. Run script\\director-install.cmd first.") from exc
        self._genai = genai
        self.client = genai.Client(api_key=api_key)
        logger.info("GeminiProvider initialized")

    def generate_content(self, config: BlockConfig, contents: str) -> str:
        logger.debug("Gemini generate_content model=%s chars=%s", config.model_name, len(contents))
        types = self._genai.types
        response = self.client.models.generate_content(
            model=config.model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=config.system_instruction,
                temperature=config.temperature,
            ),
        )
        return response.text or ""

    def generate_structured_output(
        self,
        config: BlockConfig,
        contents: str,
        response_schema: type[BaseModel],
    ) -> BaseModel:
        logger.debug(
            "Gemini generate_structured_output model=%s schema=%s chars=%s",
            config.model_name,
            response_schema.__name__,
            len(contents),
        )
        types = self._genai.types
        response = self.client.models.generate_content(
            model=config.model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
                system_instruction=config.system_instruction,
                temperature=config.temperature,
            ),
        )
        parsed = getattr(response, "parsed", None)
        if parsed is not None:
            if isinstance(parsed, response_schema):
                return parsed
            return response_schema.model_validate(parsed)
        return response_schema.model_validate_json(response.text or "{}")

    def generate_image(self, prompt: str, model_name: str) -> bytes:
        logger.debug("Gemini generate_image model=%s prompt_len=%s", model_name, len(prompt))
        import base64

        def _extract_inline_image_bytes(response: object) -> bytes | None:
            for candidate in getattr(response, "candidates", []) or []:
                content = getattr(candidate, "content", None)
                for part in getattr(content, "parts", []) or []:
                    inline = getattr(part, "inline_data", None)
                    if inline is None:
                        continue
                    data = getattr(inline, "data", None)
                    if isinstance(data, bytes):
                        return data
                    if isinstance(data, str) and data:
                        return base64.b64decode(data)
            return None

        model_lower = model_name.lower()
        if model_lower.startswith("gemini-"):
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=self._genai.types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                ),
            )
            image_bytes = _extract_inline_image_bytes(response)
            if image_bytes:
                return image_bytes
            raise ValueError("Gemini image model returned no image bytes.")

        result = self.client.models.generate_images(
            model=model_name,
            prompt=prompt,
            config=self._genai.types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type="image/jpeg",
                aspect_ratio="1:1",
            ),
        )
        if not result.generated_images:
            raise ValueError("Gemini failed to generate an image.")
        return result.generated_images[0].image.image_bytes


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError("openai is not installed. Run script\\director-install.cmd first.") from exc
        self.client = OpenAI(api_key=api_key, timeout=3600.0)
        logger.info("OpenAIProvider initialized")

    def _is_reasoning_model(self, model_name: str) -> bool:
        """Models like o1-preview, o1-mini, or 5.4-pro don't support temperature."""
        name = model_name.lower()
        return name.startswith("o1-") or "5.4" in name

    def generate_content(self, config: BlockConfig, contents: str) -> str:
        logger.debug("OpenAI generate_content model=%s chars=%s", config.model_name, len(contents))
        kwargs = {
            "model": config.model_name,
            "instructions": config.system_instruction,
            "input": contents,
        }
        if not self._is_reasoning_model(config.model_name):
            kwargs["temperature"] = config.temperature

        response = self.client.responses.create(**kwargs)
        return response.output_text

    def generate_structured_output(
        self,
        config: BlockConfig,
        contents: str,
        response_schema: type[BaseModel],
    ) -> BaseModel:
        logger.debug(
            "OpenAI generate_structured_output model=%s schema=%s chars=%s",
            config.model_name,
            response_schema.__name__,
            len(contents),
        )
        kwargs = {
            "model": config.model_name,
            "instructions": config.system_instruction,
            "input": contents,
            "text_format": response_schema,
        }
        if not self._is_reasoning_model(config.model_name):
            kwargs["temperature"] = config.temperature

        response = self.client.responses.parse(**kwargs)
        if response.output_parsed is None:
            raise ValueError(response.output_text or "OpenAI response did not return a parsed payload.")
        return response.output_parsed

    def generate_image(self, prompt: str, model_name: str) -> bytes:
        logger.debug("OpenAI generate_image model=%s prompt_len=%s", model_name, len(prompt))
        import requests
        import base64
        response = self.client.images.generate(
            model=model_name,
            prompt=prompt,
            size="1024x1024",
            quality="auto",
            n=1,
        )
        b64 = getattr(response.data[0], "b64_json", None)
        if b64:
            return base64.b64decode(b64)

        url = response.data[0].url
        if not url:
            raise ValueError("OpenAI failed to return an image URL or b64 payload.")
        res = requests.get(url, timeout=30)
        res.raise_for_status()
        return res.content


class OpenRouterProvider(AIProvider):
    """OpenAI-compatible provider routing to https://openrouter.ai/api/v1.

    Uses chat.completions (not the OpenAI-specific Responses API) so it works
    with any model OpenRouter hosts, including Llama, Mistral, Qwen, etc.
    Structured output is implemented via function/tool calling.
    """

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: str):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError("openai is not installed. Run script\\director-install.cmd first.") from exc
        http_referer = os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost")
        app_title = os.getenv("OPENROUTER_APP_TITLE", "Python Director Studio")
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.BASE_URL,
            timeout=3600.0,
            default_headers={
                "HTTP-Referer": http_referer,
                "X-Title": app_title,
            },
        )
        logger.info("OpenRouterProvider initialized")

    def generate_content(self, config: BlockConfig, contents: str) -> str:
        logger.debug("OpenRouter generate_content model=%s chars=%s", config.model_name, len(contents))
        response = self.client.chat.completions.create(
            model=config.model_name,
            messages=[
                {"role": "system", "content": config.system_instruction},
                {"role": "user", "content": contents},
            ],
            temperature=config.temperature,
        )
        return response.choices[0].message.content or ""

    def generate_structured_output(
        self,
        config: BlockConfig,
        contents: str,
        response_schema: type[BaseModel],
    ) -> BaseModel:
        import json as _json
        logger.debug(
            "OpenRouter generate_structured_output model=%s schema=%s chars=%s",
            config.model_name,
            response_schema.__name__,
            len(contents),
        )
        tool_def = {
            "type": "function",
            "function": {
                "name": "structured_output",
                "description": f"Return a valid {response_schema.__name__} object.",
                "parameters": response_schema.model_json_schema(),
            },
        }
        response = self.client.chat.completions.create(
            model=config.model_name,
            messages=[
                {"role": "system", "content": config.system_instruction},
                {"role": "user", "content": contents},
            ],
            tools=[tool_def],  # type: ignore[list-item]
            tool_choice="auto",
            temperature=config.temperature,
        )
        msg = response.choices[0].message
        if msg.tool_calls:
            args = _json.loads(msg.tool_calls[0].function.arguments)
            return response_schema.model_validate(args)
        # Fallback: try parsing raw content as JSON
        raw = msg.content or ""
        return response_schema.model_validate_json(raw)

    def generate_image(self, prompt: str, model_name: str) -> bytes:
        logger.debug("OpenRouter generate_image model=%s prompt_len=%s", model_name, len(prompt))
        import base64
        import re
        import requests

        response = self.client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            extra_body={"modalities": ["image"]},
        )
        message = response.choices[0].message

        def _decode_data_url(value: str) -> bytes | None:
            if not value.startswith("data:image"):
                return None
            _, encoded = value.split(",", 1)
            return base64.b64decode(encoded)

        def _download(url: str) -> bytes:
            res = requests.get(url, timeout=30)
            res.raise_for_status()
            return res.content

        # OpenRouter multimodal shape: message.images = [{"type":"image_url","image_url":{"url":"..."}}]
        images = getattr(message, "images", None)
        if images:
            for entry in images:
                if isinstance(entry, dict):
                    image_url = ((entry.get("image_url") or {}).get("url") or "").strip()
                else:
                    image_url_obj = getattr(entry, "image_url", None)
                    image_url = str(getattr(image_url_obj, "url", "") or "").strip()
                if not image_url:
                    continue
                decoded = _decode_data_url(image_url)
                if decoded:
                    return decoded
                if image_url.startswith("http"):
                    return _download(image_url)

        # Fallback: scan content for markdown image URL or data URL.
        content = getattr(message, "content", None)
        if isinstance(content, str) and content:
            match = re.search(r"!\[[^\]]*\]\((https?://[^)]+)\)", content)
            if match:
                return _download(match.group(1))
            data_match = re.search(r"(data:image\/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=]+)", content)
            if data_match:
                decoded = _decode_data_url(data_match.group(1))
                if decoded:
                    return decoded

        raise ValueError(f"OpenRouter failed to generate an image. message={message}")


class AnthropicProvider(AIProvider):
    def __init__(self, api_key: str):
        try:
            import anthropic as _anthropic
        except ImportError as exc:
            raise ImportError("anthropic is not installed. Run script\\director-install.cmd first.") from exc
        self._anthropic = _anthropic
        self.client = _anthropic.Anthropic(api_key=api_key)
        logger.info("AnthropicProvider initialized")

    def generate_content(self, config: BlockConfig, contents: str) -> str:
        logger.debug("Anthropic generate_content model=%s chars=%s", config.model_name, len(contents))
        response = self.client.messages.create(
            model=config.model_name,
            max_tokens=8096,
            system=config.system_instruction,
            messages=[{"role": "user", "content": contents}],
            temperature=config.temperature,
        )
        return response.content[0].text  # type: ignore[union-attr]

    def generate_structured_output(
        self,
        config: BlockConfig,
        contents: str,
        response_schema: type[BaseModel],
    ) -> BaseModel:
        logger.debug(
            "Anthropic generate_structured_output model=%s schema=%s chars=%s",
            config.model_name,
            response_schema.__name__,
            len(contents),
        )
        tool_def = {
            "name": "structured_output",
            "description": f"Return a valid {response_schema.__name__} object.",
            "input_schema": response_schema.model_json_schema(),
        }
        response = self.client.messages.create(
            model=config.model_name,
            max_tokens=8096,
            system=config.system_instruction,
            messages=[{"role": "user", "content": contents}],
            tools=[tool_def],  # type: ignore[list-item]
            tool_choice={"type": "tool", "name": "structured_output"},
            temperature=config.temperature,
        )
        for block in response.content:
            if block.type == "tool_use":
                return response_schema.model_validate(block.input)  # type: ignore[union-attr]
        raise ValueError("Anthropic did not return a tool_use block in the response.")

    def generate_image(self, prompt: str, model_name: str) -> bytes:
        raise NotImplementedError("Anthropic does not support image generation.")


def get_provider(provider_type: ProviderType, api_keys: dict[str, str | None]) -> AIProvider:
    logger.info("Resolving provider type=%s", provider_type)
    if provider_type == ProviderType.GEMINI:
        key = api_keys.get("GEMINI_API_KEY")
        if not key:
            raise ValueError("Gemini API key is missing. Add it in Settings before running Gemini blocks.")
        return GeminiProvider(api_key=key)

    if provider_type == ProviderType.OPENAI:
        key = api_keys.get("OPENAI_API_KEY")
        if not key:
            raise ValueError("OpenAI API key is missing. Add it in Settings before running OpenAI blocks.")
        return OpenAIProvider(api_key=key)

    if provider_type == ProviderType.OPENROUTER:
        key = api_keys.get("OPENROUTER_API_KEY")
        if not key:
            raise ValueError("OpenRouter API key is missing. Add it in Settings before running OpenRouter blocks.")
        return OpenRouterProvider(api_key=key)

    if provider_type == ProviderType.ANTHROPIC:
        key = api_keys.get("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("Anthropic API key is missing. Add it in Settings before running Anthropic blocks.")
        return AnthropicProvider(api_key=key)

    raise ValueError(f"Unsupported provider: {provider_type}")
