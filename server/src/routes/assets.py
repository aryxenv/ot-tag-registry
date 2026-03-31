"""Asset list and create endpoints."""

from fastapi import APIRouter

from src.models import Asset, CreateAsset
from src.utils.db import get_assets_repo

router = APIRouter(prefix="/api/assets", tags=["assets"])


@router.get("")
async def list_assets() -> list[dict]:
    """Return all assets."""
    repo = get_assets_repo()
    return repo.get_all()


@router.post("", status_code=201)
async def create_asset(body: CreateAsset) -> dict:
    """Create a new asset."""
    repo = get_assets_repo()
    asset = Asset(**body.model_dump())
    return repo.create(asset.model_dump(mode="json"))
