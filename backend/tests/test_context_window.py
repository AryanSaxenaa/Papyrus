from app.text.context_window import three_sentence_window


def test_three_sentence_window_around_marker() -> None:
    paragraph = (
        "First sentence about methods. "
        "Second sentence cites prior work [12] with a specific claim. "
        "Third sentence continues the argument. "
        "Fourth sentence is extra context."
    )
    window = three_sentence_window(paragraph, "[12]")
    assert "[12]" in window
    assert "Second sentence" in window
    assert "Third sentence" in window
    assert "Fourth sentence" not in window
