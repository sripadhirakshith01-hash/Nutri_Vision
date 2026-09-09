from pathlib import Path

import pytest

from app.ml.model_service import get_class_names, get_model, load_model_bundle, predict_food, preprocess_image


@pytest.fixture(scope="module")
def loaded_model():
    load_model_bundle()
    return get_model()


def test_model_loads(loaded_model):
    assert loaded_model is not None
    assert loaded_model.input_shape == (None, 224, 224, 3)
    assert loaded_model.output_shape == (None, 101)


def test_class_index_mapping(loaded_model):
    names = get_class_names()
    assert len(names) == 101
    assert names[0] == "apple_pie"
    assert names[76] == "pizza"
    assert names[53] == "hamburger"


def test_preprocess_shape(project_root: Path):
    from PIL import Image

    image = Image.open(project_root / "uploads" / "chicken.jpg")
    batch = preprocess_image(image)
    assert batch.shape == (1, 224, 224, 3)
    assert batch.max() > 1.5  # must stay in 0-255, not 0-1


def test_image_prediction_returns_confidence(loaded_model, burrito_image: Path):
    result = predict_food(burrito_image)
    assert "food_name" in result
    assert "confidence" in result
    assert 0 < result["confidence"] <= 100
    assert len(result["top_predictions"]) == 5
    assert result["top_predictions"][0]["food"] == result["food_name"]
    assert result["food_name"] == "breakfast_burrito"
    assert result["confidence"] > 50
