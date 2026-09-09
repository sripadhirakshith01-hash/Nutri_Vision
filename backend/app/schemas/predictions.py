from datetime import datetime

from pydantic import BaseModel, Field


class TopPrediction(BaseModel):
    food: str
    display_name: str
    confidence: float


class NutritionValues(BaseModel):
    protein_g: float
    carbs_g: float
    fat_g: float = 0
    fiber_g: float = 0
    calories: float
    serving_size: float
    basis: str


class PredictResponse(BaseModel):
    prediction_id: int | None = None
    food_name: str
    display_name: str
    confidence: float
    low_confidence: bool
    top_predictions: list[TopPrediction]
    nutrition_per_100g: NutritionValues | None = None
    estimated: NutritionValues | None = None
    estimated_grams: float | None = None
    image_path: str | None = None
    nutrition_missing: bool = False
    meal_type: str | None = None


class PortionUpdate(BaseModel):
    estimated_grams: float = Field(ge=10, le=2000)
    food_name: str | None = Field(default=None, max_length=100)
    meal_type: str | None = Field(default=None, max_length=32)


class MealCreate(BaseModel):
    food_name: str = Field(min_length=1, max_length=100)
    estimated_grams: float = Field(ge=10, le=2000)
    meal_type: str | None = Field(default=None, max_length=32)
    confidence: float | None = Field(default=None, ge=0, le=100)
    image_path: str | None = Field(default=None, max_length=255)


class MealUpdate(BaseModel):
    food_name: str | None = Field(default=None, max_length=100)
    estimated_grams: float | None = Field(default=None, ge=10, le=2000)
    meal_type: str | None = Field(default=None, max_length=32)


class FeedbackRequest(BaseModel):
    correct: bool
    actual_food: str | None = Field(default=None, max_length=100)


class PredictionListItem(BaseModel):
    prediction_id: int
    food_name: str
    display_name: str
    confidence: float
    estimated_grams: float | None
    estimated_calories: float | None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    fiber_g: float | None = None
    image_path: str | None
    predicted_at: datetime
    category: str | None = None
    meal_type: str | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatMessage(BaseModel):
    message_id: int | None = None
    role: str
    content: str
    created_at: datetime | None = None
