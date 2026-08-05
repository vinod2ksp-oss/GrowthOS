from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "GrowthOS"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://growthos:growthos@localhost:5432/growthos"
    jwt_secret: str = "change-this-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    upload_dir: str = "./storage"
    max_upload_size: int = 5 * 1024 * 1024
    allowed_upload_extensions: str = ".png,.jpg,.jpeg,.pdf,.doc,.docx,.ppt,.pptx,.txt"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


def get_settings() -> Settings:
    return Settings()
