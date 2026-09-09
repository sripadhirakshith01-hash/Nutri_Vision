from __future__ import annotations

import io
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.api.deps import get_current_user
from app.config import get_settings
from app.ml.model_service import ModelNotReadyError
from app.schemas.predictions import NutritionValues, PredictResponse, TopPrediction
from app.services.calorie_service import infer_meal_type
from app.services.food_classifier import classify_image
from app.services.meal_log import create_meal
from app.services.nutrition import scale_nutrition

ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def validate_and_save(upload: UploadFile) -> Path:
    settings = get_settings()
    content_type = (upload.content_type or "").lower()
    suffix = Path(upload.filename or "upload.jpg").suffix.lower()
    if content_type not in ALLOWED_TYPES and suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported image format. Use JPEG, PNG, or WebP.",
        )

    data = upload.file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded file is empty.")
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image is too large. Maximum size is {settings.max_upload_mb} MB.",
        )

    try:
        with Image.open(io.BytesIO(data)) as image:
            image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file.") from exc

    safe_suffix = suffix if suffix in ALLOWED_SUFFIXES else ".jpg"
    dest = settings.resolved_upload_dir / f"{uuid.uuid4().hex}{safe_suffix}"
    dest.write_bytes(data)
    return dest


def to_response(payload: dict, image_path: str | None, prediction_id: int | None = None) -> PredictResponse:
    per_100 = payload.get("nutrition_per_100g")
    estimated = payload.get("estimated")
    return PredictResponse(
        prediction_id=prediction_id,
        food_name=payload["food_name"],
        display_name=payload["display_name"],
        confidence=payload["confidence"],
        low_confidence=payload["low_confidence"],
        top_predictions=[TopPrediction(**item) for item in payload["top_predictions"]],
        nutrition_per_100g=NutritionValues(**per_100) if per_100 else None,
        estimated=NutritionValues(**estimated) if estimated else None,
        estimated_grams=payload.get("estimated_grams"),
        image_path=image_path,
        nutrition_missing=payload.get("nutrition_missing", False),
        meal_type=infer_meal_type(),
    )


def run_analysis(
    upload: UploadFile,
    estimated_grams: float | None,
    save: bool,
    user: dict,
    meal_type: str | None = None,
) -> PredictResponse:
    if estimated_grams is not None and (estimated_grams < 10 or estimated_grams > 2000):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Portion size must be between 10g and 2000g.",
        )

    saved_path = validate_and_save(upload)
    image_path = f"uploads/{saved_path.name}"

    try:
        payload = classify_image(saved_path, estimated_grams)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The food recognition model is not available.",
        ) from exc
    except (ModelNotReadyError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The food recognition model failed to load.",
        ) from exc
    except UnidentifiedImageError as exc:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file.") from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Food analysis failed. Please try another image.",
        ) from exc

    prediction_id = None
    food = payload.get("food")
    if save and food:
        try:
            meal = create_meal(
                user["user_id"],
                payload["food_name"],
                estimated_grams or 100,
                meal_type=meal_type or infer_meal_type(),
                confidence=payload["confidence"],
                image_path=image_path,
            )
            prediction_id = meal["prediction_id"]
            if estimated_grams is None:
                scaled = scale_nutrition(food, 100)
                payload["estimated"] = {
                    "protein_g": scaled["protein_g"],
                    "carbs_g": scaled["carbs_g"],
                    "fat_g": scaled["fat_g"],
                    "fiber_g": scaled.get("fiber_g") or 0,
                    "calories": scaled["calories"],
                    "serving_size": 100,
                    "basis": "estimated 100g serving",
                }
                payload["estimated_grams"] = 100
        except KeyError:
            pass

    return to_response(payload, image_path, prediction_id)


router = APIRouter(prefix="/api", tags=["predict"])


@router.post("/predict", response_model=PredictResponse)
def predict(
    file: UploadFile = File(...),
    estimated_grams: float | None = Form(default=None),
    save: bool = Form(default=True),
    meal_type: str | None = Form(default=None),
    user: dict = Depends(get_current_user),
):
    return run_analysis(file, estimated_grams, save, user, meal_type)
