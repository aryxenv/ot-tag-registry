"""Source list and create endpoints."""

from fastapi import APIRouter

from src.models import Source, CreateSource
from src.utils.db import get_sources_repo

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("")
async def list_sources() -> list[dict]:
    """Return all sources."""
    repo = get_sources_repo()
    return repo.get_all()


@router.post("", status_code=201)
async def create_source(body: CreateSource) -> dict:
    """Create a new source."""
    repo = get_sources_repo()
    source = Source(**body.model_dump())
    return repo.create(source.model_dump(mode="json"))
