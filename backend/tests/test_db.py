from app.database.connection import get_connection, ping_database
from app.database.init_db import migrate


def test_mysql_connection():
    assert ping_database() is True


def test_food_lookup():
    migrate()
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, food_name, protein_g, carbs_g, fat_g, calories, serving_size FROM food_nutrition WHERE food_name = %s",
        ("pizza",),
    )
    row = cursor.fetchone()
    cursor.close()
    connection.close()
    assert row is not None
    assert row["food_name"] == "pizza"
    assert row["protein_g"] is not None
    assert row["calories"] is not None
    assert row["serving_size"] == 100


def test_prediction_insert_and_retrieve():
    migrate()
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id FROM food_nutrition WHERE food_name = %s", ("pizza",))
    food = cursor.fetchone()
    assert food is not None

    cursor.execute(
        """
        INSERT INTO predictions (food_id, confidence, estimated_grams, estimated_calories, image_path)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (food["id"], 91.25, 150, 399, "uploads/test.jpg"),
    )
    prediction_id = cursor.lastrowid
    connection.commit()

    cursor.execute(
        """
        SELECT p.prediction_id, p.confidence, f.food_name
        FROM predictions p
        JOIN food_nutrition f ON f.id = p.food_id
        WHERE p.prediction_id = %s
        """,
        (prediction_id,),
    )
    row = cursor.fetchone()
    cursor.execute("DELETE FROM predictions WHERE prediction_id = %s", (prediction_id,))
    connection.commit()
    cursor.close()
    connection.close()

    assert row["food_name"] == "pizza"
    assert float(row["confidence"]) == 91.25
