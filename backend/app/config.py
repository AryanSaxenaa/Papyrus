from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Papyrus"
    pipeline_version: str = "2.0"
    debug: bool = False

    # SQLAlchemy sync URL (postgresql+psycopg2:// in Docker).
    database_url: str = "postgresql+psycopg2://papyrus:papyrus@localhost:5432/papyrus"
    persistence_backend: str = "json"  # json | postgres | both
    redis_url: str = "redis://localhost:6379/0"

    grobid_url: str = "http://localhost:8070"
    grobid_enabled: bool = True

    crossref_mailto: str = "contact@example.com"
    semantic_scholar_api_key: str | None = None
    openalex_mailto: str = "contact@example.com"
    exa_api_key: str | None = None
    firecrawl_api_key: str | None = None
    apify_api_token: str | None = None
    apify_actor_arxiv: str = "datapilot/arxiv-research-paper-scraper"
    apify_actor_arxiv_secondary: str = "openclawmara/arxiv-paper-scraper"
    apify_actor_openalex: str = "parseforge/openalex-scraper"
    apify_actor_openalex_secondary: str = "shahidirfan/openalex-scraper"
    apify_actor_europe_pmc: str = "parseforge/europepmc-scraper"
    apify_actor_crossref_journals: str = "parseforge/crossref-journals-scraper"
    apify_actor_academic_mcp: str = "nexgendata/academic-research-mcp-server"
    deepseek_api_key: str | None = None
    openai_api_key: str | None = None
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

    unpaywall_email: str = "contact@example.com"
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    enable_deepseek: bool = True
    use_celery_bulk: bool = False
    nli_requires_claim_approval: bool = True
    sync_relational_audits: bool = True
    use_relational_read: bool = True
    embeddings_backend: str = "openai"  # openai | snowflake (HF inference)
    snowflake_embedding_model: str = "Snowflake/snowflake-arctic-embed-m-v1.5"


@lru_cache
def get_settings() -> Settings:
    return Settings()
