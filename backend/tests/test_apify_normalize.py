from app.services.apify_client import _normalize_academic_item, _normalize_openalex_item


def test_normalize_academic_item_maps_common_fields() -> None:
    row = {
        "title": "Scaling Laws",
        "abstract": "We study emergent behavior.",
        "authors": ["A. Author"],
        "year": 2022,
        "doi": "https://doi.org/10.1234/example",
        "pdfUrl": "https://example.org/paper.pdf",
    }
    result = _normalize_academic_item(row)
    assert result["title"] == "Scaling Laws"
    assert result["doi"] == "10.1234/example"
    assert result["via"] == "academic_mcp"


def test_normalize_openalex_item_coerces_dict_authors() -> None:
    row = {
        "title": "Attention Is All You Need",
        "authors": [{"display_name": "Ashish Vaswani"}, {"display_name": "Noam Shazeer"}],
        "year": 2017,
    }
    result = _normalize_openalex_item(row)
    assert result["authors"] == ["Ashish Vaswani", "Noam Shazeer"]
