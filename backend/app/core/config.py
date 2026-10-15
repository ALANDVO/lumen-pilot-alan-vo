from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "lumen-pilot"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, validation_alias="DEBUG")
    database_url: str = Field(default="sqlite+aiosqlite:///./lumen_pilot.db", validation_alias="DATABASE_URL")
    cors_origins: list[str] = Field(default=["http://localhost:5173", "http://127.0.0.1:5173"], validation_alias="CORS_ORIGINS")

    # LLM settings (opt-in)
    llm_api_key: str | None = Field(default=None, validation_alias="LLM_API_KEY")
    llm_provider: str = Field(default="openai-compatible", validation_alias="LLM_PROVIDER")
    llm_model: str = Field(default="gpt-4o-mini", validation_alias="LLM_MODEL")
    llm_base_url: str | None = Field(default=None, validation_alias="LLM_BASE_URL")
    llm_timeout: float = Field(default=30.0, validation_alias="LLM_TIMEOUT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()