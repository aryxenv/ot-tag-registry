"""Next-available-name endpoint — generates a unique tag name with auto-incremented ID."""

import logging
import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.utils.db import get_tags_repo

logger = logging.getLogger("routes.tag_names")
router = APIRouter(prefix="/api/tags", tags=["tag-names"])


class NextAvailableNameRequest(BaseModel):
    baseName: str


class NextAvailableNameResponse(BaseModel):
    name: str


@router.post("/next-available-name", response_model=NextAvailableNameResponse)
async def next_available_name(body: NextAvailableNameRequest) -> NextAvailableNameResponse:
    """Return the next available tag name for a given base.

    Given a base like ``LUX.L1.PMP001.Pressure``, queries existing tags
    with that prefix and returns the next available ID suffix
    (e.g. ``LUX.L1.PMP001.Pressure.1`` or ``.2`` if ``.1`` exists).
    """
    base = body.baseName.strip()
    if not base:
        raise HTTPException(status_code=400, detail={"error": "baseName must not be empty"})

    repo = get_tags_repo()
    prefix = f"{base}."

    existing = repo.query(
        "SELECT c.name FROM c WHERE STARTSWITH(c.name, @prefix)",
        parameters=[{"name": "@prefix", "value": prefix}],
    )

    # Extract numeric ID suffixes from existing names
    used_ids: set[int] = set()
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")
    for item in existing:
        m = pattern.match(item.get("name", ""))
        if m:
            used_ids.add(int(m.group(1)))

    # Find the next available ID (start from 1)
    next_id = 1
    while next_id in used_ids:
        next_id += 1

    return NextAvailableNameResponse(name=f"{base}.{next_id}")
