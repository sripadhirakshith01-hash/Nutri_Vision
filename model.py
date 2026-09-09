"""
CLI helper for the existing Food-101 model.

Production inference lives in backend/app/ml/model_service.py.
This file now delegates to that service so preprocessing stays in one place.
"""

from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.ml.model_service import predict_food  # noqa: E402


if __name__ == "__main__":
    image = Path(__file__).resolve().parent / "uploads" / "chicken.jpg"
    if len(sys.argv) > 1:
        image = Path(sys.argv[1])
    result = predict_food(image)
    print(result)
