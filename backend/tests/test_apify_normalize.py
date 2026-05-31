"""Apify client is limited to arXiv actors; normalization helpers removed with OpenAlex/Europe PMC Apify scrapers."""


def test_apify_fallback_is_arxiv_only() -> None:
    from app.services.apify_client import apify_fallback_resolve
    import asyncio

    assert asyncio.run(apify_fallback_resolve("Some Title", ["Author"], None)) is None
