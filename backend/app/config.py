from __future__ import annotations

from functools import lru_cache
from typing import Self

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PLACEHOLDER_EMAIL_DOMAINS = frozenset(
    {"example.com", "example.org", "example.net", "example.invalid"}
)
_DEV_CONTACT_EMAIL = "dev@localhost.invalid"
_DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Papyrus"
    pipeline_version: str = "2.0"
    # development | production — production enforces real contact emails (no example.com).
    app_env: str = "development"

    # SQLAlchemy sync URL (postgresql+psycopg2:// in Docker).
    database_url: str = "postgresql+psycopg2://papyrus:papyrus@localhost:5432/papyrus"
    persistence_backend: str = "both"  # json | postgres | both
    redis_url: str = "redis://localhost:6379/0"

    # Comma-separated browser origins allowed by CORS (set in production).
    cors_origins: str = _DEFAULT_CORS_ORIGINS

    grobid_url: str = "http://localhost:8070"
    grobid_enabled: bool = True
    # Min share of bibliography rows with title + (DOI or year) before keeping GROBID output.
    grobid_min_bibliography_fill_ratio: float = 0.4

    crossref_mailto: str | None = None
    semantic_scholar_api_key: str | None = None
    openalex_mailto: str | None = None
    exa_api_key: str | None = None
    firecrawl_api_key: str | None = None
    apify_api_token: str | None = None
    apify_actor_arxiv: str = "datapilot/arxiv-research-paper-scraper"
    apify_actor_arxiv_secondary: str = "openclawmara/arxiv-paper-scraper"
    apify_actor_openalex: str = "parseforge/openalex-scraper"
    apify_actor_openalex_secondary: str = "shahidirfan/openalex-scraper"
    apify_actor_europe_pmc: str = "parseforge/europepmc-scraper"
    apify_actor_europe_pmc_search: str = "ryanclinton/europe-pmc-search"
    apify_actor_crossref_journals: str = "parseforge/crossref-journals-scraper"
    apify_actor_academic_mcp: str = "nexgendata/academic-research-mcp-server"
    deepseek_api_key: str | None = None
    openai_api_key: str | None = None
    openrouter_api_key: str | None = None
    huggingface_api_key: str | None = None
    nli_backend: str = "auto"  # auto | hf | ollama | local | lexical
    ollama_base_url: str | None = None
    ollama_nli_model: str = "llama3.2"

    cache_ttl_seconds: int = 60 * 60 * 24 * 30
    title_drift_ratio_threshold: float = 0.72
    title_drift_token_threshold: float = 0.65

    upload_dir: str = "./data/uploads"
    audit_data_dir: str = "./data/audits"
    max_upload_mb: int = 50

    unpaywall_email: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    enable_deepseek: bool = True
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openrouter/owl-alpha"
    openrouter_fallback_model: str = "nvidia/nemotron-3-super-120b-a12b:free"
    llm_backend: str = "deepseek"  # deepseek | openrouter
    # Prefer Celery for bulk ZIP jobs; auto-falls back to BackgroundTasks if no worker/Redis.
    use_celery_bulk: bool = True
    nli_requires_claim_approval: bool = True
    sync_relational_audits: bool = True
    use_relational_read: bool = True
    embeddings_backend: str = "openai"  # openai | openrouter | snowflake (HF inference)
    snowflake_embedding_model: str = "Snowflake/snowflake-arctic-embed-m-v1.5"

    @field_validator("app_env")
    @classmethod
    def normalize_app_env(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"development", "production"}:
            raise ValueError("APP_ENV must be 'development' or 'production'")
        return normalized

    @field_validator("persistence_backend")
    @classmethod
    def normalize_persistence_backend(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"json", "postgres", "both"}:
            raise ValueError("PERSISTENCE_BACKEND must be json, postgres, or both")
        return normalized

    @staticmethod
    def _is_placeholder_email(email: str) -> bool:
        domain = email.rsplit("@", 1)[-1].strip().lower()
        return domain in _PLACEHOLDER_EMAIL_DOMAINS

    @model_validator(mode="after")
    def apply_contact_defaults(self) -> Self:
        for name in ("crossref_mailto", "openalex_mailto", "unpaywall_email"):
            value = getattr(self, name)
            if not value:
                if self.app_env == "production":
                    raise ValueError(
                        f"{name} is required when APP_ENV=production "
                        "(set CROSSREF_MAILTO, OPENALEX_MAILTO, UNPAYWALL_EMAIL)"
                    )
                object.__setattr__(self, name, _DEV_CONTACT_EMAIL)
                continue
            if self.app_env == "production" and self._is_placeholder_email(value):
                raise ValueError(
                    f"{name} must be a real contact address in production (not example.com)"
                )
        return self

    def cors_origins_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        if origins:
            return origins
        return [part.strip() for part in _DEFAULT_CORS_ORIGINS.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
