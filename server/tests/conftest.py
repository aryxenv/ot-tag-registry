"""Shared test fixtures — mock Cosmos repository and FastAPI test client."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

# Ensure the server root is on sys.path so `import src.*` works
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient


class FakeRepository:
    """In-memory stand-in for CosmosRepository."""

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    def create(self, item: dict) -> dict:
        self._store[item["id"]] = item
        return item

    def get_by_id(self, item_id: str, partition_key: str) -> dict | None:
        return self._store.get(item_id)

    def get_all(self, partition_key: str | None = None) -> list[dict]:
        items = list(self._store.values())
        if partition_key is not None:
            # Try to filter by common partition key fields
            items = [
                i for i in items
                if i.get("site") == partition_key
                or i.get("assetId") == partition_key
                or i.get("systemType") == partition_key
            ]
        return items

    def query(
        self,
        query_str: str,
        parameters: list[dict] | None = None,
        partition_key: str | None = None,
    ) -> list[dict]:
        """Minimal query emulation for tests."""
        params = {p["name"]: p["value"] for p in (parameters or [])}
        items = list(self._store.values())

        # Filter by id
        if "@id" in params:
            items = [i for i in items if i.get("id") == params["@id"]]

        # Filter by status (exclude or match)
        if "@status" in params:
            items = [i for i in items if i.get("status") == params["@status"]]
        elif "@retired" in params:
            items = [i for i in items if i.get("status") != params["@retired"]]

        # Filter by assetId
        if "@assetId" in params:
            items = [i for i in items if i.get("assetId") == params["@assetId"]]

        # Filter by search
        if "@search" in params:
            term = params["@search"].lower()
            items = [
                i for i in items
                if term in i.get("name", "").lower()
                or term in i.get("description", "").lower()
            ]

        return items

    def update(self, item_id: str, partition_key: str, updates: dict) -> dict:
        from datetime import datetime, timezone

        item = self._store.get(item_id)
        if item is None:
            from azure.cosmos.exceptions import CosmosResourceNotFoundError
            raise CosmosResourceNotFoundError(status_code=404, message="Not found")
        item.update(updates)
        item["updatedAt"] = datetime.now(timezone.utc).isoformat()
        return item

    def delete(self, item_id: str, partition_key: str) -> None:
        item = self._store.get(item_id)
        if item is not None:
            item["status"] = "retired"


# Shared fake repo instances — reset per test via fixtures
_fake_tags_repo = FakeRepository()
_fake_assets_repo = FakeRepository()
_fake_sources_repo = FakeRepository()


@pytest.fixture(autouse=True)
def _reset_repos():
    """Clear all fake repos before each test."""
    _fake_tags_repo._store.clear()
    _fake_assets_repo._store.clear()
    _fake_sources_repo._store.clear()


@pytest.fixture()
def client():
    """Return a FastAPI TestClient with mocked Cosmos repos."""
    with (
        patch("src.routes.tags.get_tags_repo", return_value=_fake_tags_repo),
        patch("src.routes.assets.get_assets_repo", return_value=_fake_assets_repo),
        patch("src.routes.sources.get_sources_repo", return_value=_fake_sources_repo),
        patch("src.main.get_cosmos_client", return_value=MagicMock()),
    ):
        from src.main import app

        yield TestClient(app)


@pytest.fixture()
def tags_repo() -> FakeRepository:
    return _fake_tags_repo


@pytest.fixture()
def assets_repo() -> FakeRepository:
    return _fake_assets_repo


@pytest.fixture()
def sources_repo() -> FakeRepository:
    return _fake_sources_repo


# -- Helpers -----------------------------------------------------------------

VALID_TAG_PAYLOAD: dict[str, Any] = {
    "name": "MUN.L2.PMP001.OutletPressure",
    "description": "Outlet pressure of pump 001",
    "unit": "bar",
    "datatype": "float",
    "samplingFrequency": 1.0,
    "criticality": "high",
    "assetId": "asset-001",
}

VALID_ASSET_PAYLOAD: dict[str, Any] = {
    "site": "Plant-Munich",
    "line": "Line-2",
    "equipment": "Pump-001",
    "description": "Main coolant pump",
}

VALID_SOURCE_PAYLOAD: dict[str, Any] = {
    "systemType": "PLC",
    "connectorType": "OPC-UA",
    "topicOrPath": "ns=2;s=Pump001.Pressure",
    "description": "Pressure sensor PLC",
}
