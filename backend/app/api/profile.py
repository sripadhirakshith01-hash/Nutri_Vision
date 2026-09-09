from fastapi import APIRouter, Depends

from app.api.auth import _public_user
from app.api.deps import get_current_user
from app.database.connection import get_connection
from app.schemas.auth import ProfileUpdate, UserPublic

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=UserPublic)
def get_profile(user: dict = Depends(get_current_user)):
    return _public_user(user)


@router.put("", response_model=UserPublic)
def update_profile(payload: ProfileUpdate, user: dict = Depends(get_current_user)):
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return _public_user(user)

    assignments = ", ".join(f"{key} = %s" for key in updates)
    values = list(updates.values()) + [user["user_id"]]

    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(f"UPDATE users SET {assignments} WHERE user_id = %s", values)
        connection.commit()
        cursor.execute(
            "SELECT user_id, name, email, age, gender, height, weight, activity_level, goal FROM users WHERE user_id = %s",
            (user["user_id"],),
        )
        updated = cursor.fetchone()
        cursor.close()
    finally:
        connection.close()

    return _public_user(updated)
