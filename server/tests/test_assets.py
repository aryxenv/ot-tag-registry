"""Tests for asset endpoints."""

from conftest import VALID_ASSET_PAYLOAD


class TestListAssets:
    def test_list_empty(self, client):
        resp = client.get("/api/assets")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_returns_created(self, client):
        client.post("/api/assets", json=VALID_ASSET_PAYLOAD)
        resp = client.get("/api/assets")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestCreateAsset:
    def test_create_returns_201(self, client):
        resp = client.post("/api/assets", json=VALID_ASSET_PAYLOAD)
        assert resp.status_code == 201
        data = resp.json()
        assert data["site"] == VALID_ASSET_PAYLOAD["site"]
        assert data["hierarchy"] == "Plant-Munich.Line-2.Pump-001"
        assert "id" in data

    def test_create_missing_required_field(self, client):
        payload = {"site": "X"}
        resp = client.post("/api/assets", json=payload)
        assert resp.status_code == 422

    def test_create_optional_description(self, client):
        payload = {k: v for k, v in VALID_ASSET_PAYLOAD.items() if k != "description"}
        resp = client.post("/api/assets", json=payload)
        assert resp.status_code == 201
