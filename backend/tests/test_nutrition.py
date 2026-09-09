from app.ai.factory import get_nutrition_provider
from app.ai.local_provider import LocalProvider
from app.services.calorie_service import goal_status, infer_meal_type, remaining_budget
from app.services.chatbot_service import MEDICAL_REPLY, local_reply
from app.services.nutrition import scale_nutrition


def test_scale_nutrition_is_proportional():
    per_100 = {
        "calories": 285,
        "protein_g": 12,
        "carbs_g": 36,
        "fat_g": 10,
        "fiber_g": 2,
        "serving_size": 100,
    }
    scaled = scale_nutrition(per_100, 250)
    assert scaled["calories"] == 712.5
    assert scaled["protein_g"] == 30.0
    assert scaled["carbs_g"] == 90.0
    assert scaled["fat_g"] == 25.0
    assert scaled["fiber_g"] == 5.0


def test_remaining_and_goal_status():
    remaining = remaining_budget({"calories": 1450, "protein_g": 80, "carbs_g": 140, "fat_g": 40}, {
        "calories": 2200,
        "protein_g": 140,
        "carbs_g": 220,
        "fat_g": 70,
    })
    assert remaining["calories"] == 750
    assert goal_status(1450, 2200) == "under_target"
    assert goal_status(2200, 2200) == "near_target"
    assert goal_status(2500, 2200) == "over_target"


def test_infer_meal_type_bounds():
    from datetime import datetime

    assert infer_meal_type(datetime(2026, 8, 26, 8, 0)) == "breakfast"
    assert infer_meal_type(datetime(2026, 8, 26, 12, 30)) == "lunch"
    assert infer_meal_type(datetime(2026, 8, 26, 19, 0)) == "dinner"


def test_chatbot_uses_logged_calories():
    ctx = {
        "name": "CB",
        "goal": "maintain weight",
        "consumed_calories": 1450,
        "target_calories": 2200,
        "remaining_calories": 750,
        "protein_g": 70,
        "target_protein_g": 140,
        "meals_today": 2,
        "recent_meals": [{"food": "Pizza", "calories": 712, "meal_type": "lunch"}],
        "fiber_g": 5,
    }
    reply = local_reply("How many calories have I consumed today?", ctx)
    assert "1450" in reply
    assert "750" in reply


def test_chatbot_suggests_dinner_from_remaining():
    ctx = {
        "name": "CB",
        "goal": "maintain weight",
        "consumed_calories": 1500,
        "target_calories": 2200,
        "remaining_calories": 700,
        "protein_g": 60,
        "target_protein_g": 140,
        "meals_today": 2,
        "recent_meals": [],
        "fiber_g": 4,
    }
    reply = local_reply("I have 700 calories remaining. Suggest a meal for dinner.", ctx)
    assert "700" in reply
    assert "estimate" in reply.lower() or "estimated" in reply.lower()


def test_chatbot_refuses_medical_advice():
    ctx = {
        "name": "CB",
        "goal": "maintain",
        "consumed_calories": 0,
        "target_calories": 2200,
        "remaining_calories": 2200,
        "protein_g": 0,
        "target_protein_g": 140,
        "meals_today": 0,
        "recent_meals": [],
        "fiber_g": 0,
    }
    reply = local_reply("Can you diagnose my eating disorder?", ctx)
    assert reply == MEDICAL_REPLY


def test_provider_local_when_forced(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "local")
    from app.config import get_settings

    get_settings.cache_clear()
    provider = get_nutrition_provider()
    assert isinstance(provider, LocalProvider)
    assert provider.name == "local"
    get_settings.cache_clear()


def test_local_reply_uses_classified_food():
    ctx = {
        "name": "CB",
        "goal": "maintain",
        "consumed_calories": 0,
        "target_calories": 2200,
        "remaining_calories": 2200,
        "protein_g": 0,
        "target_protein_g": 140,
        "meals_today": 0,
        "recent_meals": [],
        "fiber_g": 0,
        "classified_food": {
            "display_name": "Pizza",
            "food_name": "pizza",
            "confidence": 94.0,
            "nutrition_per_100g": {"calories": 258, "protein_g": 11, "carbs_g": 33, "fat_g": 10, "fiber_g": 2.3},
        },
    }
    reply = local_reply("Is this meal healthy?", ctx)
    assert "Pizza" in reply
    assert "class prediction" in reply.lower() or "Food-101" in reply
    assert "estimate" in reply.lower()
