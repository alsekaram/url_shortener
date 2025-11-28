"""Configuration settings from environment variables."""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    database_path: str = "/app/data/links.db"
    base_url: str = "http://localhost:8000"

    # Telegram
    telegram_bot_token: str
    telegram_chat_id: str

    # Reports Schedule
    daily_report_time: str = "09:00"
    weekly_report_day: str = "monday"
    weekly_report_time: str = "09:00"
    timezone: str = "Europe/Moscow"

    # Logging
    log_level: str = "INFO"

    # Yandex Metrica
    yandex_metrica_counter_id: Optional[str] = None
    yandex_metrica_token: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()



