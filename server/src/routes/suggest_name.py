"""Suggest-name route — returns AI-powered tag name suggestions."""

import logging

from fastapi import APIRouter, HTTPException

from src.models.suggest_name import SuggestNameRequest, SuggestionResult
from src.utils.search import SearchServiceError, suggest_tag_name

logger = logging.getLogger("ot_tag_registry.routes.suggest_name")

router = APIRouter(prefix="/api/tags", tags=["suggest-name"])


@router.post("/suggest-name", response_model=SuggestionResult)
async def suggest_name(body: SuggestNameRequest) -> SuggestionResult:
    """Return ranked tag-name suggestions via hybrid vector search."""
    try:
        result = await suggest_tag_name(
            site=body.site,
            line=body.line,
            description=body.description,
            equipment=body.equipment,
            unit=body.unit,
            datatype=body.datatype,
        )
    except SearchServiceError as exc:
        logger.error("Search service error: %s", exc)
        raise HTTPException(status_code=502, detail={"error": str(exc)}) from exc
    except ValueError as exc:
        logger.error("Configuration error: %s", exc)
        raise HTTPException(status_code=400, detail={"error": str(exc)}) from exc

    return result
