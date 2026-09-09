from __future__ import annotations

from collections.abc import Iterator

from app.services.chatbot_service import local_reply


class LocalProvider:
    """On-device fallback when no external LLM key is configured."""

    name = "local"

    def generate(self, system_prompt: str, messages: list[dict[str, str]]) -> str:
        del system_prompt
        user_message = next((item["content"] for item in reversed(messages) if item["role"] == "user"), "")
        ctx = {}
        for item in messages:
            if item["role"] == "system" or item["content"].startswith("User context"):
                ctx["_raw"] = item["content"]
        # local_reply expects the structured context dict; NutritionAIService
        # injects it via a synthetic user preface. Parse loosely.
        return local_reply(user_message, _context_from_messages(messages))

    def stream(self, system_prompt: str, messages: list[dict[str, str]]) -> Iterator[str]:
        yield self.generate(system_prompt, messages)


def _context_from_messages(messages: list[dict[str, str]]) -> dict:
    """Recover the compact context dict the service prepends as a hidden note."""
    for item in messages:
        if item.get("role") == "user" and item.get("content", "").startswith("[NutriVision context]"):
            # Fallback numbers if parsing fails — local_reply still answers.
            break
    return {
        "name": "there",
        "goal": "your goal",
        "consumed_calories": 0,
        "target_calories": None,
        "remaining_calories": None,
        "protein_g": 0,
        "target_protein_g": None,
        "meals_today": 0,
        "recent_meals": [],
        "fiber_g": 0,
        "_messages": messages,
    }
