from enum import StrEnum


class CitationIntent(StrEnum):
    EVIDENTIARY = "evidentiary"
    METHODOLOGICAL = "methodological"
    CONTRASTIVE = "contrastive"
    BACKGROUND = "background"


class EvidenceTier(StrEnum):
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"
    TIER_4 = "tier_4"


class HallucinationType(StrEnum):
    DOI_404 = "type_1_doi_404"
    DOI_REDIRECT = "type_2_doi_redirect"
    DATE_IMPOSSIBLE = "type_5_date_impossible"
    TITLE_DRIFT = "type_6_title_drift"
    CLAIM_CONTRADICTION = "type_7_claim_contradiction"
    RETRACTION = "retraction"
    VERSION_MISMATCH = "version_mismatch"
    NONE = "none"


class NliVerdict(StrEnum):
    ENTAILS = "entails"
    CONTRADICTS = "contradicts"
    NEUTRAL = "neutral"
    SKIPPED = "skipped"


class ConfidenceLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskLevel(StrEnum):
    LOW = "low"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


class ResolutionSource(StrEnum):
    CROSSREF = "crossref"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    OPENALEX = "openalex"
    UNPAYWALL = "unpaywall"
    ARXIV = "arxiv"
    EXA = "exa"
    DEEPSEEK = "deepseek"
    GROBID = "grobid"
    PYMUPDF = "pymupdf"
