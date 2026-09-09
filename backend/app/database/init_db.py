"""Create / migrate NUTRITION_DATABASE tables without dropping existing nutrition data."""

from __future__ import annotations

import json
from pathlib import Path

from app.database.connection import get_connection


def _column_exists(cursor, table: str, column: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*) AS n
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
        """,
        (table, column),
    )
    return cursor.fetchone()["n"] > 0


def _index_exists(cursor, table: str, index: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*) AS n
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND INDEX_NAME = %s
        """,
        (table, index),
    )
    return cursor.fetchone()["n"] > 0


def _constraint_exists(cursor, table: str, constraint: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*) AS n
        FROM information_schema.TABLE_CONSTRAINTS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND CONSTRAINT_NAME = %s
        """,
        (table, constraint),
    )
    return cursor.fetchone()["n"] > 0


def _seed_catalog_if_empty(cursor) -> None:
    cursor.execute("SELECT COUNT(*) AS n FROM food_nutrition")
    if cursor.fetchone()["n"] > 0:
        return
    seed_path = Path(__file__).resolve().parents[1] / "data" / "food_nutrition_seed.json"
    if not seed_path.exists():
        return
    rows = json.loads(seed_path.read_text(encoding="utf-8"))
    for row in rows:
        cursor.execute(
            """
            INSERT INTO food_nutrition
                (food_name, protein_g, carbs_g, fat_g, fiber_g, calories, serving_size, category, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                row.get("food_name"),
                row.get("protein_g"),
                row.get("carbs_g"),
                row.get("fat_g"),
                row.get("fiber_g"),
                row.get("calories"),
                row.get("serving_size") or 100,
                row.get("category"),
                row.get("source"),
            ),
        )


def migrate() -> None:
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INT NOT NULL AUTO_INCREMENT,
            name VARCHAR(120) NOT NULL,
            email VARCHAR(255) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            age INT NULL,
            gender VARCHAR(32) NULL,
            height DECIMAL(6,2) NULL,
            weight DECIMAL(6,2) NULL,
            activity_level VARCHAR(32) NULL,
            goal VARCHAR(32) NULL,
            created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id),
            UNIQUE KEY uq_users_email (email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS food_nutrition (
            id INT NOT NULL AUTO_INCREMENT,
            food_name VARCHAR(100) DEFAULT NULL,
            protein_g DECIMAL(6,2) DEFAULT NULL,
            carbs_g DECIMAL(6,2) DEFAULT NULL,
            fat_g DECIMAL(6,2) DEFAULT NULL,
            calories INT DEFAULT NULL,
            serving_size INT DEFAULT NULL,
            created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """
    )

    if not _column_exists(cursor, "food_nutrition", "category"):
        cursor.execute("ALTER TABLE food_nutrition ADD COLUMN category VARCHAR(50) NULL")

    if not _column_exists(cursor, "food_nutrition", "source"):
        cursor.execute("ALTER TABLE food_nutrition ADD COLUMN source VARCHAR(255) NULL")

    if not _column_exists(cursor, "food_nutrition", "fiber_g"):
        cursor.execute("ALTER TABLE food_nutrition ADD COLUMN fiber_g DECIMAL(6,2) NULL")

    _seed_catalog_if_empty(cursor)

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            prediction_id INT NOT NULL AUTO_INCREMENT,
            food_id INT NOT NULL,
            confidence DECIMAL(5,2) NOT NULL,
            image_path VARCHAR(255) DEFAULT NULL,
            predicted_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (prediction_id),
            KEY food_id (food_id),
            CONSTRAINT predictions_ibfk_1 FOREIGN KEY (food_id) REFERENCES food_nutrition (id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """
    )

    if not _column_exists(cursor, "predictions", "user_id"):
        cursor.execute("ALTER TABLE predictions ADD COLUMN user_id INT NULL")
    if not _column_exists(cursor, "predictions", "estimated_grams"):
        cursor.execute("ALTER TABLE predictions ADD COLUMN estimated_grams DECIMAL(8,2) NULL")
    if not _column_exists(cursor, "predictions", "estimated_calories"):
        cursor.execute("ALTER TABLE predictions ADD COLUMN estimated_calories DECIMAL(8,2) NULL")
    if not _column_exists(cursor, "predictions", "meal_type"):
        cursor.execute("ALTER TABLE predictions ADD COLUMN meal_type VARCHAR(32) NULL")

    if not _index_exists(cursor, "predictions", "idx_predictions_user"):
        cursor.execute("CREATE INDEX idx_predictions_user ON predictions (user_id)")

    if not _constraint_exists(cursor, "predictions", "predictions_user_fk"):
        cursor.execute(
            """
            ALTER TABLE predictions
            ADD CONSTRAINT predictions_user_fk
            FOREIGN KEY (user_id) REFERENCES users (user_id)
            """
        )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS prediction_feedback (
            feedback_id INT NOT NULL AUTO_INCREMENT,
            prediction_id INT NOT NULL,
            user_id INT NOT NULL,
            predicted_food VARCHAR(100) NOT NULL,
            actual_food VARCHAR(100) NULL,
            correct TINYINT(1) NOT NULL,
            created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (feedback_id),
            KEY idx_feedback_prediction (prediction_id),
            KEY idx_feedback_user (user_id),
            CONSTRAINT feedback_prediction_fk FOREIGN KEY (prediction_id)
                REFERENCES predictions (prediction_id) ON DELETE CASCADE,
            CONSTRAINT feedback_user_fk FOREIGN KEY (user_id) REFERENCES users (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            message_id INT NOT NULL AUTO_INCREMENT,
            user_id INT NOT NULL,
            role VARCHAR(16) NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (message_id),
            KEY idx_chat_user (user_id),
            CONSTRAINT chat_user_fk FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """
    )

    if not _column_exists(cursor, "chat_messages", "conversation_id"):
        cursor.execute("ALTER TABLE chat_messages ADD COLUMN conversation_id VARCHAR(36) NULL")
    if not _index_exists(cursor, "chat_messages", "idx_chat_conversation"):
        cursor.execute("CREATE INDEX idx_chat_conversation ON chat_messages (user_id, conversation_id)")

    cursor.execute(
        """
        UPDATE chat_messages
        SET conversation_id = CONCAT('legacy-', user_id)
        WHERE conversation_id IS NULL
        """
    )

    from app.data.fiber_values import FIBER_PER_100G

    for food_name, fiber in FIBER_PER_100G.items():
        cursor.execute(
            """
            UPDATE food_nutrition
            SET fiber_g = %s
            WHERE food_name = %s AND fiber_g IS NULL
            """,
            (fiber, food_name),
        )

    # Fill missing calories from existing macros using Atwater factors. Do not invent macros.
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
        WHERE protein_g IS NOT NULL
          AND carbs_g IS NOT NULL
          AND fat_g IS NOT NULL
          AND (calories IS NULL OR serving_size IS NULL OR source IS NULL)
        """
    )

    connection.commit()
    cursor.close()
    connection.close()


if __name__ == "__main__":
    migrate()
    print("Database schema is ready.")
