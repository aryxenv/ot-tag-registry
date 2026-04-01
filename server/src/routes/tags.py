"""Tag CRUD and lifecycle endpoints."""

import logging
from datetime import datetime, timezone
from typing import Any

from azure.cosmos.exceptions import CosmosResourceNotFoundError
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel

from src.models import Tag, TagStatus, ApprovalStatus, CreateTag, UpdateTag
from src.utils.db import get_tags_repo
from src.validators import validate_tag_name

logger = logging.getLogger("routes.tags")
router = APIRouter(prefix="/api/tags", tags=["tags"])


def _error(message: str, details: list[str] | None = None) -> dict:
    return {"error": message, "details": details}


def _run_name_validation(name: str) -> None:
    """Validate a tag name and raise HTTPException 400 if invalid."""
    result = validate_tag_name(name)
    if not result.valid:
        details = [
            f"[{e.segment}] {e.message} (got '{e.received}')"
            for e in result.errors
        ]
        raise HTTPException(
            status_code=400,
            detail=_error("Invalid tag name", details),
        )


def _check_name_unique(name: str, exclude_id: str | None = None) -> None:
    """Raise HTTPException 400 if a tag with this name already exists."""
    repo = get_tags_repo()
    existing = repo.query(
        "SELECT c.id FROM c WHERE c.name = @name",
        parameters=[{"name": "@name", "value": name}],
    )
    for item in existing:
        if item["id"] != exclude_id:
            raise HTTPException(
                status_code=400,
                detail=_error("A tag with this name already exists"),
            )


class ValidateNameRequest(BaseModel):
    name: str


@router.post("/validate-name")
async def validate_name(body: ValidateNameRequest) -> dict:
    """Validate a tag name against the naming schema without creating a tag."""
    result = validate_tag_name(body.name)
    return {
        "valid": result.valid,
        "errors": [
            {
                "segment": e.segment,
                "message": e.message,
                "received": e.received,
                "expected": e.expected,
            }
            for e in result.errors
        ],
    }


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
    _run_name_validation(body.name)
    _check_name_unique(body.name)
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

    # Validate name if it is being changed
    if "name" in updates:
        _run_name_validation(updates["name"])
        _check_name_unique(updates["name"], exclude_id=tag_id)

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

    new_asset_id = updates.get("assetId")
    old_asset_id = existing["assetId"]

    # Partition key change: delete old doc and create new one
    if new_asset_id and new_asset_id != old_asset_id:
        existing.update(updates)
        existing["updatedAt"] = datetime.now(timezone.utc).isoformat()
        repo.hard_delete(tag_id, old_asset_id)
        return repo.create(existing)

    return repo.update(tag_id, old_asset_id, updates)


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


class RejectRequest(BaseModel):
    """Request body for POST /api/tags/{tag_id}/reject."""
    rejectionReason: str | None = None


@router.post("/{tag_id}/request-approval")
async def request_approval(tag_id: str) -> dict:
    """Request governance approval for a draft tag."""
    repo = get_tags_repo()
    items = repo.query(
        "SELECT * FROM c WHERE c.id = @id",
        parameters=[{"name": "@id", "value": tag_id}],
    )
    if not items:
        raise HTTPException(status_code=404, detail=_error("Tag not found"))

    existing = items[0]

    # Guard: tag must be draft AND approvalStatus must be none or rejected
    if existing.get("status") != TagStatus.DRAFT.value:
        raise HTTPException(
            status_code=400,
            detail=_error("Only draft tags can request approval"),
        )

    current_approval = existing.get("approvalStatus", "none")
    if current_approval not in (ApprovalStatus.NONE.value, ApprovalStatus.REJECTED.value):
        raise HTTPException(
            status_code=400,
            detail=_error(
                "Tag approval is already pending or approved",
            ),
        )

    updates = {
        "approvalStatus": ApprovalStatus.PENDING.value,
        "rejectionReason": None,
    }
    return repo.update(tag_id, existing["assetId"], updates)


@router.post("/{tag_id}/approve")
async def approve_tag(tag_id: str) -> dict:
    """Approve a pending tag — sets status to active."""
    repo = get_tags_repo()
    items = repo.query(
        "SELECT * FROM c WHERE c.id = @id",
        parameters=[{"name": "@id", "value": tag_id}],
    )
    if not items:
        raise HTTPException(status_code=404, detail=_error("Tag not found"))

    existing = items[0]

    current_approval = existing.get("approvalStatus", "none")
    if current_approval != ApprovalStatus.PENDING.value:
        raise HTTPException(
            status_code=400,
            detail=_error("Only pending tags can be approved"),
        )

    updates = {
        "approvalStatus": ApprovalStatus.APPROVED.value,
        "status": TagStatus.ACTIVE.value,
    }
    return repo.update(tag_id, existing["assetId"], updates)


@router.post("/{tag_id}/reject")
async def reject_tag(tag_id: str, body: RejectRequest | None = None) -> dict:
    """Reject a pending tag with an optional reason."""
    repo = get_tags_repo()
    items = repo.query(
        "SELECT * FROM c WHERE c.id = @id",
        parameters=[{"name": "@id", "value": tag_id}],
    )
    if not items:
        raise HTTPException(status_code=404, detail=_error("Tag not found"))

    existing = items[0]

    current_approval = existing.get("approvalStatus", "none")
    if current_approval != ApprovalStatus.PENDING.value:
        raise HTTPException(
            status_code=400,
            detail=_error("Only pending tags can be rejected"),
        )

    updates: dict[str, Any] = {
        "approvalStatus": ApprovalStatus.REJECTED.value,
        "rejectionReason": body.rejectionReason if body else None,
    }
    return repo.update(tag_id, existing["assetId"], updates)
