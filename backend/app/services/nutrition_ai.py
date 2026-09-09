"""NutritionAIService — provider-agnostic nutrition chat."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from app.ai.base import NutritionAIError
from app.ai.factory import get_nutrition_provider
from app.ai.prompts import NUTRITION_SYSTEM_PROMPT
from app.config import get_settings
from app.services.chatbot_service import local_reply
from app.services.food_classifier import classify_image
from app.services.food_taxonomy import display_name


def new_conversation_id() -> str:
    return str(uuid.uuid4())


def _trim_history(history: list[dict[str, Any]], max_turns: int) -> list[dict[str, str]]:
    turns: list[dict[str, str]] = []
    for item in history:
        role = item.get("role")
        content = (item.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            turns.append({"role": role, "content": content[:4000]})
    return turns[-(max_turns * 2) :]


def _format_user_context(ctx: dict[str, Any]) -> str:
    lines = ["User context (use only if it improves the answer; do not repeat sensitive details unnecessarily):"]
    if ctx.get("age"):
        lines.append(f"- Age: {ctx['age']}")
    if ctx.get("height"):
        lines.append(f"- Height: {ctx['height']} cm")
    if ctx.get("weight"):
        lines.append(f"- Weight: {ctx['weight']} kg")
    if ctx.get("activity_level"):
        lines.append(f"- Activity level: {ctx['activity_level']}")
    if ctx.get("goal"):
        lines.append(f"- Fitness goal: {ctx['goal']}")
    if ctx.get("target_calories"):
        lines.append(f"- Estimated daily calorie target: {ctx['target_calories']} kcal (Mifflin-St Jeor estimate)")
    lines.append(
        f"- Today (estimates from logged meals): "
        f"{ctx.get('consumed_calories') or 0:.0f} kcal, "
        f"protein {ctx.get('protein_g') or 0:.0f} g, "
        f"carbs {ctx.get('carbs_g') or 0:.0f} g, "
        f"fat {ctx.get('fat_g') or 0:.0f} g, "
        f"{ctx.get('meals_today') or 0} meals"
    )
    if ctx.get("remaining_calories") is not None:
        lines.append(f"- Estimated remaining today: {ctx['remaining_calories']:.0f} kcal")
    meals = ctx.get("recent_meals") or []
    if meals:
        meal_bits = []
        for item in meals[:8]:
            kcal = item.get("calories")
            kcal_txt = f"{kcal:.0f} kcal" if isinstance(kcal, (int, float)) else "kcal unknown"
            meal_bits.append(f"{item.get('meal_type') or 'meal'}: {item.get('food')} ({kcal_txt})")
        lines.append("- Today's meals: " + "; ".join(meal_bits))
    else:
        lines.append("- Today's meals: none logged yet")
    return "\n".join(lines)


def _format_food_context(food: dict[str, Any]) -> str:
    per = food.get("nutrition_per_100g") or {}
    alts = ", ".join(
        f"{item['display_name']} ({item['confidence']:.0f}%)" for item in (food.get("top_predictions") or [])[1:4]
    )
    lines = [
        "Food-101 image classification (this is a class prediction, not a calorie measurement):",
        f"- Predicted food: {food.get('display_name')} ({food.get('food_name')})",
        f"- Model confidence: {food.get('confidence')}%",
    ]
    if alts:
        lines.append(f"- Other possibilities: {alts}")
    if per:
        lines.append(
            "- Typical nutrition table values per 100g (estimates from the app database, not measured from the photo): "
            f"{per.get('calories')} kcal, protein {per.get('protein_g')} g, "
            f"carbs {per.get('carbs_g')} g, fat {per.get('fat_g')} g, fiber {per.get('fiber_g')} g"
        )
    lines.append(
        "Clearly distinguish classification from estimated nutrition. Do not present these macros as exact lab values."
    )
    return "\n".join(lines)


class NutritionAIService:
    def classify_food_image(self, image: Path | str) -> dict[str, Any]:
        result = classify_image(image, grams=100)
        return {
            "food_name": result["food_name"],
            "display_name": result.get("display_name") or display_name(result["food_name"]),
            "confidence": result["confidence"],
            "low_confidence": result.get("low_confidence"),
            "top_predictions": result.get("top_predictions") or [],
            "nutrition_per_100g": result.get("nutrition_per_100g"),
        }

    def generateNutritionResponse(
        self,
        user_message: str,
        context: dict[str, Any],
        history: list[dict[str, Any]] | None = None,
        food_context: dict[str, Any] | None = None,
    ) -> str:
        settings = get_settings()
        provider = get_nutrition_provider()
        text = (user_message or "").strip()
        if not text:
            text = "Please explain the estimated nutrition for this food."

        if provider.name == "local":
            extra = dict(context)
            extra["classified_food"] = food_context
            extra["history"] = history or []
            return local_reply(text, extra)

        system = NUTRITION_SYSTEM_PROMPT + "\n\n" + _format_user_context(context)
        if food_context:
            system += "\n\n" + _format_food_context(food_context)

        messages = _trim_history(history or [], settings.ai_max_history_turns)
        messages.append({"role": "user", "content": text[:2000]})
        try:
            return provider.generate(system, messages)
        except NutritionAIError:
            extra = dict(context)
            extra["classified_food"] = food_context
            extra["history"] = history or []
            fallback = local_reply(text, extra)
            return (
                fallback
                + "\n\n(The configured AI provider was unavailable, so this reply used NutriVision's on-device nutrition helper.)"
            )

    def streamNutritionResponse(
        self,
        user_message: str,
        context: dict[str, Any],
        history: list[dict[str, Any]] | None = None,
        food_context: dict[str, Any] | None = None,
    ) -> Iterator[str]:
        settings = get_settings()
        provider = get_nutrition_provider()
        text = (user_message or "").strip() or "Please explain the estimated nutrition for this food."
        if provider.name == "local":
            extra = dict(context)
            extra["classified_food"] = food_context
            extra["history"] = history or []
            yield local_reply(text, extra)
            return

        system = NUTRITION_SYSTEM_PROMPT + "\n\n" + _format_user_context(context)
        if food_context:
            system += "\n\n" + _format_food_context(food_context)
        messages = _trim_history(history or [], settings.ai_max_history_turns)
        messages.append({"role": "user", "content": text[:2000]})
        try:
            yielded = False
            for chunk in provider.stream(system, messages):
                yielded = True
                yield chunk
            if not yielded:
                yield self.generateNutritionResponse(text, context, history, food_context)
        except NutritionAIError:
            extra = dict(context)
            extra["classified_food"] = food_context
            extra["history"] = history or []
            yield local_reply(text, extra)


nutrition_ai_service = NutritionAIService()
