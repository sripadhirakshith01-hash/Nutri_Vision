from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol, runtime_checkable


class NutritionAIError(RuntimeError):
    """Raised when a configured AI provider fails."""


@runtime_checkable
class NutritionAIProvider(Protocol):
    name: str

    def generate(self, system_prompt: str, messages: list[dict[str, str]]) -> str:
        """Return a complete assistant reply."""

    def stream(self, system_prompt: str, messages: list[dict[str, str]]) -> Iterator[str]:
        """Yield text chunks. Default implementations may yield once."""
