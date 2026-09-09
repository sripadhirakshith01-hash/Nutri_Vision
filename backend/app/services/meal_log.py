"""Shared meal-log operations on the existing predictions table."""

from __future__ import annotations

from datetime import date
from typing import Any

from app.services.food_lookup import get_food_by_name
from app.database.connection import get_connection
from app.services.calorie_service import infer_meal_type
from app.services.food_taxonomy import category_for, display_name
from app.services.nutrition import scale_nutrition


def serialize_meal(row: dict[str, Any]) -> dict[str, Any]:
    grams = float(row["estimated_grams"]) if row.get("estimated_grams") is not None else None
    serving = float(row["serving_size"] or 100)
    factor = (grams / serving) if grams else None
    fiber = float(row["fiber_g"]) if row.get("fiber_g") is not None else None
    return {
        "prediction_id": row["prediction_id"],
        "id": row["prediction_id"],
        "food_name": row["food_name"],
        "display_name": display_name(row["food_name"]),
        "confidence": float(row["confidence"]),
        "estimated_grams": grams,
        "estimated_calories": float(row["estimated_calories"]) if row.get("estimated_calories") is not None else None,
        "protein_g": round(float(row["protein_g"]) * factor, 1) if factor is not None and row.get("protein_g") is not None else None,
        "carbs_g": round(float(row["carbs_g"]) * factor, 1) if factor is not None and row.get("carbs_g") is not None else None,
        "fat_g": round(float(row["fat_g"]) * factor, 1) if factor is not None and row.get("fat_g") is not None else None,
        "fiber_g": round(fiber * factor, 1) if factor is not None and fiber is not None else None,
        "image_path": row.get("image_path"),
        "predicted_at": row["predicted_at"],
        "category": row.get("category") or category_for(row["food_name"]),
        "meal_type": row.get("meal_type") or infer_meal_type(row.get("predicted_at")),
    }


_SELECT = """
    SELECT p.prediction_id, p.confidence, p.estimated_grams, p.estimated_calories,
           p.image_path, p.predicted_at, p.meal_type, f.food_name, f.protein_g, f.carbs_g,
           f.fat_g, f.fiber_g, f.serving_size, f.category
    FROM predictions p
    JOIN food_nutrition f ON f.id = p.food_id
"""


def list_meals(
    user_id: int,
    q: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[dict[str, Any]]:
    clauses = ["p.user_id = %s"]
    params: list[Any] = [user_id]
    if q:
        clauses.append("f.food_name LIKE %s")
        params.append(f"%{q.strip()}%")
    if date_from:
        clauses.append("DATE(p.predicted_at) >= %s")
        params.append(date_from)
    if date_to:
        clauses.append("DATE(p.predicted_at) <= %s")
        params.append(date_to)
    where = " AND ".join(clauses)
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(f"{_SELECT} WHERE {where} ORDER BY p.predicted_at DESC", params)
        rows = cursor.fetchall()
        cursor.close()
    finally:
        connection.close()
    return [serialize_meal(row) for row in rows]


def get_meal(user_id: int, meal_id: int) -> dict[str, Any] | None:
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(f"{_SELECT} WHERE p.prediction_id = %s AND p.user_id = %s", (meal_id, user_id))
        row = cursor.fetchone()
        cursor.close()
    finally:
        connection.close()
    return serialize_meal(row) if row else None


def create_meal(
    user_id: int,
    food_name: str,
    estimated_grams: float,
    meal_type: str | None = None,
    confidence: float | None = None,
    image_path: str | None = None,
) -> dict[str, Any]:
    food = get_food_by_name(food_name)
    if not food:
        raise KeyError(food_name)
    scaled = scale_nutrition(food, estimated_grams)
    meal_type = meal_type or infer_meal_type()
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO predictions
                (user_id, food_id, confidence, estimated_grams, estimated_calories, image_path, meal_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,
                food["id"],
                confidence if confidence is not None else 100.0,
                estimated_grams,
                scaled["calories"],
                image_path,
                meal_type,
            ),
        )
        meal_id = cursor.lastrowid
        connection.commit()
        cursor.close()
    finally:
        connection.close()
    meal = get_meal(user_id, meal_id)
    assert meal is not None
    return meal


def update_meal(
    user_id: int,
    meal_id: int,
    estimated_grams: float | None = None,
    food_name: str | None = None,
    meal_type: str | None = None,
) -> dict[str, Any]:
    existing = get_meal(user_id, meal_id)
    if not existing:
        raise LookupError(str(meal_id))

    name = food_name or existing["food_name"]
    food = get_food_by_name(name)
    if not food:
        raise KeyError(name)
    grams = estimated_grams if estimated_grams is not None else existing["estimated_grams"] or 100
    scaled = scale_nutrition(food, grams)
    next_type = meal_type or existing.get("meal_type")

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE predictions
            SET food_id = %s, estimated_grams = %s, estimated_calories = %s, meal_type = %s
            WHERE prediction_id = %s AND user_id = %s
            """,
            (food["id"], grams, scaled["calories"], next_type, meal_id, user_id),
        )
        if cursor.rowcount == 0:
            raise LookupError(str(meal_id))
        connection.commit()
        cursor.close()
    finally:
        connection.close()
    meal = get_meal(user_id, meal_id)
    assert meal is not None
    return meal


def delete_meal(user_id: int, meal_id: int) -> bool:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM predictions WHERE prediction_id = %s AND user_id = %s",
            (meal_id, user_id),
        )
        deleted = cursor.rowcount > 0
        connection.commit()
        cursor.close()
    finally:
        connection.close()
    return deleted


def today_meals(user_id: int) -> list[dict[str, Any]]:
    today = date.today()
    return list(reversed(list_meals(user_id, date_from=today, date_to=today)))
