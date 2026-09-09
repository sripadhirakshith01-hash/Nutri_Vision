"""Wrap the existing Food-101 model with nutrition lookup."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.config import get_settings
from app.ml.model_service import predict_food
from app.services.food_lookup import get_food_by_name
from app.services.food_taxonomy import display_name
from app.services.nutrition import scale_nutrition


def nutrition_card(food: dict | None, grams: float | None) -> tuple[dict | None, dict | None, bool]:
    if not food or food.get("calories") is None:
        return None, None, True
    per_100 = {
        "protein_g": food["protein_g"],
        "carbs_g": food["carbs_g"],
        "fat_g": food["fat_g"],
        "fiber_g": food.get("fiber_g") or 0,
        "calories": food["calories"],
        "serving_size": float(food["serving_size"]),
        "basis": "per 100g",
    }
    estimated = None
    if grams:
        scaled = scale_nutrition(food, grams)
        estimated = {
            "protein_g": scaled["protein_g"],
            "carbs_g": scaled["carbs_g"],
            "fat_g": scaled["fat_g"],
            "fiber_g": scaled.get("fiber_g") or 0,
            "calories": scaled["calories"],
            "serving_size": grams,
            "basis": f"estimated {grams:g}g serving",
        }
    return per_100, estimated, False


def classify_image(image: Path | str, grams: float | None = None) -> dict[str, Any]:
    settings = get_settings()
    result = predict_food(image)
    food = get_food_by_name(result["food_name"])
    per_100, estimated, missing = nutrition_card(food, grams)
    return {
        "food_name": result["food_name"],
        "display_name": display_name(result["food_name"]),
        "confidence": result["confidence"],
        "low_confidence": result["confidence"] < settings.low_confidence_threshold,
        "top_predictions": [
            {
                "food": item["food"],
                "display_name": display_name(item["food"]),
                "confidence": item["confidence"],
            }
            for item in result["top_predictions"]
        ],
        "nutrition_per_100g": per_100,
        "estimated": estimated,
        "estimated_grams": grams,
        "nutrition_missing": missing,
        "food": food,
    }
