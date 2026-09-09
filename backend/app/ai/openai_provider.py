from __future__ import annotations

from collections.abc import Iterator

import httpx

from app.ai.base import NutritionAIError


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str, model: str, timeout: float = 30.0):
        if not api_key:
            raise NutritionAIError("OPENAI_API_KEY is not set.")
        self.api_key = api_key
        self.model = model or "gpt-4o-mini"
        self.timeout = timeout

    def _payload(self, system_prompt: str, messages: list[dict[str, str]], stream: bool) -> dict:
        return {
            "model": self.model,
            "temperature": 0.4,
            "max_tokens": 700,
            "stream": stream,
            "messages": [{"role": "system", "content": system_prompt}, *messages],
        }

    def generate(self, system_prompt: str, messages: list[dict[str, str]]) -> str:
        try:
            response = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=self._payload(system_prompt, messages, False),
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise NutritionAIError("The nutrition AI timed out. Please try again.") from exc
        except httpx.HTTPStatusError as exc:
            raise NutritionAIError("The nutrition AI provider rejected the request.") from exc
        except httpx.HTTPError as exc:
            raise NutritionAIError("Could not reach the nutrition AI provider.") from exc

        content = response.json().get("choices", [{}])[0].get("message", {}).get("content")
        if not content or not str(content).strip():
            raise NutritionAIError("The nutrition AI returned an empty reply.")
        return str(content).strip()

    def stream(self, system_prompt: str, messages: list[dict[str, str]]) -> Iterator[str]:
        try:
            with httpx.stream(
                "POST",
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=self._payload(system_prompt, messages, True),
                timeout=self.timeout,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        import json

                        delta = json.loads(data)["choices"][0]["delta"].get("content") or ""
                    except (KeyError, ValueError, IndexError):
                        continue
                    if delta:
                        yield delta
        except httpx.TimeoutException as exc:
            raise NutritionAIError("The nutrition AI timed out. Please try again.") from exc
        except httpx.HTTPError as exc:
            raise NutritionAIError("Could not reach the nutrition AI provider.") from exc
