"""NutriCoach — personalized nutrition assistant with a local fallback."""

from __future__ import annotations

import re
from typing import Any

from datetime import date

from app.database.connection import get_connection
from app.services.calorie_service import daily_progress, infer_meal_type
from app.services.meal_log import list_meals
from app.services.nutrition import estimate_calorie_target
from app.services.nutrition_stats import fetch_range, sum_rows

MEDICAL_PATTERN = re.compile(
    r"\b(diagnos|disease|cancer|diabetes treatment|medication|prescription|"
    r"eating disorder|anorex|bulim|purg|starve myself|binge|self[- ]harm)\b",
    re.IGNORECASE,
)

MEDICAL_REPLY = (
    "I can't help with medical diagnoses, treatment, or eating-disorder concerns. "
    "Please talk with a qualified healthcare professional. "
    "If you are in crisis in the US, call or text 988."
)

DISCLAIMER = (
    "Nutrition values are estimates based on typical per-100g data and the portion you logged. "
    "They are not medical advice."
)


def _today_totals(user_id: int) -> dict[str, Any]:
    today = date.today()
    return sum_rows(fetch_range(user_id, today, today))


def build_context(user: dict[str, Any]) -> dict[str, Any]:
    totals = _today_totals(user["user_id"])
    targets = estimate_calorie_target(user)
    progress = daily_progress(user, totals)
    recent = list_meals(user["user_id"])[:8]
    remaining = progress["remaining"]
    return {
        "name": user.get("name"),
        "age": user.get("age"),
        "height": float(user["height"]) if user.get("height") is not None else None,
        "weight": float(user["weight"]) if user.get("weight") is not None else None,
        "goal": (user.get("goal") or "general_fitness").replace("_", " "),
        "activity_level": (user.get("activity_level") or "").replace("_", " "),
        "target_calories": targets["calories"] if targets else None,
        "target_protein_g": targets["protein_g"] if targets else None,
        "target_carbs_g": targets["carbs_g"] if targets else None,
        "target_fat_g": targets["fat_g"] if targets else None,
        "consumed_calories": totals.get("calories") or 0,
        "protein_g": totals.get("protein_g") or 0,
        "carbs_g": totals.get("carbs_g") or 0,
        "fat_g": totals.get("fat_g") or 0,
        "fiber_g": totals.get("fiber_g") or 0,
        "meals_today": totals.get("meals") or 0,
        "remaining_calories": remaining["calories"] if remaining else None,
        "remaining_protein_g": remaining["protein_g"] if remaining else None,
        "goal_status": progress["goal_status"],
        "recent_meals": [
            {
                "food": item["display_name"],
                "calories": item["estimated_calories"],
                "meal_type": item["meal_type"],
            }
            for item in recent
        ],
    }


def _meal_line(ctx: dict[str, Any]) -> str:
    meals = ctx.get("recent_meals") or []
    today = [m for m in meals if m.get("meal_type")]
    if not today:
        return "You have not logged any meals yet today."
    names = ", ".join(f"{m['food']} ({m.get('calories') or 0:.0f} kcal)" for m in meals[:5])
    return f"Logged so far: {names}."


def _suggest_for_remaining(remaining: float | None, protein_gap: float | None, kind: str) -> str:
    if remaining is None:
        return (
            "Add your age, height, weight, activity, and goal in Profile so I can size a suggestion "
            "against an estimated daily target."
        )
    if remaining <= 0:
        return (
            f"You are around your estimated calorie target for today. "
            f"If you are still hungry, a lighter option such as a salad, edamame, or grilled salmon "
            f"is a gentler next meal than stacking another large dish. {DISCLAIMER}"
        )
    protein_note = ""
    if protein_gap and protein_gap > 15:
        protein_note = " Lean toward protein — omelette, grilled salmon, steak, or edamame would help close the gap."

    if remaining >= 700:
        ideas = {
            "dinner": "grilled salmon with vegetables, chicken curry with a modest rice portion, or steak and a salad",
            "breakfast": "eggs benedict, an omelette, or a breakfast burrito",
            "workout": "grilled salmon, steak, or a chicken dish plus a carbohydrate such as rice or a baked potato",
            "protein": "grilled salmon, steak, omelette, or edamame with a grain",
            "default": "a balanced plate such as grilled salmon and vegetables, bibimbap, or chicken curry",
        }
    elif remaining >= 400:
        ideas = {
            "dinner": "caesar salad with extra protein, sushi, or shrimp and grits",
            "breakfast": "omelette, pancakes in a modest portion, or Greek yogurt-style frozen yogurt if you want something lighter",
            "workout": "edamame, sashimi, or an omelette",
            "protein": "omelette, sashimi, or a smaller steak portion",
            "default": "a moderate meal such as sushi, a salad with protein, or tacos",
        }
    else:
        ideas = {
            "dinner": "miso soup, a small salad, or edamame",
            "breakfast": "a smaller omelette or fruit-style frozen yogurt",
            "workout": "edamame or a small omelette",
            "protein": "edamame, sashimi, or a couple of eggs",
            "default": "a lighter bite such as miso soup, seaweed salad, or edamame",
        }
    suggestion = ideas.get(kind, ideas["default"])
    return (
        f"You have about {remaining:.0f} estimated calories remaining today. "
        f"A Food-101 option that would fit well: {suggestion}.{protein_note} {DISCLAIMER}"
    )


