from __future__ import annotations

from typing import Any

from app.database.connection import get_connection
from app.services.food_taxonomy import category_for, display_name
from app.services.nutrition import atwater_calories


def serialize_food(row: dict[str, Any]) -> dict[str, Any]:
    protein = float(row["protein_g"]) if row.get("protein_g") is not None else None
    carbs = float(row["carbs_g"]) if row.get("carbs_g") is not None else None
    fat = float(row["fat_g"]) if row.get("fat_g") is not None else None
    fiber = float(row["fiber_g"]) if row.get("fiber_g") is not None else None
    calories = row.get("calories")
    if calories is None and protein is not None and carbs is not None and fat is not None:
        calories = round(atwater_calories(protein, carbs, fat))
    return {
        "id": row["id"],
        "food_name": row["food_name"],
        "display_name": display_name(row["food_name"]),
        "protein_g": protein,
        "carbs_g": carbs,
        "fat_g": fat,
        "fiber_g": fiber,
        "calories": float(calories) if calories is not None else None,
        "serving_size": row.get("serving_size") or 100,
        "category": row.get("category") or category_for(row["food_name"]),
        "source": row.get("source"),
        "basis": "per 100g",
    }


_FOOD_SELECT = """
    SELECT id, food_name, protein_g, carbs_g, fat_g, fiber_g, calories, serving_size, category, source
    FROM food_nutrition
"""


def get_food_by_name(food_name: str) -> dict[str, Any] | None:
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(f"{_FOOD_SELECT} WHERE food_name = %s", (food_name,))
        row = cursor.fetchone()
        cursor.close()
        return serialize_food(row) if row else None
    finally:
        connection.close()


def normalize_food_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")
