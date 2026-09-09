from __future__ import annotations

from app.ai.base import NutritionAIError, NutritionAIProvider
from app.ai.gemini_provider import GeminiProvider
from app.ai.local_provider import LocalProvider
from app.ai.openai_provider import OpenAIProvider
from app.config import get_settings


def get_nutrition_provider() -> NutritionAIProvider:
    """Return the configured LLM provider. `auto` picks the first available key."""
    settings = get_settings()
    name = (settings.ai_provider or "auto").strip().lower()
    timeout = float(settings.ai_timeout_seconds)

    if name == "local":
        return LocalProvider()
    if name == "openai":
        return OpenAIProvider(settings.openai_api_key, settings.openai_model, timeout)
    if name in {"gemini", "google"}:
        return GeminiProvider(settings.gemini_api_key, settings.gemini_model, timeout)
    if name != "auto":
        raise NutritionAIError(f"Unknown AI_PROVIDER '{settings.ai_provider}'. Use openai, gemini, local, or auto.")

    if settings.openai_api_key:
        return OpenAIProvider(settings.openai_api_key, settings.openai_model, timeout)
    if settings.gemini_api_key:
        return GeminiProvider(settings.gemini_api_key, settings.gemini_model, timeout)
    return LocalProvider()
