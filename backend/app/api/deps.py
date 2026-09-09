from fastapi import Depends, HTTPException, status

from app.database.connection import get_connection
from app.services.auth import get_current_user_id
from app.services.nutrition import estimate_calorie_target


def fetch_user(user_id: int) -> dict | None:
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT user_id, name, email, age, gender, height, weight, activity_level, goal, created_at
            FROM users
            WHERE user_id = %s
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        return row
    finally:
        connection.close()


def get_current_user(user_id: int = Depends(get_current_user_id)) -> dict:
    user = fetch_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    user["calorie_target"] = estimate_calorie_target(user)
    return user
