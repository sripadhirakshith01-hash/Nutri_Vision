-- NUTRITION_DATABASE schema
-- Existing food_nutrition macros are reused. Calories are derived with Atwater factors.

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS food_nutrition (
    id INT NOT NULL AUTO_INCREMENT,
    food_name VARCHAR(100) DEFAULT NULL,
    protein_g DECIMAL(6,2) DEFAULT NULL,
    carbs_g DECIMAL(6,2) DEFAULT NULL,
    fat_g DECIMAL(6,2) DEFAULT NULL,
    fiber_g DECIMAL(6,2) DEFAULT NULL,
    calories INT DEFAULT NULL,
    serving_size INT DEFAULT NULL,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS predictions (
    prediction_id INT NOT NULL AUTO_INCREMENT,
    user_id INT NULL,
    food_id INT NOT NULL,
    confidence DECIMAL(5,2) NOT NULL,
    estimated_grams DECIMAL(8,2) NULL,
    estimated_calories DECIMAL(8,2) NULL,
    meal_type VARCHAR(32) NULL,
    image_path VARCHAR(255) DEFAULT NULL,
    predicted_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (prediction_id),
    KEY food_id (food_id),
    KEY idx_predictions_user (user_id),
    CONSTRAINT predictions_ibfk_1 FOREIGN KEY (food_id) REFERENCES food_nutrition (id),
    CONSTRAINT predictions_user_fk FOREIGN KEY (user_id) REFERENCES users (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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
    CONSTRAINT feedback_prediction_fk FOREIGN KEY (prediction_id) REFERENCES predictions (prediction_id) ON DELETE CASCADE,
    CONSTRAINT feedback_user_fk FOREIGN KEY (user_id) REFERENCES users (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS chat_messages (
    message_id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    role VARCHAR(16) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (message_id),
    KEY idx_chat_user (user_id),
    CONSTRAINT chat_user_fk FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
