"""Auto-fill route — returns AI-powered tag field suggestions."""

import logging

from fastapi import APIRouter, HTTPException

from src.models.auto_fill import AutoFillRequest, AutoFillResult
from src.utils.search import SearchServiceError, auto_fill_tag

logger = logging.getLogger("ot_tag_registry.routes.auto_fill")

router = APIRouter(prefix="/api/tags", tags=["auto-fill"])


@router.post("/auto-fill", response_model=AutoFillResult)
async def auto_fill(body: AutoFillRequest) -> AutoFillResult:
    """Return AI-extracted tag fields via hybrid vector search + LLM."""
    try:
        result = await auto_fill_tag(
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
