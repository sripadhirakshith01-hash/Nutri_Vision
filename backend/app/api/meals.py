from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.schemas.predictions import MealCreate, MealUpdate
from app.services.food_lookup import normalize_food_name
from app.services.meal_log import create_meal, delete_meal, get_meal, list_meals, update_meal

router = APIRouter(prefix="/api/meals", tags=["meals"])


@router.get("")
def get_meals(
    q: str | None = Query(default=None, max_length=80),
    date_from: date | None = None,
    date_to: date | None = None,
    user: dict = Depends(get_current_user),
):
    return list_meals(user["user_id"], q=q, date_from=date_from, date_to=date_to)


@router.post("", status_code=status.HTTP_201_CREATED)
def add_meal(payload: MealCreate, user: dict = Depends(get_current_user)):
    try:
        return create_meal(
            user["user_id"],
            normalize_food_name(payload.food_name),
            payload.estimated_grams,
            meal_type=payload.meal_type,
            confidence=payload.confidence,
            image_path=payload.image_path,
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nutrition data is unavailable for that food.",
        )


@router.get("/{meal_id}")
def read_meal(meal_id: int, user: dict = Depends(get_current_user)):
    meal = get_meal(user["user_id"], meal_id)
    if not meal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found")
    return meal


@router.put("/{meal_id}")
def edit_meal(meal_id: int, payload: MealUpdate, user: dict = Depends(get_current_user)):
    try:
        return update_meal(
            user["user_id"],
            meal_id,
            estimated_grams=payload.estimated_grams,
            food_name=normalize_food_name(payload.food_name) if payload.food_name else None,
            meal_type=payload.meal_type,
        )
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found")
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nutrition data is unavailable for that food.",
        )


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_meal(meal_id: int, user: dict = Depends(get_current_user)):
    if not delete_meal(user["user_id"], meal_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found")
