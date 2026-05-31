from unittest.mock import AsyncMock, patch

import pytest

from app.config import get_settings


@pytest.fixture
def openalex_settings(monkeypatch):
    monkeypatch.setenv("OPENALEX_MAILTO", "test@example.com")
    monkeypatch.setenv("OPENALEX_API_KEY", "test-key-123")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_openalex_params_include_api_key(openalex_settings) -> None:
    from app.services.openalex import OpenAlexClient

    params = OpenAlexClient()._params()
    assert params["mailto"] == "test@example.com"
    assert params["api_key"] == "test-key-123"


def test_lookup_doi_strips_trailing_period(openalex_settings) -> None:
    import asyncio

    from app.services.openalex import OpenAlexClient

    client = OpenAlexClient()

    async def run() -> None:
        with (
            patch(
                "app.services.openalex.rate_limit_service.allow",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch.object(
                client,
                "_lookup_doi_native",
                new_callable=AsyncMock,
                return_value=({"title": "Paper"}, False),
            ) as lookup,
        ):
            result = await client.lookup_doi("10.1038/478026a.")
            assert result == {"title": "Paper"}
            lookup.assert_awaited_once_with("10.1038/478026a")

    asyncio.run(run())
