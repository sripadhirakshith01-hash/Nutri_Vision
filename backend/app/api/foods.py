from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.database.connection import get_connection
from app.services.food_lookup import get_food_by_name, serialize_food

router = APIRouter(prefix="/api/foods", tags=["foods"])


@router.get("")
def list_foods(q: str | None = Query(default=None, max_length=80), _user: dict = Depends(get_current_user)):
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        if q:
            like = f"%{q.strip()}%"
            cursor.execute(
                """
                SELECT id, food_name, protein_g, carbs_g, fat_g, fiber_g, calories, serving_size, category, source
                FROM food_nutrition
                WHERE food_name LIKE %s
                ORDER BY food_name
                """,
                (like,),
            )
        else:
            cursor.execute(
                """
                SELECT id, food_name, protein_g, carbs_g, fat_g, fiber_g, calories, serving_size, category, source
                FROM food_nutrition
                ORDER BY food_name
                """
            )
        rows = cursor.fetchall()
        cursor.close()
    finally:
        connection.close()
    return [serialize_food(row) for row in rows]


@router.get("/{food_id}")
def get_food(food_id: int, _user: dict = Depends(get_current_user)):
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, food_name, protein_g, carbs_g, fat_g, fiber_g, calories, serving_size, category, source
            FROM food_nutrition
            WHERE id = %s
            """,
            (food_id,),
        )
        row = cursor.fetchone()
        cursor.close()
    finally:
        connection.close()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food not found")
    return serialize_food(row)


__all__ = ["router", "get_food_by_name", "serialize_food"]
