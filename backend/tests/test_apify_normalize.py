from app.services.apify_client import _normalize_academic_item


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
