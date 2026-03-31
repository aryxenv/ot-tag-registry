"""Pydantic models for the suggest-name endpoint."""

from pydantic import BaseModel


class SuggestNameRequest(BaseModel):
    """Request body for ``POST /api/tags/suggest-name``."""

    site: str
    line: str
    description: str
    equipment: str | None = None
    unit: str | None = None
    datatype: str | None = None


class SuggestionMatch(BaseModel):
    """A single search hit with its relevance score."""

    tagName: str
    description: str
    score: float
    site: str
    line: str
    equipment: str
    unit: str
    datatype: str


class SuggestionResult(BaseModel):
    """Ranked suggestions returned by the suggest-name endpoint."""

    suggestedName: str
    alternatives: list[str]
    evidence: str
    matches: list[SuggestionMatch]
