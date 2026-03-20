from __future__ import annotations

from abc import ABC, abstractmethod

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
        return response_schema.model_validate_json(response.text or "{}")


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

    raise ValueError(f"Unsupported provider: {provider_type}")
