import re

from app.domain.enums import CitationIntent
from app.domain.models import CitationRecord


CONTRASTIVE = re.compile(
    r"\b(contrary to|unlike|in contrast|we challenge|we dispute|inconsistent with)\b",
    re.I,
)
METHODOLOGICAL = re.compile(
    r"\b(we used|following the (method|approach|procedure)|as described in|based on the method)\b",
    re.I,
)
EVIDENTIARY = re.compile(
    r"\b(found|showed|demonstrated|reported|observed|revealed|established|indicates? that)\b",
    re.I,
)


def classify_intent(record: CitationRecord) -> CitationIntent:
    context = " ".join(marker.context_window for marker in record.inline_markers)
    if not context:
        return CitationIntent.BACKGROUND
    if CONTRASTIVE.search(context):
        return CitationIntent.CONTRASTIVE
    if METHODOLOGICAL.search(context):
        return CitationIntent.METHODOLOGICAL
    if EVIDENTIARY.search(context):
        return CitationIntent.EVIDENTIARY
    return CitationIntent.BACKGROUND


def apply_negation_override(record: CitationRecord) -> CitationIntent:
    context = " ".join(marker.context_window for marker in record.inline_markers)
    if CONTRASTIVE.search(context):
        return CitationIntent.CONTRASTIVE
    return record.intent
