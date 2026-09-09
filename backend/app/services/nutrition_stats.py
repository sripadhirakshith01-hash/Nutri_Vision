"""Aggregate logged meals into daily / weekly nutrition totals."""

from __future__ import annotations

from datetime import date
from typing import Any

from app.database.connection import get_connection
from app.services.food_taxonomy import FRIED_FOODS, VEGETABLE_FOODS


def empty_totals() -> dict[str, Any]:
    return {
        "calories": 0.0,
        "protein_g": 0.0,
        "carbs_g": 0.0,
        "fat_g": 0.0,
        "fiber_g": 0.0,
        "meals": 0,
    }


def fetch_range(user_id: int, start: date, end: date) -> list[dict]:
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT p.prediction_id, p.estimated_grams, p.estimated_calories, p.predicted_at, p.meal_type,
                   f.food_name, f.protein_g, f.carbs_g, f.fat_g, f.fiber_g, f.serving_size, f.category
            FROM predictions p
            JOIN food_nutrition f ON f.id = p.food_id
            WHERE p.user_id = %s
              AND DATE(p.predicted_at) >= %s
              AND DATE(p.predicted_at) <= %s
            ORDER BY p.predicted_at ASC
            """,
            (user_id, start, end),
        )
        rows = cursor.fetchall()
        cursor.close()
    finally:
        connection.close()
    return rows


def scale_row(row: dict) -> dict:
    grams = float(row["estimated_grams"]) if row.get("estimated_grams") else None
    serving = float(row["serving_size"] or 100)
    factor = (grams / serving) if grams else 0
    calories = float(row["estimated_calories"]) if row.get("estimated_calories") is not None else 0
    return {
        "food_name": row["food_name"],
        "calories": calories,
        "protein_g": float(row["protein_g"] or 0) * factor,
        "carbs_g": float(row["carbs_g"] or 0) * factor,
        "fat_g": float(row["fat_g"] or 0) * factor,
        "fiber_g": float(row["fiber_g"] or 0) * factor,
        "predicted_at": row["predicted_at"],
        "category": row.get("category"),
        "meal_type": row.get("meal_type"),
    }


def sum_rows(rows: list[dict]) -> dict[str, Any]:
    totals = empty_totals()
    days = set()
    foods: list[str] = []
    for raw in rows:
        item = scale_row(raw)
        totals["calories"] += item["calories"]
        totals["protein_g"] += item["protein_g"]
        totals["carbs_g"] += item["carbs_g"]
        totals["fat_g"] += item["fat_g"]
        totals["fiber_g"] += item["fiber_g"]
        totals["meals"] += 1
        days.add(item["predicted_at"].date())
        foods.append(item["food_name"])
    totals["active_days"] = len(days)
    totals["vegetable_count"] = sum(1 for food in foods if food in VEGETABLE_FOODS)
    totals["fried_count"] = sum(1 for food in foods if food in FRIED_FOODS)
    totals["foods"] = foods
    for key in ("calories", "protein_g", "carbs_g", "fat_g", "fiber_g"):
        totals[key] = round(totals[key], 1)
    return totals
