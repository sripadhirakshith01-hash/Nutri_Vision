"""
Reuse existing food_nutrition / food101 macros.

Calories are not invented. They are calculated with the Atwater factors
(protein×4 + carbs×4 + fat×9) and stored per 100g.

Source: existing NUTRITION_DATABASE.food_nutrition rows, originally aligned
with the food101 table in this project.
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.database.connection import get_connection  # noqa: E402
from app.database.init_db import migrate  # noqa: E402
from app.services.food_taxonomy import FOOD_CATEGORIES  # noqa: E402


def seed() -> None:
    migrate()
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS n FROM food_nutrition")
    existing = cursor.fetchone()["n"]
    print(f"food_nutrition rows: {existing}")

    if existing == 0:
        cursor.execute("SHOW TABLES LIKE 'food101'")
        if cursor.fetchone():
            cursor.execute(
                """
                INSERT INTO food_nutrition (food_name, protein_g, carbs_g, fat_g, serving_size)
                SELECT food_name, protein_g_per_100g, carbohydrates_g_per_100g, fat_g_per_100g, 100
                FROM food101
                """
            )
            print(f"Copied {cursor.rowcount} rows from food101")

    cursor.execute(
        """
        UPDATE food_nutrition
        SET
            calories = ROUND((protein_g * 4) + (carbs_g * 4) + (fat_g * 9)),
            serving_size = COALESCE(serving_size, 100),
            source = COALESCE(
                source,
                'Existing NUTRITION_DATABASE macros (food_nutrition / food101); calories = Atwater 4/4/9 per 100g'
            )
        WHERE protein_g IS NOT NULL AND carbs_g IS NOT NULL AND fat_g IS NOT NULL
        """
    )
    print(f"Updated calories/serving_size on {cursor.rowcount} rows")

    for food_name, category in FOOD_CATEGORIES.items():
        cursor.execute(
            "UPDATE food_nutrition SET category = %s WHERE food_name = %s",
            (category, food_name),
        )

    connection.commit()
    cursor.execute("SELECT food_name, calories, serving_size, category FROM food_nutrition WHERE food_name = 'pizza'")
    print("pizza row:", cursor.fetchone())
    cursor.close()
    connection.close()


if __name__ == "__main__":
    seed()
