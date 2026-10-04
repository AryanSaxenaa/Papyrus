import pytest

from app.config import Settings, get_settings


def test_cors_origins_list_parses_comma_separated() -> None:
    settings = Settings(cors_origins="https://app.example.com, https://admin.example.com")
    assert settings.cors_origins_list() == [
        "https://app.example.com",
        "https://admin.example.com",
    ]


def test_development_fills_contact_defaults() -> None:
    settings = Settings(app_env="development")
    assert settings.crossref_mailto == "dev@localhost.invalid"
    assert settings.openalex_mailto == "dev@localhost.invalid"
    assert settings.unpaywall_email == "dev@localhost.invalid"


def test_production_rejects_placeholder_email() -> None:
    with pytest.raises(ValueError, match="example.com"):
        Settings(
            app_env="production",
            crossref_mailto="team@example.com",
            openalex_mailto="team@yourdomain.com",
            unpaywall_email="team@yourdomain.com",
        )


def test_production_requires_contact_emails() -> None:
    with pytest.raises(ValueError, match="crossref_mailto"):
        Settings(app_env="production", crossref_mailto=None)


def test_get_settings_uses_lru_cache() -> None:
    get_settings.cache_clear()
    first = get_settings()
    second = get_settings()
    assert first is second
    get_settings.cache_clear()


def _production_kwargs(**overrides: object) -> dict:
    base = {
        "app_env": "production",
        "persistence_backend": "postgres",
        "file_storage_backend": "gcs",
        "gcs_bucket": "papyrus-prod",
        "llm_backend": "deepseek",
        "deepseek_api_key": "sk-test",
        "nli_backend": "hf",
        "huggingface_api_key": "hf_test",
        "serpapi_api_key": "serpapi_test_key",
        "crossref_mailto": "ops@yourdomain.com",
        "openalex_mailto": "ops@yourdomain.com",
        "unpaywall_email": "ops@yourdomain.com",
    }
    base.update(overrides)
    return base


def test_production_requires_gcs_bucket() -> None:
    with pytest.raises(ValueError, match="GCS_BUCKET"):
        Settings(**_production_kwargs(gcs_bucket=None))


def test_production_rejects_json_only_persistence() -> None:
    with pytest.raises(ValueError, match="PERSISTENCE_BACKEND"):
        Settings(**_production_kwargs(persistence_backend="json"))


def test_production_deepseek_requires_api_key() -> None:
    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
        Settings(**_production_kwargs(deepseek_api_key=None))


def test_audit_queue_name_defaults_by_app_env() -> None:
    assert Settings(app_env="development").audit_queue_name() == "audits-development"
    assert Settings(**_production_kwargs()).audit_queue_name() == "audits-production"


def test_audit_queue_name_override() -> None:
    settings = Settings(**_production_kwargs(celery_audit_queue="audits-staging"))
    assert settings.audit_queue_name() == "audits-staging"
