from __future__ import annotations

import logging

from app.domain.enums import NliVerdict

logger = logging.getLogger(__name__)

_cross_encoder = None


def _get_cross_encoder():
    global _cross_encoder
    if _cross_encoder is not None:
        return _cross_encoder
    try:
        from sentence_transformers import CrossEncoder
    except ImportError:
        logger.info("sentence-transformers not installed; local NLI unavailable")
        return None
    _cross_encoder = CrossEncoder("cross-encoder/nli-deberta-v3-base")
    return _cross_encoder


def classify_local(claim: str, evidence: str) -> NliVerdict | None:
    model = _get_cross_encoder()
    if model is None:
        return None
    import numpy as np

    raw = model.predict([[evidence[:2000], claim[:512]]])
    arr = np.asarray(raw).reshape(-1)
    if arr.size >= 3:
        labels = [NliVerdict.CONTRADICTS, NliVerdict.NEUTRAL, NliVerdict.ENTAILS]
        return labels[int(arr.argmax())]
    label = str(raw).upper()
    if "CONTRAD" in label:
        return NliVerdict.CONTRADICTS
    if "ENTAIL" in label:
        return NliVerdict.ENTAILS
    return NliVerdict.NEUTRAL
