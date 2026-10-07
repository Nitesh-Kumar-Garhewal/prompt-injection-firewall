from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ET AI Hackathon - Prompt Injection Firewall"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./prompt_firewall.db"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4.1-mini"
    llm_timeout_seconds: int = 20
    max_input_chars: int = 200_000
    risk_block_threshold: int = 80
    risk_escalate_threshold: int = 60
    risk_sanitize_threshold: int = 35
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
