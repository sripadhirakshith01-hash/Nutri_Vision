from __future__ import annotations

from typing import Any

from app.services.food_taxonomy import FRIED_FOODS, HIGH_PROTEIN_FOODS, VEGETABLE_FOODS, display_name


def build_insights(weekly: dict[str, Any], previous: dict[str, Any], today: dict[str, Any]) -> list[dict[str, str]]:
    insights: list[dict[str, str]] = []

    week_cal = weekly.get("calories") or 0
    prev_cal = previous.get("calories") or 0
    if week_cal and prev_cal:
        delta = ((week_cal - prev_cal) / prev_cal) * 100
        if abs(delta) >= 5:
            direction = "more" if delta > 0 else "fewer"
            insights.append(
                {
                    "icon": "flame",
                    "tone": "warn" if delta > 0 else "good",
                    "text": f"You consumed {abs(delta):.0f}% {direction} calories this week than last week.",
                }
            )
    elif week_cal:
        insights.append(
            {
                "icon": "flame",
                "tone": "info",
                "text": f"You logged {week_cal:.0f} estimated kcal this week.",
            }
        )

    days = max(weekly.get("active_days") or 1, 1)
    avg_protein = (weekly.get("protein_g") or 0) / days
    if weekly.get("protein_g"):
        insights.append(
            {
                "icon": "beef",
                "tone": "info",
                "text": f"Your average protein intake is {avg_protein:.0f}g/day this week.",
            }
        )

    veg_count = weekly.get("vegetable_count") or 0
    if veg_count:
        insights.append(
            {
                "icon": "salad",
                "tone": "good",
                "text": f"You ate vegetables {veg_count} time{'s' if veg_count != 1 else ''} this week.",
            }
        )

    fried_count = weekly.get("fried_count") or 0
    if fried_count:
        insights.append(
            {
                "icon": "alert",
                "tone": "warn",
                "text": f"You consumed fried foods {fried_count} time{'s' if fried_count != 1 else ''} this week.",
            }
        )

    if not insights:
        insights.append(
            {
                "icon": "info",
                "tone": "info",
                "text": "Log a few meals to see nutrition insights based on your history.",
            }
        )

    return insights[:6]


def build_recommendations(
    profile: dict[str, Any],
    today: dict[str, Any],
    weekly: dict[str, Any],
    targets: dict[str, Any] | None,
    recent_foods: list[str],
) -> list[dict[str, str]]:
    recs: list[dict[str, str]] = []
    goal = (profile.get("goal") or "general_fitness").replace("_", " ")

    if targets:
        cal = today.get("calories") or 0
        protein = today.get("protein_g") or 0
        if cal and cal > targets["calories"] * 1.05:
            recs.append(
                {
                    "title": "Calories above target",
                    "text": f"Today's estimated intake is {cal:.0f} kcal versus your {targets['calories']} kcal estimate.",
                }
            )
        elif cal and cal < targets["calories"] * 0.55 and cal > 0:
            recs.append(
                {
                    "title": "Intake looks light so far",
                    "text": "You still have room toward your estimated calorie target. Log upcoming meals as you go.",
                }
            )

        if protein < targets["protein_g"] * 0.6:
            recs.append(
                {
                    "title": "You are low on protein today",
                    "text": "Consider a higher-protein meal next — eggs, grilled salmon, or steak if it fits your plan.",
                }
            )

        over_days = weekly.get("days_over_calorie_target") or 0
        if over_days >= 3:
            recs.append(
                {
                    "title": "Calorie streak above target",
                    "text": f"Your estimated calorie intake has been higher than your target for {over_days} of the last 7 days.",
                }
            )
    else:
        recs.append(
            {
                "title": "Complete your profile",
                "text": "Add age, height, weight, activity, and goal to see an estimated daily calorie target.",
            }
        )

    if any(food in FRIED_FOODS for food in recent_foods[-5:]):
        recs.append(
            {
                "title": "Balance fried meals",
                "text": "A recent log includes fried food. Pair the next meal with a salad or steamed vegetables.",
            }
        )

    if recent_foods and not any(food in HIGH_PROTEIN_FOODS | VEGETABLE_FOODS for food in recent_foods[:3]):
        recs.append(
            {
                "title": "Add variety",
                "text": f"Recent meals leaned on {display_name(recent_foods[0])}. Mix in a vegetable or lean protein next.",
            }
        )

    if not recs:
        recs.append(
            {
                "title": f"On track for {goal}",
                "text": "Keep logging meals so recommendations stay based on your actual history.",
            }
        )

    recs.append(
        {
            "title": "General wellness only",
            "text": "These suggestions are not medical advice and estimates are based on portion size plus typical nutrition values.",
        }
    )
    return recs[:5]
