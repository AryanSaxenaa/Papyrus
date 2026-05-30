from app.text.identifiers import author_title_query, normalize_doi


def test_normalize_doi_strips_url_prefixes() -> None:
    assert normalize_doi("  https://doi.org/10.1234/x  ") == "10.1234/x"
    assert normalize_doi("http://doi.org/10.1234/y") == "10.1234/y"


def test_author_title_query_uses_first_author() -> None:
    assert author_title_query("Scaling Laws", ["A. Author"]) == "A. Author Scaling Laws"
    assert author_title_query("Scaling Laws", None) == "Scaling Laws"
    assert author_title_query("Scaling Laws", []) == "Scaling Laws"
