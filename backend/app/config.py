from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_database: str = "NUTRITION_DATABASE"
    mysql_user: str = "root"
    mysql_password: str = ""

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    model_path: str = ""
    class_names_path: str = ""
    upload_dir: str = "uploads"

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    serve_frontend: bool = True
    low_confidence_threshold: float = 50.0
    max_upload_mb: int = 8
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    ai_provider: str = "auto"
    ai_timeout_seconds: float = 30.0
    ai_max_history_turns: int = 12
    chat_rate_limit_per_minute: int = 20

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def resolved_model_path(self) -> Path:
        if self.model_path:
            path = Path(self.model_path)
            if not path.is_absolute():
                path = (BACKEND_DIR / path).resolve()
            return path
        matches = list(PROJECT_ROOT.glob("*.keras"))
        if matches:
            return matches[0]
        return BACKEND_DIR / "app" / "ml" / "food101_model.keras"

    @property
    def resolved_class_names_path(self) -> Path:
        if self.class_names_path:
            path = Path(self.class_names_path)
            if not path.is_absolute():
                path = (BACKEND_DIR / path).resolve()
            return path
        local = BACKEND_DIR / "app" / "ml" / "class_names.json"
        if local.exists():
            return local
        return PROJECT_ROOT / "class_names.json"

    @property
    def resolved_upload_dir(self) -> Path:
        path = Path(self.upload_dir)
        if not path.is_absolute():
            path = BACKEND_DIR / path
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