def _food_from_text(text: str):
    from app.services.food_lookup import get_food_by_name
    from app.services.food_taxonomy import FOOD_CATEGORIES

    lowered = text.lower().replace("-", " ")
    hits: list[str] = []
    for key in FOOD_CATEGORIES:
        label = key.replace("_", " ")
        if label in lowered or key in lowered:
            hits.append(key)
    hits.sort(key=lambda name: len(name.replace("_", " ")), reverse=True)
    return get_food_by_name(hits[0]) if hits else None


def _history_food_hint(history: list[dict]) -> str:
    for item in reversed(history or []):
        content = (item.get("content") or "").lower()
        food = _food_from_text(content)
        if food:
            return food["food_name"]
        classified = item.get("food_name")
        if classified:
            return classified
    return ""


def local_reply(message: str, ctx: dict[str, Any]) -> str:
    if MEDICAL_PATTERN.search(message):
        return MEDICAL_REPLY

    classified = ctx.get("classified_food")
    if classified and classified.get("display_name"):
        per = classified.get("nutrition_per_100g") or {}
        name = classified["display_name"]
        conf = classified.get("confidence") or 0
        nutrition = ""
        if per:
            nutrition = (
                f"**Estimated nutrition (typical per 100g, not measured from the photo):** "
                f"{per.get('calories')} kcal, protein {per.get('protein_g')} g, "
                f"carbs {per.get('carbs_g')} g, fat {per.get('fat_g')} g, fiber {per.get('fiber_g')} g. "
            )
        return (
            f"**Short answer**\nThe Food-101 model identified this as **{name}** "
            f"({conf:.0f}% confidence). That is a class prediction, not a calorie reading.\n\n"
            f"**Explanation**\n{nutrition}"
            f"Actual calories vary with portion, toppings, and cooking method.\n\n"
            f"**Practical recommendation**\nLog a serving size you actually ate on the Analyze page for a better estimate. {DISCLAIMER}"
        )

    text = message.lower().strip()
    catalog = _food_from_text(text) or _food_from_text(_history_food_hint(ctx.get("history") or []))
    if catalog and any(k in text for k in ("calorie", "protein", "carb", "fat", "fiber", "nutrition", "healthy", "how much")):
        name = catalog["display_name"]
        return (
            f"**Short answer**\nTypical database values for {name} are about "
            f"{catalog.get('calories')} kcal, {catalog.get('protein_g')} g protein, "
            f"{catalog.get('carbs_g')} g carbs, and {catalog.get('fat_g')} g fat per 100g.\n\n"
            f"**Explanation**\nThese come from NutriVision's nutrition table, not from a lab analysis of a specific plate. "
            f"A 200g serving would be roughly double those numbers.\n\n"
            f"**Practical recommendation**\nAdjust for how the food is cooked and what is served with it. {DISCLAIMER}"
        )

    consumed = ctx["consumed_calories"]
    target = ctx["target_calories"]
    remaining = ctx["remaining_calories"]
    protein = ctx["protein_g"]
    protein_target = ctx["target_protein_g"]
    protein_gap = (protein_target - protein) if protein_target is not None else None
    name = ctx.get("name") or "there"
    goal = ctx.get("goal") or "your goal"

    if any(k in text for k in ("how am i doing", "analyze my nutrition", "how's my day", "how is my day")):
        target_bit = f" against an estimated {target:.0f} kcal target" if target else ""
        remaining_bit = (
            f" About {remaining:.0f} kcal remain."
            if remaining is not None and remaining > 0
            else " You are near or above your estimated target."
            if remaining is not None
            else ""
        )
        protein_bit = (
            f" Protein so far is {protein:.0f}g"
            + (f" of about {protein_target:.0f}g." if protein_target else ".")
        )
        return (
            f"Hi {name}. You have logged about {consumed:.0f} kcal today{target_bit}."
            f"{remaining_bit} {protein_bit} {_meal_line(ctx)} "
            f"Your stated goal is {goal}. Keep logging meals so this stays based on your actual day. {DISCLAIMER}"
        )

    if any(k in text for k in ("how many calories", "consumed today", "eaten today", "calories have i")):
        extra = f" Estimated remaining: {remaining:.0f} kcal." if remaining is not None else " Set up your profile to see remaining calories."
        return f"You have consumed about {consumed:.0f} estimated kcal today across {ctx['meals_today']} meal(s).{extra} {DISCLAIMER}"

    if "protein" in text and any(k in text for k in ("enough", "low", "am i", "getting")):
        if protein_target is None:
            return "I need your profile (age, height, weight, activity, goal) to compare protein against an estimated target."
        if protein >= protein_target * 0.9:
            return f"You are close to your estimated protein target: {protein:.0f}g of about {protein_target:.0f}g today. {DISCLAIMER}"
        return (
            f"Protein looks a bit light: {protein:.0f}g of about {protein_target:.0f}g so far. "
            f"Eggs, grilled salmon, steak, or edamame would raise it without guessing from a photo. {DISCLAIMER}"
        )

    if "high-protein" in text or "high protein" in text or "protein breakfast" in text:
        return _suggest_for_remaining(remaining, protein_gap, "protein" if "breakfast" not in text else "breakfast")

    if "after my workout" in text or "post-workout" in text or "after workout" in text:
        return _suggest_for_remaining(remaining, protein_gap, "workout")

    if "dinner" in text or "tonight" in text or "eat tonight" in text:
        return _suggest_for_remaining(remaining, protein_gap, "dinner")

    if "breakfast" in text:
        return _suggest_for_remaining(remaining, protein_gap, "breakfast")

    if "remaining" in text or "left today" in text or "suggest a meal" in text or "what should i eat" in text:
        kind = infer_meal_type()
        mapped = "dinner" if kind == "dinner" else "breakfast" if kind == "breakfast" else "default"
        return _suggest_for_remaining(remaining, protein_gap, mapped)

    if "fiber" in text:
        fiber = ctx.get("fiber_g") or 0
        return (
            f"Logged fiber so far is about {fiber:.0f}g (estimate). "
            f"Salads, edamame, hummus, and guacamole are higher-fiber Food-101 options. {DISCLAIMER}"
        )

    meal_hint = _meal_line(ctx)
    remaining_hint = (
        f" About {remaining:.0f} estimated kcal remain."
        if remaining is not None
        else " Complete your profile to unlock a calorie remaining estimate."
    )
    return (
        f"I can use today's log to help with calories, macros, and meal ideas. "
        f"So far you are at about {consumed:.0f} kcal.{remaining_hint} {meal_hint} "
        f"Try asking how you are doing today, for a dinner idea, or for a high-protein meal. {DISCLAIMER}"
    )


