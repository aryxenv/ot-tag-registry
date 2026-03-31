"""Tests for tag CRUD and lifecycle endpoints."""

import pytest
from conftest import VALID_TAG_PAYLOAD


class TestCreateTag:
    def test_create_returns_201(self, client):
        resp = client.post("/api/tags", json=VALID_TAG_PAYLOAD)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == VALID_TAG_PAYLOAD["name"]
        assert data["status"] == "draft"
        assert "id" in data
        assert "createdAt" in data

    def test_create_missing_required_field(self, client):
        payload = {k: v for k, v in VALID_TAG_PAYLOAD.items() if k != "name"}
        resp = client.post("/api/tags", json=payload)
        assert resp.status_code == 422

    def test_create_invalid_enum(self, client):
        payload = {**VALID_TAG_PAYLOAD, "datatype": "invalid"}
        resp = client.post("/api/tags", json=payload)
        assert resp.status_code == 422

    def test_create_invalid_criticality(self, client):
        payload = {**VALID_TAG_PAYLOAD, "criticality": "ultra"}
        resp = client.post("/api/tags", json=payload)
        assert resp.status_code == 422


class TestGetTag:
    def test_get_existing_tag(self, client):
        created = client.post("/api/tags", json=VALID_TAG_PAYLOAD).json()
        resp = client.get(f"/api/tags/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    def test_get_nonexistent_tag(self, client):
        resp = client.get("/api/tags/does-not-exist")
        assert resp.status_code == 404


class TestListTags:
    def test_list_empty(self, client):
        resp = client.get("/api/tags")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_excludes_retired_by_default(self, client, tags_repo):
        # Create a draft and a retired tag
        client.post("/api/tags", json=VALID_TAG_PAYLOAD)
        retired_payload = {**VALID_TAG_PAYLOAD, "name": "MUN.L2.PMP002.RetiredTag"}
        created = client.post("/api/tags", json=retired_payload).json()
        # Manually retire it in the fake repo
        tags_repo._store[created["id"]]["status"] = "retired"

        resp = client.get("/api/tags")
        names = [t["name"] for t in resp.json()]
        assert "MUN.L2.PMP002.RetiredTag" not in names

    def test_list_filter_by_status(self, client, tags_repo):
        created = client.post("/api/tags", json=VALID_TAG_PAYLOAD).json()
        tags_repo._store[created["id"]]["status"] = "active"

        resp = client.get("/api/tags?status=active")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_list_filter_by_asset_id(self, client):
        client.post("/api/tags", json=VALID_TAG_PAYLOAD)
        other = {**VALID_TAG_PAYLOAD, "name": "MUN.L2.PMP002.InletPressure", "assetId": "asset-999"}
        client.post("/api/tags", json=other)

        resp = client.get("/api/tags?assetId=asset-001")
        assert all(t["assetId"] == "asset-001" for t in resp.json())

    def test_list_search(self, client):
        client.post("/api/tags", json=VALID_TAG_PAYLOAD)
        resp = client.get("/api/tags?search=pump")
        assert len(resp.json()) >= 1


class TestUpdateTag:
    def test_update_partial(self, client):
        created = client.post("/api/tags", json=VALID_TAG_PAYLOAD).json()
        resp = client.put(f"/api/tags/{created['id']}", json={"unit": "psi"})
        assert resp.status_code == 200
        assert resp.json()["unit"] == "psi"

    def test_update_nonexistent(self, client):
        resp = client.put("/api/tags/no-such-id", json={"unit": "psi"})
        assert resp.status_code == 404

    def test_update_empty_body(self, client):
        created = client.post("/api/tags", json=VALID_TAG_PAYLOAD).json()
        resp = client.put(f"/api/tags/{created['id']}", json={})
        assert resp.status_code == 400

    def test_update_status_to_active(self, client):
        created = client.post("/api/tags", json=VALID_TAG_PAYLOAD).json()
        resp = client.put(
            f"/api/tags/{created['id']}", json={"status": "active"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"


class TestRetireTag:
    def test_retire_returns_204(self, client):
        created = client.post("/api/tags", json=VALID_TAG_PAYLOAD).json()
        resp = client.patch(f"/api/tags/{created['id']}/retire")
        assert resp.status_code == 204
        assert resp.content == b""

    def test_retire_sets_status(self, client, tags_repo):
        created = client.post("/api/tags", json=VALID_TAG_PAYLOAD).json()
        client.patch(f"/api/tags/{created['id']}/retire")
        assert tags_repo._store[created["id"]]["status"] == "retired"

    def test_retire_nonexistent(self, client):
        resp = client.patch("/api/tags/no-such-id/retire")
        assert resp.status_code == 404


class TestNameValidation:
    """Integration tests: naming validator enforced on create/update."""

    def test_create_rejects_invalid_name(self, client):
        payload = {**VALID_TAG_PAYLOAD, "name": "bad-name"}
        resp = client.post("/api/tags", json=payload)
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        assert detail["error"] == "Invalid tag name"
        assert len(detail["details"]) >= 1

    def test_create_rejects_too_few_segments(self, client):
        payload = {**VALID_TAG_PAYLOAD, "name": "MUN.L2"}
        resp = client.post("/api/tags", json=payload)
        assert resp.status_code == 400

    def test_update_validates_name_when_changed(self, client):
        created = client.post("/api/tags", json=VALID_TAG_PAYLOAD).json()
        resp = client.put(
            f"/api/tags/{created['id']}", json={"name": "invalid!!"}
        )
        assert resp.status_code == 400

    def test_update_skips_validation_for_other_fields(self, client):
        created = client.post("/api/tags", json=VALID_TAG_PAYLOAD).json()
        resp = client.put(f"/api/tags/{created['id']}", json={"unit": "psi"})
        assert resp.status_code == 200


class TestValidateNameEndpoint:
    def test_valid_name(self, client):
        resp = client.post(
            "/api/tags/validate-name",
            json={"name": "MUN.L2.PMP001.OutletPressure"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert data["errors"] == []

    def test_invalid_name(self, client):
        resp = client.post(
            "/api/tags/validate-name",
            json={"name": "bad"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False
        assert len(data["errors"]) >= 1

    def test_five_segment_valid(self, client):
        resp = client.post(
            "/api/tags/validate-name",
            json={"name": "Munich.Line2.Pump001.Pressure.Discharge"},
        )
        assert resp.status_code == 200
        assert resp.json()["valid"] is True


class TestApprovalWorkflow:
    def test_request_approval_sets_pending(self, client):
        created = client.post("/api/tags", json=VALID_TAG_PAYLOAD).json()
        resp = client.post(f"/api/tags/{created['id']}/request-approval")
        assert resp.status_code == 200
        data = resp.json()
        assert data["approvalStatus"] == "pending"

    def test_request_approval_rejects_active_tag(self, client, tags_repo):
        created = client.post("/api/tags", json=VALID_TAG_PAYLOAD).json()
        tags_repo._store[created["id"]]["status"] = "active"
        resp = client.post(f"/api/tags/{created['id']}/request-approval")
        assert resp.status_code == 400

    def test_request_approval_rejects_already_pending(self, client, tags_repo):
        created = client.post("/api/tags", json=VALID_TAG_PAYLOAD).json()
        tags_repo._store[created["id"]]["approvalStatus"] = "pending"
        resp = client.post(f"/api/tags/{created['id']}/request-approval")
        assert resp.status_code == 400

    def test_approve_sets_approved_and_active(self, client, tags_repo):
        created = client.post("/api/tags", json=VALID_TAG_PAYLOAD).json()
        tags_repo._store[created["id"]]["approvalStatus"] = "pending"
        resp = client.post(f"/api/tags/{created['id']}/approve")
        assert resp.status_code == 200
        data = resp.json()
        assert data["approvalStatus"] == "approved"
        assert data["status"] == "active"

    def test_approve_rejects_non_pending(self, client):
        created = client.post("/api/tags", json=VALID_TAG_PAYLOAD).json()
        resp = client.post(f"/api/tags/{created['id']}/approve")
        assert resp.status_code == 400

    def test_reject_with_reason(self, client, tags_repo):
        created = client.post("/api/tags", json=VALID_TAG_PAYLOAD).json()
        tags_repo._store[created["id"]]["approvalStatus"] = "pending"
        resp = client.post(
            f"/api/tags/{created['id']}/reject",
            json={"rejectionReason": "Missing calibration data"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["approvalStatus"] == "rejected"
        assert data["rejectionReason"] == "Missing calibration data"

    def test_reject_without_reason(self, client, tags_repo):
        created = client.post("/api/tags", json=VALID_TAG_PAYLOAD).json()
        tags_repo._store[created["id"]]["approvalStatus"] = "pending"
        resp = client.post(f"/api/tags/{created['id']}/reject")
        assert resp.status_code == 200
        data = resp.json()
        assert data["approvalStatus"] == "rejected"

    def test_re_request_after_rejection(self, client, tags_repo):
        created = client.post("/api/tags", json=VALID_TAG_PAYLOAD).json()
        tags_repo._store[created["id"]]["approvalStatus"] = "rejected"
        resp = client.post(f"/api/tags/{created['id']}/request-approval")
        assert resp.status_code == 200
        data = resp.json()
        assert data["approvalStatus"] == "pending"

    def test_request_approval_nonexistent(self, client):
        resp = client.post("/api/tags/nonexistent-id/request-approval")
        assert resp.status_code == 404

    def test_approve_nonexistent(self, client):
        resp = client.post("/api/tags/nonexistent-id/approve")
        assert resp.status_code == 404

    def test_reject_nonexistent(self, client):
        resp = client.post("/api/tags/nonexistent-id/reject")
        assert resp.status_code == 404
