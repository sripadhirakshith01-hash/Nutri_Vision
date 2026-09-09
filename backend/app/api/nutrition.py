from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.services.calorie_service import daily_progress
from app.services.meal_log import list_meals
from app.services.nutrition_stats import fetch_range, sum_rows

router = APIRouter(prefix="/api/nutrition", tags=["nutrition"])


@router.get("/today")
def nutrition_today(user: dict = Depends(get_current_user)):
    today = date.today()
    totals = sum_rows(fetch_range(user["user_id"], today, today))
    progress = daily_progress(user, totals)
    return {
        "date": today.isoformat(),
        "target": progress["targets"],
        "consumed": totals,
        "remaining": progress["remaining"],
        "goal_status": progress["goal_status"],
        "meals": list_meals(user["user_id"], date_from=today, date_to=today),
    }


@router.get("/history")
def nutrition_history(days: int = Query(default=7, ge=1, le=90), user: dict = Depends(get_current_user)):
    today = date.today()
    start = today - timedelta(days=days - 1)
    rows = fetch_range(user["user_id"], start, today)
    series = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        day_rows = [row for row in rows if row["predicted_at"].date() == day]
        totals = sum_rows(day_rows)
        series.append(
            {
                "date": day.isoformat(),
                "label": day.strftime("%a"),
                "calories": totals["calories"],
                "protein_g": totals["protein_g"],
                "carbs_g": totals["carbs_g"],
                "fat_g": totals["fat_g"],
                "fiber_g": totals["fiber_g"],
                "meals": totals["meals"],
            }
        )
    return {"days": series, "totals": sum_rows(rows)}
