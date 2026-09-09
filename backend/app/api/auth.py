from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.database.connection import get_connection
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserPublic
from app.services.auth import create_access_token, hash_password, verify_password
from app.services.nutrition import estimate_calorie_target

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _public_user(row: dict) -> UserPublic:
    return UserPublic(
        user_id=row["user_id"],
        name=row["name"],
        email=row["email"],
        age=row.get("age"),
        gender=row.get("gender"),
        height=float(row["height"]) if row.get("height") is not None else None,
        weight=float(row["weight"]) if row.get("weight") is not None else None,
        activity_level=row.get("activity_level"),
        goal=row.get("goal"),
        calorie_target=estimate_calorie_target(row),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest):
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (payload.email.lower(),))
        if cursor.fetchone():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")

        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES (%s, %s, %s)
            """,
            (payload.name.strip(), payload.email.lower(), hash_password(payload.password)),
        )
        user_id = cursor.lastrowid
        connection.commit()
        cursor.execute(
            "SELECT user_id, name, email, age, gender, height, weight, activity_level, goal FROM users WHERE user_id = %s",
            (user_id,),
        )
        user = cursor.fetchone()
        cursor.close()
    finally:
        connection.close()

    token = create_access_token(user["user_id"], user["email"])
    return TokenResponse(access_token=token, user=_public_user(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id, name, email, password_hash, age, gender, height, weight, activity_level, goal FROM users WHERE email = %s",
            (payload.email.lower(),),
        )
        user = cursor.fetchone()
        cursor.close()
    finally:
        connection.close()

    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(user["user_id"], user["email"])
    return TokenResponse(access_token=token, user=_public_user(user))


@router.get("/me", response_model=UserPublic)
def me(user: dict = Depends(get_current_user)):
    return _public_user(user)


@router.post("/logout")
def logout():
    return {"ok": True}
