from __future__ import annotations

from collections.abc import Iterator

import httpx

from app.ai.base import NutritionAIError


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str, timeout: float = 30.0):
        if not api_key:
            raise NutritionAIError("GEMINI_API_KEY is not set.")
        self.api_key = api_key
        self.model = model or "gemini-2.0-flash"
        self.timeout = timeout

    def _url(self, stream: bool) -> str:
        method = "streamGenerateContent" if stream else "generateContent"
        suffix = "?alt=sse" if stream else ""
        return (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:{method}{suffix}"
        )

    def _payload(self, system_prompt: str, messages: list[dict[str, str]]) -> dict:
        contents = []
        for item in messages:
            role = "user" if item["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": item["content"]}]})
        return {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 700},
        }

    def generate(self, system_prompt: str, messages: list[dict[str, str]]) -> str:
        try:
            response = httpx.post(
                self._url(False),
                params={"key": self.api_key},
                json=self._payload(system_prompt, messages),
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise NutritionAIError("The nutrition AI timed out. Please try again.") from exc
        except httpx.HTTPStatusError as exc:
            raise NutritionAIError("The nutrition AI provider rejected the request.") from exc
        except httpx.HTTPError as exc:
            raise NutritionAIError("Could not reach the nutrition AI provider.") from exc

        candidates = response.json().get("candidates") or []
        parts = (((candidates[0] or {}).get("content") or {}).get("parts") or []) if candidates else []
        text = "".join(part.get("text") or "" for part in parts).strip()
        if not text:
            raise NutritionAIError("The nutrition AI returned an empty reply.")
        return text

    def stream(self, system_prompt: str, messages: list[dict[str, str]]) -> Iterator[str]:
        try:
            with httpx.stream(
                "POST",
                self._url(True),
                params={"key": self.api_key},
                json=self._payload(system_prompt, messages),
                timeout=self.timeout,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    try:
                        import json

                        payload = json.loads(line[5:].strip())
                        parts = (((payload.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [])
                    except (ValueError, IndexError, TypeError):
                        continue
                    for part in parts:
                        text = part.get("text") or ""
                        if text:
                            yield text
        except httpx.TimeoutException as exc:
            raise NutritionAIError("The nutrition AI timed out. Please try again.") from exc
        except httpx.HTTPError as exc:
            raise NutritionAIError("Could not reach the nutrition AI provider.") from exc
