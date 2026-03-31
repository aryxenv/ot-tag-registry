"""Tests for source endpoints."""

from conftest import VALID_SOURCE_PAYLOAD


class TestListSources:
    def test_list_empty(self, client):
        resp = client.get("/api/sources")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_returns_created(self, client):
        client.post("/api/sources", json=VALID_SOURCE_PAYLOAD)
        resp = client.get("/api/sources")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestCreateSource:
    def test_create_returns_201(self, client):
        resp = client.post("/api/sources", json=VALID_SOURCE_PAYLOAD)
        assert resp.status_code == 201
        data = resp.json()
        assert data["systemType"] == "PLC"
        assert data["connectorType"] == "OPC-UA"
        assert "id" in data

    def test_create_missing_required_field(self, client):
        payload = {"systemType": "PLC"}
        resp = client.post("/api/sources", json=payload)
        assert resp.status_code == 422

    def test_create_invalid_system_type(self, client):
        payload = {**VALID_SOURCE_PAYLOAD, "systemType": "MAGIC"}
        resp = client.post("/api/sources", json=payload)
        assert resp.status_code == 422
