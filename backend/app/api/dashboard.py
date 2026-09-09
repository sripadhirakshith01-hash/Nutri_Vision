from datetime import date, timedelta

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.services.calorie_service import daily_progress, goal_status
from app.services.food_taxonomy import display_name
from app.services.insights import build_insights, build_recommendations
from app.services.meal_log import today_meals
from app.services.nutrition_stats import fetch_range, scale_row, sum_rows

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard")
def dashboard(user: dict = Depends(get_current_user)):
    today = date.today()
    week_start = today - timedelta(days=6)
    prev_start = week_start - timedelta(days=7)
    prev_end = week_start - timedelta(days=1)

    today_rows = fetch_range(user["user_id"], today, today)
    week_rows = fetch_range(user["user_id"], week_start, today)
    prev_rows = fetch_range(user["user_id"], prev_start, prev_end)

    today_totals = sum_rows(today_rows)
    week_totals = sum_rows(week_rows)
    prev_totals = sum_rows(prev_rows)
    progress = daily_progress(user, today_totals)
    targets = progress["targets"]

    daily = []
    for offset in range(7):
        day = week_start + timedelta(days=offset)
        day_rows = [row for row in week_rows if row["predicted_at"].date() == day]
        day_sum = sum_rows(day_rows)
        daily.append(
            {
                "date": day.isoformat(),
                "label": day.strftime("%a"),
                "calories": day_sum["calories"],
                "protein_g": day_sum["protein_g"],
                "carbs_g": day_sum["carbs_g"],
                "fat_g": day_sum["fat_g"],
                "status": goal_status(day_sum["calories"], targets["calories"] if targets else None),
            }
        )

    days_over = sum(1 for item in daily if item["status"] == "over_target")
    week_totals["days_over_calorie_target"] = days_over

    food_counts: dict[str, dict] = {}
    category_counts: dict[str, int] = {}
    for row in week_rows:
        item = scale_row(row)
        food_counts.setdefault(
            item["food_name"],
            {"food": item["food_name"], "display_name": display_name(item["food_name"]), "count": 0, "calories": 0.0},
        )
        food_counts[item["food_name"]]["count"] += 1
        food_counts[item["food_name"]]["calories"] += item["calories"]
        category = item["category"] or "other"
        category_counts[category] = category_counts.get(category, 0) + 1

    top_foods = sorted(food_counts.values(), key=lambda item: item["count"], reverse=True)[:8]
    meal_frequency = [
        {"category": key, "count": value}
        for key, value in sorted(category_counts.items(), key=lambda item: item[1], reverse=True)
    ]

    return {
        "today": today_totals,
        "targets": targets,
        "remaining": progress["remaining"],
        "goal_status": progress["goal_status"],
        "today_meals": today_meals(user["user_id"]),
        "weekly_calories": daily,
        "macros": {
            "protein_g": week_totals["protein_g"],
            "carbs_g": week_totals["carbs_g"],
            "fat_g": week_totals["fat_g"],
            "fiber_g": week_totals["fiber_g"],
        },
        "top_foods": top_foods,
        "meal_frequency": meal_frequency,
        "insights": build_insights(week_totals, prev_totals, today_totals),
        "recommendations": build_recommendations(
            user, today_totals, week_totals, targets, week_totals.get("foods") or []
        ),
    }


@router.get("/nutrition/summary")
def nutrition_summary(user: dict = Depends(get_current_user)):
    today = date.today()
    week_start = today - timedelta(days=6)
    today_totals = sum_rows(fetch_range(user["user_id"], today, today))
    week_totals = sum_rows(fetch_range(user["user_id"], week_start, today))
    progress = daily_progress(user, today_totals)
    return {
        "today": today_totals,
        "week": week_totals,
        "targets": progress["targets"],
        "remaining": progress["remaining"],
        "goal_status": progress["goal_status"],
    }
