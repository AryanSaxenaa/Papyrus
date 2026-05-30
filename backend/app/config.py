from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Papyrus"
    pipeline_version: str = "2.0"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://papyrus:papyrus@localhost:5432/papyrus"
    redis_url: str = "redis://localhost:6379/0"

    grobid_url: str = "http://localhost:8070"
    grobid_enabled: bool = True

    crossref_mailto: str = "contact@example.com"
    semantic_scholar_api_key: str | None = None
    openalex_mailto: str = "contact@example.com"
    exa_api_key: str | None = None
    deepseek_api_key: str | None = None
    openai_api_key: str | None = None
    huggingface_api_key: str | None = None

    cache_ttl_seconds: int = 60 * 60 * 24 * 30
    title_drift_ratio_threshold: float = 0.72
    title_drift_token_threshold: float = 0.65

    upload_dir: str = "./data/uploads"
    audit_data_dir: str = "./data/audits"
    max_upload_mb: int = 50

    unpaywall_email: str = "contact@example.com"
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    enable_deepseek: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
