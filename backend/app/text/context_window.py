from __future__ import annotations

from app.text.sentences import split_sentences


def three_sentence_window(paragraph: str, anchor: str | None = None) -> str:
    """Return up to three sentences around the anchor (or the full short paragraph)."""
    text = " ".join(paragraph.split())
    if not text:
        return ""
    sentences = split_sentences(text)
    if not sentences:
        return text[:800]
    if len(sentences) <= 3:
        return " ".join(sentences)[:1200]
    if anchor:
        anchor_lower = anchor.lower()
        for idx, sentence in enumerate(sentences):
            if anchor_lower in sentence.lower():
                start = max(0, idx - 1)
                end = min(len(sentences), idx + 2)
                return " ".join(sentences[start:end])[:1200]
    return " ".join(sentences[:3])[:1200]
