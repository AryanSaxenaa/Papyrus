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
