import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.config import get_settings  # noqa: E402


@pytest.fixture(scope="session")
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def burrito_image(project_root: Path) -> Path:
    path = project_root / "uploads" / "Burrito_1200x800.jpg"
    if not path.exists():
        pytest.skip("Sample burrito image is not available")
    return path


@pytest.fixture(scope="session")
def settings():
    get_settings.cache_clear()
    return get_settings()
