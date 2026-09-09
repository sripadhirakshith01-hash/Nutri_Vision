from __future__ import annotations

from decimal import Decimal
from typing import Any


def _num(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def atwater_calories(protein_g: float, carbs_g: float, fat_g: float) -> float:
    return (protein_g * 4) + (carbs_g * 4) + (fat_g * 9)


def scale_nutrition(per_serving: dict[str, Any], grams: float) -> dict[str, float]:
    serving = _num(per_serving.get("serving_size")) or 100.0
    factor = grams / serving
    protein = (_num(per_serving.get("protein_g")) or 0.0) * factor
    carbs = (_num(per_serving.get("carbs_g")) or 0.0) * factor
    fat = (_num(per_serving.get("fat_g")) or 0.0) * factor
    calories = _num(per_serving.get("calories"))
    if calories is None:
        calories = atwater_calories(
            _num(per_serving.get("protein_g")) or 0.0,
            _num(per_serving.get("carbs_g")) or 0.0,
            _num(per_serving.get("fat_g")) or 0.0,
        )
    fiber = (_num(per_serving.get("fiber_g")) or 0.0) * factor
    return {
        "protein_g": round(protein, 1),
        "carbs_g": round(carbs, 1),
        "fat_g": round(fat, 1),
        "fiber_g": round(fiber, 1),
        "calories": round(calories * factor, 1),
        "estimated_grams": grams,
    }


ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "lightly_active": 1.375,
    "moderately_active": 1.55,
    "very_active": 1.725,
    "extra_active": 1.9,
}

GOAL_ADJUSTMENTS = {
    "weight_loss": 0.85,
    "maintain": 1.0,
    "weight_gain": 1.10,
    "general_fitness": 1.0,
}

MACRO_SPLIT = {
    "weight_loss": {"protein": 0.30, "carbs": 0.40, "fat": 0.30},
    "maintain": {"protein": 0.25, "carbs": 0.45, "fat": 0.30},
    "weight_gain": {"protein": 0.25, "carbs": 0.50, "fat": 0.25},
    "general_fitness": {"protein": 0.30, "carbs": 0.40, "fat": 0.30},
}


def estimate_calorie_target(profile: dict[str, Any]) -> dict[str, Any] | None:
    age = _num(profile.get("age"))
    height = _num(profile.get("height"))
    weight = _num(profile.get("weight"))
    gender = (profile.get("gender") or "").lower()
    activity = profile.get("activity_level") or "moderately_active"
    goal = profile.get("goal") or "general_fitness"

    if not age or not height or not weight:
        return None

    # Mifflin-St Jeor (kcal/day). Labeled as an estimate in the UI.
    if gender in {"male", "man"}:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    elif gender in {"female", "woman"}:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 78

    tdee = bmr * ACTIVITY_MULTIPLIERS.get(activity, 1.55)
    calories = round(tdee * GOAL_ADJUSTMENTS.get(goal, 1.0))
    split = MACRO_SPLIT.get(goal, MACRO_SPLIT["general_fitness"])

    return {
        "calories": calories,
        "protein_g": round((calories * split["protein"]) / 4),
        "carbs_g": round((calories * split["carbs"]) / 4),
        "fat_g": round((calories * split["fat"]) / 9),
        "method": "Mifflin-St Jeor estimate",
    }
