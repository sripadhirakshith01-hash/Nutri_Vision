from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.deps import get_current_user
from app.api.predict import run_analysis
from app.schemas.predictions import PredictResponse

router = APIRouter(prefix="/api/food", tags=["food"])


@router.post("/analyze", response_model=PredictResponse)
def analyze_food(
    image: UploadFile | None = File(default=None),
    file: UploadFile | None = File(default=None),
    estimated_grams: float | None = Form(default=None),
    save: bool = Form(default=False),
    meal_type: str | None = Form(default=None),
    user: dict = Depends(get_current_user),
):
    upload = image or file
    if upload is None:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload a food image.")
    return run_analysis(upload, estimated_grams, save, user, meal_type)