def save_message(
    user_id: int,
    role: str,
    content: str,
    conversation_id: str | None = None,
) -> dict[str, Any]:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO chat_messages (user_id, role, content, conversation_id) VALUES (%s, %s, %s, %s)",
            (user_id, role, content, conversation_id),
        )
        message_id = cursor.lastrowid
        connection.commit()
        cursor.close()
    finally:
        connection.close()
    return {
        "message_id": message_id,
        "role": role,
        "content": content,
        "conversation_id": conversation_id,
    }


def list_history(user_id: int, limit: int = 40, conversation_id: str | None = None) -> list[dict[str, Any]]:
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        if conversation_id:
            cursor.execute(
                """
                SELECT message_id, role, content, created_at, conversation_id
                FROM chat_messages
                WHERE user_id = %s AND conversation_id = %s
                ORDER BY message_id DESC
                LIMIT %s
                """,
                (user_id, conversation_id, limit),
            )
        else:
            cursor.execute(
                """
                SELECT message_id, role, content, created_at, conversation_id
                FROM chat_messages
                WHERE user_id = %s
                ORDER BY message_id DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
        rows = list(reversed(cursor.fetchall()))
        cursor.close()
    finally:
        connection.close()
    return rows


def latest_conversation_id(user_id: int) -> str | None:
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT conversation_id
            FROM chat_messages
            WHERE user_id = %s AND conversation_id IS NOT NULL
            ORDER BY message_id DESC
            LIMIT 1
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        cursor.close()
    finally:
        connection.close()
    return row["conversation_id"] if row else None


def clear_conversation(user_id: int, conversation_id: str) -> None:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM chat_messages WHERE user_id = %s AND conversation_id = %s",
            (user_id, conversation_id),
        )
        connection.commit()
        cursor.close()
    finally:
        connection.close()
