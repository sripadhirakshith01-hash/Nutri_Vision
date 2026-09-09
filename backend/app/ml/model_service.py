"""
Food-101 inference service.

This is the single prediction implementation for the platform.
It wraps the existing EfficientNetV2-B0 .keras model and class_names.json.

Verified preprocessing
----------------------
The trained backbone contains:

* Rescaling(scale=1/255)  — 0.00392156862745098
* Normalization(ImageNet mean=[0.485, 0.456, 0.406])

The model therefore expects RGB float32 pixels in the **[0, 255]** range
at **224×224**. Dividing by 255 before inference double-scales the image
and collapses every input to nearly the same softmax (observed on the
existing sample images). That step from the original model.py is not used.

The model is loaded once and reused for every request.
"""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

INPUT_SIZE = (224, 224)
TOP_K = 5

_model = None
_class_names: list[str] | None = None


class ModelNotReadyError(RuntimeError):
    pass


def _load_class_names(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8") as handle:
        names = json.load(handle)
    if not isinstance(names, list) or not names:
        raise ValueError(f"class_names.json must be a non-empty list: {path}")
    return [str(name) for name in names]


def load_model_bundle(model_path: Path | None = None, class_names_path: Path | None = None) -> None:
    """Load the .keras model and class names once. Safe to call repeatedly."""
    global _model, _class_names

    if _model is not None and _class_names is not None:
        return

    from app.config import get_settings

    settings = get_settings()
    model_file = Path(model_path) if model_path else settings.resolved_model_path
    names_file = Path(class_names_path) if class_names_path else settings.resolved_class_names_path

    if not model_file.exists():
        raise FileNotFoundError(f"Keras model not found: {model_file}")
    if not names_file.exists():
        raise FileNotFoundError(f"class_names.json not found: {names_file}")

    import os

    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    import tensorflow as tf

    _model = tf.keras.models.load_model(model_file, compile=False)
    _class_names = _load_class_names(names_file)

    output_classes = int(_model.output_shape[-1])
    if output_classes != len(_class_names):
        raise ValueError(
            f"Model outputs {output_classes} classes but class_names.json has {len(_class_names)}"
        )


def get_model():
    if _model is None:
        load_model_bundle()
    return _model


def get_class_names() -> list[str]:
    if _class_names is None:
        load_model_bundle()
    assert _class_names is not None
    return _class_names


def preprocess_image(image: Image.Image) -> np.ndarray:
    """Match the trained EfficientNetV2-B0 input: RGB, 224×224, float32 [0, 255]."""
    image = image.convert("RGB").resize(INPUT_SIZE, Image.Resampling.BILINEAR)
    array = np.asarray(image, dtype=np.float32)
    return np.expand_dims(array, axis=0)


def _open_image(image: Image.Image | bytes | Path | str) -> Image.Image:
    if isinstance(image, Image.Image):
        return image
    if isinstance(image, (bytes, bytearray)):
        return Image.open(BytesIO(image))
    return Image.open(image)


def predict_food(image: Image.Image | bytes | Path | str, top_k: int = TOP_K) -> dict[str, Any]:
    """
    Run Food-101 inference.

    Returns:
        {
            "food_name": "pizza",
            "confidence": 92.45,
            "top_predictions": [{"food": "pizza", "confidence": 92.45}, ...]
        }
    """
    model = get_model()
    class_names = get_class_names()

    pil_image = _open_image(image)
    batch = preprocess_image(pil_image)
    probabilities = model.predict(batch, verbose=0)[0]

    k = min(top_k, len(class_names))
    top_indices = np.argsort(probabilities)[-k:][::-1]
    top_predictions = [
        {
            "food": class_names[int(index)],
            "confidence": round(float(probabilities[int(index)]) * 100, 2),
        }
        for index in top_indices
    ]

    return {
        "food_name": top_predictions[0]["food"],
        "confidence": top_predictions[0]["confidence"],
        "top_predictions": top_predictions,
    }
