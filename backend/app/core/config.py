from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "GrowthOS"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://growthos:growthos@localhost:5432/growthos"
    jwt_secret: str = "change-this-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    frontend_url: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3000"
    storage_path: str = "./storage"
    upload_dir: str | None = None
    max_upload_size: int = 5 * 1024 * 1024
    allowed_upload_extensions: str = ".png,.jpg,.jpeg,.pdf,.doc,.docx,.ppt,.pptx,.txt"
    ai_enabled: bool = False
    ai_provider: str = "openai-compatible"
    ai_api_key: str | None = None
    ai_base_url: str = "https://api.openai.com/v1"
    ai_model: str = ""
    ai_timeout_seconds: float = 20
    ai_max_retries: int = 2

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def validate_production(self) -> "Settings":
        if self.upload_dir:
            self.storage_path = self.upload_dir
        if self.app_env.lower() == "production":
            if self.jwt_secret == "change-this-secret" or len(self.jwt_secret) < 32:
                raise ValueError("Production requires a non-default JWT_SECRET of at least 32 characters")
            if "sqlite" in self.database_url.lower() or "test" in self.database_url.lower():
                raise ValueError("Production cannot use SQLite or a test database")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def storage_root(self) -> Path:
        return Path(self.storage_path).expanduser().resolve()


def get_settings() -> Settings:
    return Settings()
