from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def auth_headers(client: TestClient):
    email = "api.tester@example.com"
    password = "correcthorse"
    register = client.post(
        "/api/auth/register",
        json={"name": "API Tester", "email": email, "password": password},
    )
    if register.status_code == 409:
        login = client.post("/api/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200
        token = login.json()["access_token"]
    else:
        assert register.status_code == 201
        token = register.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_unauthorized_access(client: TestClient):
    response = client.get("/api/predictions")
    assert response.status_code == 401


def test_login_rejects_bad_password(client: TestClient):
    response = client.post(
        "/api/auth/login",
        json={"email": "missing@example.com", "password": "not-the-password"},
    )
    assert response.status_code == 401


def test_invalid_image(client: TestClient, auth_headers: dict):
    response = client.post(
        "/api/predict",
        headers=auth_headers,
        files={"file": ("notes.txt", b"not-an-image", "text/plain")},
    )
    assert response.status_code == 400


def test_legacy_predict_can_save(client: TestClient, auth_headers: dict, burrito_image: Path):
    with burrito_image.open("rb") as handle:
        response = client.post(
            "/api/predict",
            headers=auth_headers,
            files={"file": ("burrito.jpg", handle, "image/jpeg")},
            data={"estimated_grams": "150", "save": "true"},
        )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["food_name"] == "breakfast_burrito"
    assert body["prediction_id"] is not None
    client.delete(f"/api/predictions/{body['prediction_id']}", headers=auth_headers)


def test_prediction_endpoint(client: TestClient, auth_headers: dict, burrito_image: Path):
    with burrito_image.open("rb") as handle:
        response = client.post(
            "/api/food/analyze",
            headers=auth_headers,
            files={"image": ("burrito.jpg", handle, "image/jpeg")},
        )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["food_name"] == "breakfast_burrito"
    assert body["confidence"] > 50
    assert body["prediction_id"] is None
    assert body["nutrition_per_100g"]["calories"] > 0
    assert "top_predictions" in body


def test_meal_create_and_nutrition_today(client: TestClient, auth_headers: dict):
    created = client.post(
        "/api/meals",
        headers=auth_headers,
        json={"food_name": "pizza", "estimated_grams": 250, "meal_type": "lunch"},
    )
    assert created.status_code == 201, created.text
    meal = created.json()
    assert meal["food_name"] == "pizza"
    assert meal["estimated_calories"] > 0
    assert abs(meal["estimated_calories"] - (meal["estimated_calories"])) < 0.01

    today = client.get("/api/nutrition/today", headers=auth_headers)
    assert today.status_code == 200
    payload = today.json()
    assert payload["consumed"]["meals"] >= 1
    assert "remaining" in payload

    deleted = client.delete(f"/api/meals/{meal['prediction_id']}", headers=auth_headers)
    assert deleted.status_code == 204


def test_chatbot_endpoint(client: TestClient, auth_headers: dict):
    response = client.post("/api/chat", headers=auth_headers, json={"message": "How am I doing today?"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["role"] == "assistant"
    assert body["content"]
    assert body["response"] == body["content"]
    assert body["conversationId"]
    history = client.get("/api/chat/history", headers=auth_headers, params={"conversationId": body["conversationId"]})
    assert history.status_code == 200
    payload = history.json()
    assert payload["conversationId"] == body["conversationId"]
    assert len(payload["messages"]) >= 2
