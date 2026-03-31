"""L1 (Range) and L2 (State Profile) rule CRUD endpoints."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Response

from src.models import (
    L1Rule,
    L2Rule,
    CreateL1Rule,
    UpdateL1Rule,
    CreateL2Rule,
    UpdateL2Rule,
)
from src.utils.db import get_tags_repo, get_l1_rules_repo, get_l2_rules_repo

logger = logging.getLogger("routes.rules")
router = APIRouter(prefix="/api/tags/{tag_id}/rules", tags=["rules"])


def _error(message: str, details: list[str] | None = None) -> dict:
    return {"error": message, "details": details}


def _require_tag(tag_id: str) -> dict:
    """Verify that the referenced tag exists. Raises 404 if not."""
    repo = get_tags_repo()
    items = repo.query(
        "SELECT * FROM c WHERE c.id = @id",
        parameters=[{"name": "@id", "value": tag_id}],
    )
    if not items:
        raise HTTPException(status_code=404, detail=_error("Tag not found"))
    return items[0]


def _get_rule_for_tag(repo, tag_id: str) -> dict | None:
    """Return the single rule for a tag, or None."""
    items = repo.get_all(partition_key=tag_id)
    return items[0] if items else None


# ---------------------------------------------------------------------------
# L1 Rule endpoints
# ---------------------------------------------------------------------------


@router.get("/l1")
async def get_l1_rule(tag_id: str) -> dict:
    """Get the L1 (range) rule for a tag."""
    _require_tag(tag_id)
    rule = _get_rule_for_tag(get_l1_rules_repo(), tag_id)
    if rule is None:
        raise HTTPException(status_code=404, detail=_error("L1 rule not found"))
    return rule


@router.post("/l1", status_code=201)
async def create_l1_rule(tag_id: str, body: CreateL1Rule) -> dict:
    """Create or replace the L1 rule for a tag (upsert semantics)."""
    _require_tag(tag_id)
    repo = get_l1_rules_repo()

    existing = _get_rule_for_tag(repo, tag_id)
    if existing is not None:
        # Replace: keep the same id, refresh timestamps
        rule = L1Rule(id=existing["id"], tagId=tag_id, **body.model_dump())
    else:
        rule = L1Rule(tagId=tag_id, **body.model_dump())

    return repo.create(rule.model_dump(mode="json"))


@router.put("/l1")
async def update_l1_rule(tag_id: str, body: UpdateL1Rule) -> dict:
    """Partial-update the L1 rule for a tag."""
    _require_tag(tag_id)
    repo = get_l1_rules_repo()

    existing = _get_rule_for_tag(repo, tag_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=_error("L1 rule not found"))

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail=_error("No fields to update"))

    # Convert enum values to their string form for storage
    for key, value in updates.items():
        if hasattr(value, "value"):
            updates[key] = value.value

    # Validate that after merge at least one threshold field remains
    merged = {**existing, **updates}
    if merged.get("min") is None and merged.get("max") is None and merged.get("spikeThreshold") is None:
        raise HTTPException(
            status_code=400,
            detail=_error(
                "At least one of 'min', 'max', or 'spikeThreshold' must be set"
            ),
        )

    return repo.update(existing["id"], tag_id, updates)


@router.delete("/l1", status_code=204)
async def delete_l1_rule(tag_id: str) -> Response:
    """Permanently remove the L1 rule for a tag."""
    _require_tag(tag_id)
    repo = get_l1_rules_repo()

    existing = _get_rule_for_tag(repo, tag_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=_error("L1 rule not found"))

    repo.hard_delete(existing["id"], tag_id)
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# L2 Rule endpoints
# ---------------------------------------------------------------------------


@router.get("/l2")
async def get_l2_rule(tag_id: str) -> dict:
    """Get the L2 (state profile) rule for a tag."""
    _require_tag(tag_id)
    rule = _get_rule_for_tag(get_l2_rules_repo(), tag_id)
    if rule is None:
        raise HTTPException(status_code=404, detail=_error("L2 rule not found"))
    return rule


@router.post("/l2", status_code=201)
async def create_l2_rule(tag_id: str, body: CreateL2Rule) -> dict:
    """Create or replace the L2 rule for a tag (upsert semantics)."""
    _require_tag(tag_id)
    repo = get_l2_rules_repo()

    existing = _get_rule_for_tag(repo, tag_id)
    if existing is not None:
        rule = L2Rule(id=existing["id"], tagId=tag_id, **body.model_dump())
    else:
        rule = L2Rule(tagId=tag_id, **body.model_dump())

    return repo.create(rule.model_dump(mode="json"))


@router.put("/l2")
async def update_l2_rule(tag_id: str, body: UpdateL2Rule) -> dict:
    """Partial-update the L2 rule for a tag."""
    _require_tag(tag_id)
    repo = get_l2_rules_repo()

    existing = _get_rule_for_tag(repo, tag_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=_error("L2 rule not found"))

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail=_error("No fields to update"))

    # Validate stateMapping is non-empty if provided
    if "stateMapping" in updates and len(updates["stateMapping"]) == 0:
        raise HTTPException(
            status_code=400,
            detail=_error("'stateMapping' must have at least one entry"),
        )

    return repo.update(existing["id"], tag_id, updates)


@router.delete("/l2", status_code=204)
async def delete_l2_rule(tag_id: str) -> Response:
    """Permanently remove the L2 rule for a tag."""
    _require_tag(tag_id)
    repo = get_l2_rules_repo()

    existing = _get_rule_for_tag(repo, tag_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=_error("L2 rule not found"))

    repo.hard_delete(existing["id"], tag_id)
    return Response(status_code=204)
