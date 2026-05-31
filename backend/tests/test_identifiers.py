from app.text.identifiers import normalize_doi


def test_normalize_doi_strips_trailing_period() -> None:
    assert normalize_doi("10.1038/478026a.") == "10.1038/478026a"


def test_normalize_doi_strips_url_prefix() -> None:
    assert normalize_doi("https://doi.org/10.1000/xyz") == "10.1000/xyz"
