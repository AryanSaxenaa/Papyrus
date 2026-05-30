from app.pipeline.journal_checks import is_resolved_metadata_mismatch, is_year_impossible


def test_is_year_impossible_before_journal_launch() -> None:
    assert is_year_impossible(2015, {"first_issue": 2019}) is True
    assert is_year_impossible(2020, {"first_issue": 2019}) is False


def test_resolved_metadata_mismatch_year() -> None:
    crossref = {"year": 2021, "volume": "12"}
    assert is_resolved_metadata_mismatch(2018, "12", crossref) is True


def test_resolved_metadata_mismatch_volume() -> None:
    crossref = {"year": 2020, "volume": "8"}
    assert is_resolved_metadata_mismatch(2020, "12", crossref) is True
