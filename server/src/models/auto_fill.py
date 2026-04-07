"""Pydantic models for the auto-fill endpoint."""

from pydantic import BaseModel


class AutoFillRequest(BaseModel):
    """Request body for ``POST /api/tags/auto-fill``."""

    query: str


class TranslateRequest(BaseModel):
    """Request body for ``POST /api/tags/translate``."""

    text: str


class TranslateResponse(BaseModel):
    """Response from ``POST /api/tags/translate``."""

    text: str
    sourceLanguage: str
    wasTranslated: bool


class AutoFillMatch(BaseModel):
    """A single search hit from the golden-tags index."""

    tagName: str
    description: str
    score: float
    site: str
    line: str
    equipment: str
    unit: str
    datatype: str


class AutoFillResult(BaseModel):
    """AI-extracted form fields + supporting search evidence."""

    # AI-extracted fields (None = couldn't determine)
    site: str | None = None
    line: str | None = None
    equipment: str | None = None
    unit: str | None = None
    datatype: str | None = None
    name: str | None = None
    description: str | None = None
    criticality: str | None = None

    # Evidence from vector search
    confidence: float = 0.0
    matches: list[AutoFillMatch]
