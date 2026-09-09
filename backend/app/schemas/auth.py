from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserPublic"


class UserPublic(BaseModel):
    user_id: int
    name: str
    email: str
    age: int | None = None
    gender: str | None = None
    height: float | None = None
    weight: float | None = None
    activity_level: str | None = None
    goal: str | None = None
    calorie_target: dict | None = None


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    age: int | None = Field(default=None, ge=13, le=120)
    gender: Literal["male", "female", "other", "prefer_not_to_say"] | None = None
    height: float | None = Field(default=None, gt=50, lt=250)
    weight: float | None = Field(default=None, gt=20, lt=400)
    activity_level: Literal[
        "sedentary",
        "lightly_active",
        "moderately_active",
        "very_active",
        "extra_active",
    ] | None = None
    goal: Literal["weight_loss", "maintain", "weight_gain", "general_fitness"] | None = None
