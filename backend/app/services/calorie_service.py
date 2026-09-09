"""Daily calorie target helpers and remaining-budget math."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.services.nutrition import estimate_calorie_target

MEAL_TYPES = ("breakfast", "lunch", "snack", "dinner")


def infer_meal_type(when: datetime | None = None) -> str:
    hour = (when or datetime.now()).hour
    if 5 <= hour < 11:
        return "breakfast"
    if 11 <= hour < 15:
        return "lunch"
    if 15 <= hour < 17:
        return "snack"
    if 17 <= hour < 22:
        return "dinner"
    return "snack"


def remaining_budget(consumed: dict[str, Any], targets: dict[str, Any] | None) -> dict[str, float] | None:
    if not targets:
        return None
    return {
        "calories": round(float(targets["calories"]) - float(consumed.get("calories") or 0), 1),
        "protein_g": round(float(targets["protein_g"]) - float(consumed.get("protein_g") or 0), 1),
        "carbs_g": round(float(targets["carbs_g"]) - float(consumed.get("carbs_g") or 0), 1),
        "fat_g": round(float(targets["fat_g"]) - float(consumed.get("fat_g") or 0), 1),
    }


def goal_status(consumed_calories: float, target_calories: float | None) -> str | None:
    if not target_calories:
        return None
    ratio = consumed_calories / target_calories if target_calories else 0
    if ratio < 0.85:
        return "under_target"
    if ratio <= 1.05:
        return "near_target"
    return "over_target"


def daily_progress(profile: dict[str, Any], consumed: dict[str, Any]) -> dict[str, Any]:
    targets = estimate_calorie_target(profile)
    remaining = remaining_budget(consumed, targets)
    status = goal_status(float(consumed.get("calories") or 0), targets["calories"] if targets else None)
    return {
        "targets": targets,
        "consumed": consumed,
        "remaining": remaining,
        "goal_status": status,
    }
