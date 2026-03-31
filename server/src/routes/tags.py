"""Tag CRUD and lifecycle endpoints."""

import logging
from datetime import datetime, timezone

from azure.cosmos.exceptions import CosmosResourceNotFoundError
from fastapi import APIRouter, HTTPException, Query, Response

from src.models import Tag, TagStatus, CreateTag, UpdateTag
from src.utils.db import get_tags_repo

logger = logging.getLogger("routes.tags")
router = APIRouter(prefix="/api/tags", tags=["tags"])


def _error(message: str, details: list[str] | None = None) -> dict:
    return {"error": message, "details": details}


@router.get("")
async def list_tags(
    status: TagStatus | None = Query(None, description="Filter by status"),
    assetId: str | None = Query(None, description="Filter by asset ID"),
    search: str | None = Query(None, description="Search name/description"),
) -> list[dict]:
    """List tags with optional filters. Excludes retired tags by default."""
    repo = get_tags_repo()

    clauses: list[str] = []
    parameters: list[dict] = []

    # Default: exclude retired unless explicitly requested
    if status is not None:
        clauses.append("c.status = @status")
        parameters.append({"name": "@status", "value": status.value})
    else:
        clauses.append("c.status != @retired")
        parameters.append({"name": "@retired", "value": TagStatus.RETIRED.value})

    if assetId is not None:
        clauses.append("c.assetId = @assetId")
        parameters.append({"name": "@assetId", "value": assetId})

    if search is not None:
        clauses.append(
            "(CONTAINS(c.name, @search, true) OR CONTAINS(c.description, @search, true))"
        )
        parameters.append({"name": "@search", "value": search})

    where = " AND ".join(clauses)
    query_str = f"SELECT * FROM c WHERE {where}" if where else "SELECT * FROM c"

    return repo.query(
        query_str,
        parameters=parameters or None,
        partition_key=assetId,
    )


@router.get("/{tag_id}")
async def get_tag(tag_id: str) -> dict:
    """Get a single tag by ID (cross-partition query)."""
    repo = get_tags_repo()
    items = repo.query(
        "SELECT * FROM c WHERE c.id = @id",
        parameters=[{"name": "@id", "value": tag_id}],
    )
    if not items:
        raise HTTPException(status_code=404, detail=_error("Tag not found"))
    return items[0]


@router.post("", status_code=201)
async def create_tag(body: CreateTag) -> dict:
    """Create a new tag. Status defaults to draft."""
    repo = get_tags_repo()
    tag = Tag(**body.model_dump())
    return repo.create(tag.model_dump(mode="json"))


@router.put("/{tag_id}")
async def update_tag(tag_id: str, body: UpdateTag) -> dict:
    """Update a tag (partial update — only provided fields are changed)."""
    repo = get_tags_repo()

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=400,
            detail=_error("No fields to update"),
        )

    # Find the tag first (cross-partition)
    items = repo.query(
        "SELECT * FROM c WHERE c.id = @id",
        parameters=[{"name": "@id", "value": tag_id}],
    )
    if not items:
        raise HTTPException(status_code=404, detail=_error("Tag not found"))

    existing = items[0]

    # Convert enum values to their string form for storage
    for key, value in updates.items():
        if hasattr(value, "value"):
            updates[key] = value.value

    return repo.update(tag_id, existing["assetId"], updates)


@router.patch("/{tag_id}/retire", status_code=204)
async def retire_tag(tag_id: str) -> Response:
    """Soft-delete: set tag status to retired."""
    repo = get_tags_repo()

    items = repo.query(
        "SELECT * FROM c WHERE c.id = @id",
        parameters=[{"name": "@id", "value": tag_id}],
    )
    if not items:
        raise HTTPException(status_code=404, detail=_error("Tag not found"))

    existing = items[0]
    repo.update(tag_id, existing["assetId"], {"status": TagStatus.RETIRED.value})
    return Response(status_code=204)
