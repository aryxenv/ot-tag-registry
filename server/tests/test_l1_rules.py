"""Tests for L1 (Range) rule endpoints."""

from conftest import VALID_TAG_PAYLOAD, VALID_L1_RULE_PAYLOAD


def _seed_tag(client) -> str:
    """Create a tag and return its id."""
    resp = client.post("/api/tags", json=VALID_TAG_PAYLOAD)
    return resp.json()["id"]


class TestGetL1Rule:
    def test_returns_rule(self, client):
        tag_id = _seed_tag(client)
        client.post(f"/api/tags/{tag_id}/rules/l1", json=VALID_L1_RULE_PAYLOAD)
        resp = client.get(f"/api/tags/{tag_id}/rules/l1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["tagId"] == tag_id
        assert data["min"] == 0.0
        assert data["max"] == 100.0

    def test_404_when_no_rule(self, client):
        tag_id = _seed_tag(client)
        resp = client.get(f"/api/tags/{tag_id}/rules/l1")
        assert resp.status_code == 404

    def test_404_when_tag_missing(self, client):
        resp = client.get("/api/tags/nonexistent/rules/l1")
        assert resp.status_code == 404
        assert "Tag not found" in resp.json()["detail"]["error"]


class TestCreateL1Rule:
    def test_create_returns_201(self, client):
        tag_id = _seed_tag(client)
        resp = client.post(f"/api/tags/{tag_id}/rules/l1", json=VALID_L1_RULE_PAYLOAD)
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert data["tagId"] == tag_id
        assert data["min"] == 0.0
        assert data["max"] == 100.0
        assert data["spikeThreshold"] == 25.0
        assert data["missingDataPolicy"] == "alert"

    def test_upsert_replaces_existing(self, client):
        tag_id = _seed_tag(client)
        resp1 = client.post(f"/api/tags/{tag_id}/rules/l1", json=VALID_L1_RULE_PAYLOAD)
        original_id = resp1.json()["id"]

        new_payload = {"min": 10.0, "max": 200.0}
        resp2 = client.post(f"/api/tags/{tag_id}/rules/l1", json=new_payload)
        assert resp2.status_code == 201
        data = resp2.json()
        assert data["id"] == original_id  # same id preserved
        assert data["min"] == 10.0
        assert data["max"] == 200.0
        assert data["spikeThreshold"] is None  # replaced, not merged

    def test_validation_requires_at_least_one_threshold(self, client):
        tag_id = _seed_tag(client)
        payload = {"missingDataPolicy": "alert"}
        resp = client.post(f"/api/tags/{tag_id}/rules/l1", json=payload)
        assert resp.status_code == 422

    def test_only_min_is_valid(self, client):
        tag_id = _seed_tag(client)
        resp = client.post(f"/api/tags/{tag_id}/rules/l1", json={"min": 5.0})
        assert resp.status_code == 201

    def test_only_spike_is_valid(self, client):
        tag_id = _seed_tag(client)
        resp = client.post(
            f"/api/tags/{tag_id}/rules/l1", json={"spikeThreshold": 10.0}
        )
        assert resp.status_code == 201

    def test_404_when_tag_missing(self, client):
        resp = client.post("/api/tags/nonexistent/rules/l1", json=VALID_L1_RULE_PAYLOAD)
        assert resp.status_code == 404


class TestUpdateL1Rule:
    def test_partial_update(self, client):
        tag_id = _seed_tag(client)
        client.post(f"/api/tags/{tag_id}/rules/l1", json=VALID_L1_RULE_PAYLOAD)
        resp = client.put(f"/api/tags/{tag_id}/rules/l1", json={"max": 150.0})
        assert resp.status_code == 200
        data = resp.json()
        assert data["max"] == 150.0
        assert data["min"] == 0.0  # unchanged

    def test_update_missing_data_policy(self, client):
        tag_id = _seed_tag(client)
        client.post(f"/api/tags/{tag_id}/rules/l1", json=VALID_L1_RULE_PAYLOAD)
        resp = client.put(
            f"/api/tags/{tag_id}/rules/l1", json={"missingDataPolicy": "ignore"}
        )
        assert resp.status_code == 200
        assert resp.json()["missingDataPolicy"] == "ignore"

    def test_404_when_no_rule(self, client):
        tag_id = _seed_tag(client)
        resp = client.put(f"/api/tags/{tag_id}/rules/l1", json={"max": 50.0})
        assert resp.status_code == 404

    def test_400_empty_body(self, client):
        tag_id = _seed_tag(client)
        client.post(f"/api/tags/{tag_id}/rules/l1", json=VALID_L1_RULE_PAYLOAD)
        resp = client.put(f"/api/tags/{tag_id}/rules/l1", json={})
        assert resp.status_code == 400

    def test_rejects_removing_all_thresholds(self, client):
        tag_id = _seed_tag(client)
        client.post(f"/api/tags/{tag_id}/rules/l1", json={"min": 5.0})
        resp = client.put(f"/api/tags/{tag_id}/rules/l1", json={"min": None})
        assert resp.status_code == 400
        assert "at least one" in resp.json()["detail"]["error"].lower()


class TestDeleteL1Rule:
    def test_delete_returns_204(self, client):
        tag_id = _seed_tag(client)
        client.post(f"/api/tags/{tag_id}/rules/l1", json=VALID_L1_RULE_PAYLOAD)
        resp = client.delete(f"/api/tags/{tag_id}/rules/l1")
        assert resp.status_code == 204
        assert resp.content == b""

    def test_rule_gone_after_delete(self, client):
        tag_id = _seed_tag(client)
        client.post(f"/api/tags/{tag_id}/rules/l1", json=VALID_L1_RULE_PAYLOAD)
        client.delete(f"/api/tags/{tag_id}/rules/l1")
        resp = client.get(f"/api/tags/{tag_id}/rules/l1")
        assert resp.status_code == 404

    def test_404_when_no_rule(self, client):
        tag_id = _seed_tag(client)
        resp = client.delete(f"/api/tags/{tag_id}/rules/l1")
        assert resp.status_code == 404

    def test_404_when_tag_missing(self, client):
        resp = client.delete("/api/tags/nonexistent/rules/l1")
        assert resp.status_code == 404
