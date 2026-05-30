from app.pipeline.verdicts import compare_titles


def test_compare_titles_identical() -> None:
    ratio, _ = compare_titles("Attention Is All You Need", "Attention Is All You Need")
    assert ratio > 0.95


def test_compare_titles_different() -> None:
    ratio, _ = compare_titles(
        "Long-term outcomes in post-COVID neurological syndromes",
        "Association of SARS-CoV-2 Infection With Physical Activity",
    )
    assert ratio < 0.5
