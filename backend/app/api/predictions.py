from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.database.connection import get_connection
from app.schemas.predictions import FeedbackRequest, MealUpdate, PortionUpdate
from app.services.food_lookup import normalize_food_name
from app.services.meal_log import delete_meal, get_meal, list_meals, update_meal

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


@router.get("")
def list_predictions(
    q: str | None = Query(default=None, max_length=80),
    date_from: date | None = None,
    date_to: date | None = None,
    user: dict = Depends(get_current_user),
):
    return list_meals(user["user_id"], q=q, date_from=date_from, date_to=date_to)


@router.get("/{prediction_id}")
def get_prediction(prediction_id: int, user: dict = Depends(get_current_user)):
    meal = get_meal(user["user_id"], prediction_id)
    if not meal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    return meal


@router.patch("/{prediction_id}")
def update_portion(prediction_id: int, payload: PortionUpdate, user: dict = Depends(get_current_user)):
    try:
        meal = update_meal(
            user["user_id"],
            prediction_id,
            estimated_grams=payload.estimated_grams,
            food_name=payload.food_name,
            meal_type=payload.meal_type,
        )
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nutrition data is missing for this food")
    return {
        "prediction_id": prediction_id,
        "estimated_grams": meal["estimated_grams"],
        "estimated": {
            "protein_g": meal["protein_g"],
            "carbs_g": meal["carbs_g"],
            "fat_g": meal["fat_g"],
            "fiber_g": meal["fiber_g"],
            "calories": meal["estimated_calories"],
        },
        "meal": meal,
    }


@router.put("/{prediction_id}")
def replace_prediction(prediction_id: int, payload: MealUpdate, user: dict = Depends(get_current_user)):
    try:
        meal = update_meal(
            user["user_id"],
            prediction_id,
            estimated_grams=payload.estimated_grams,
            food_name=payload.food_name,
            meal_type=payload.meal_type,
        )
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nutrition data is missing for this food")
    return meal


@router.delete("/{prediction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prediction(prediction_id: int, user: dict = Depends(get_current_user)):
    if not delete_meal(user["user_id"], prediction_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")


@router.post("/{prediction_id}/feedback")
def add_feedback(prediction_id: int, payload: FeedbackRequest, user: dict = Depends(get_current_user)):
    meal = get_meal(user["user_id"], prediction_id)
    if not meal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")

    actual = normalize_food_name(payload.actual_food) if payload.actual_food else None
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO prediction_feedback
                (prediction_id, user_id, predicted_food, actual_food, correct)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (prediction_id, user["user_id"], meal["food_name"], actual, 1 if payload.correct else 0),
        )
        if actual and not payload.correct:
            try:
                update_meal(user["user_id"], prediction_id, food_name=actual)
            except KeyError:
                pass
        connection.commit()
        feedback_id = cursor.lastrowid
        cursor.close()
    finally:
        connection.close()

    return {
        "feedback_id": feedback_id,
        "prediction_id": prediction_id,
        "correct": payload.correct,
        "actual_food": actual,
    }
