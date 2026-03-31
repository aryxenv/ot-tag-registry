"""Tests for L2 (State Profile) rule endpoints."""

from conftest import VALID_TAG_PAYLOAD, VALID_L2_RULE_PAYLOAD


def _seed_tag(client) -> str:
    """Create a tag and return its id."""
    resp = client.post("/api/tags", json=VALID_TAG_PAYLOAD)
    return resp.json()["id"]


class TestGetL2Rule:
    def test_returns_rule(self, client):
        tag_id = _seed_tag(client)
        client.post(f"/api/tags/{tag_id}/rules/l2", json=VALID_L2_RULE_PAYLOAD)
        resp = client.get(f"/api/tags/{tag_id}/rules/l2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["tagId"] == tag_id
        assert len(data["stateMapping"]) == 2

    def test_404_when_no_rule(self, client):
        tag_id = _seed_tag(client)
        resp = client.get(f"/api/tags/{tag_id}/rules/l2")
        assert resp.status_code == 404

    def test_404_when_tag_missing(self, client):
        resp = client.get("/api/tags/nonexistent/rules/l2")
        assert resp.status_code == 404
        assert "Tag not found" in resp.json()["detail"]["error"]


class TestCreateL2Rule:
    def test_create_returns_201(self, client):
        tag_id = _seed_tag(client)
        resp = client.post(f"/api/tags/{tag_id}/rules/l2", json=VALID_L2_RULE_PAYLOAD)
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert data["tagId"] == tag_id
        assert len(data["stateMapping"]) == 2
        assert data["stateMapping"][0]["state"] == "Running"
        assert data["stateMapping"][1]["state"] == "Idle"

    def test_upsert_replaces_existing(self, client):
        tag_id = _seed_tag(client)
        resp1 = client.post(f"/api/tags/{tag_id}/rules/l2", json=VALID_L2_RULE_PAYLOAD)
        original_id = resp1.json()["id"]

        new_payload = {
            "stateMapping": [
                {
                    "state": "Stop",
                    "conditionField": "speed",
                    "conditionOperator": "==",
                    "conditionValue": 0.0,
                }
            ]
        }
        resp2 = client.post(f"/api/tags/{tag_id}/rules/l2", json=new_payload)
        assert resp2.status_code == 201
        data = resp2.json()
        assert data["id"] == original_id
        assert len(data["stateMapping"]) == 1
        assert data["stateMapping"][0]["state"] == "Stop"

    def test_validation_requires_non_empty_mapping(self, client):
        tag_id = _seed_tag(client)
        resp = client.post(f"/api/tags/{tag_id}/rules/l2", json={"stateMapping": []})
        assert resp.status_code == 422

    def test_validation_rejects_invalid_state(self, client):
        tag_id = _seed_tag(client)
        payload = {
            "stateMapping": [
                {
                    "state": "Flying",
                    "conditionField": "speed",
                    "conditionOperator": ">",
                    "conditionValue": 100.0,
                }
            ]
        }
        resp = client.post(f"/api/tags/{tag_id}/rules/l2", json=payload)
        assert resp.status_code == 422

    def test_validation_rejects_invalid_operator(self, client):
        tag_id = _seed_tag(client)
        payload = {
            "stateMapping": [
                {
                    "state": "Running",
                    "conditionField": "speed",
                    "conditionOperator": "LIKE",
                    "conditionValue": 100.0,
                }
            ]
        }
        resp = client.post(f"/api/tags/{tag_id}/rules/l2", json=payload)
        assert resp.status_code == 422

    def test_between_operator_with_list_value(self, client):
        tag_id = _seed_tag(client)
        payload = {
            "stateMapping": [
                {
                    "state": "Running",
                    "conditionField": "speed",
                    "conditionOperator": "between",
                    "conditionValue": [50.0, 200.0],
                    "rangeMin": 50.0,
                    "rangeMax": 200.0,
                }
            ]
        }
        resp = client.post(f"/api/tags/{tag_id}/rules/l2", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["stateMapping"][0]["conditionValue"] == [50.0, 200.0]

    def test_404_when_tag_missing(self, client):
        resp = client.post("/api/tags/nonexistent/rules/l2", json=VALID_L2_RULE_PAYLOAD)
        assert resp.status_code == 404


class TestUpdateL2Rule:
    def test_update_state_mapping(self, client):
        tag_id = _seed_tag(client)
        client.post(f"/api/tags/{tag_id}/rules/l2", json=VALID_L2_RULE_PAYLOAD)
        new_mapping = [
            {
                "state": "Stop",
                "conditionField": "speed",
                "conditionOperator": "==",
                "conditionValue": 0.0,
            }
        ]
        resp = client.put(
            f"/api/tags/{tag_id}/rules/l2", json={"stateMapping": new_mapping}
        )
        assert resp.status_code == 200
        assert len(resp.json()["stateMapping"]) == 1

    def test_404_when_no_rule(self, client):
        tag_id = _seed_tag(client)
        resp = client.put(
            f"/api/tags/{tag_id}/rules/l2",
            json={
                "stateMapping": [
                    {
                        "state": "Running",
                        "conditionField": "speed",
                        "conditionOperator": ">",
                        "conditionValue": 100.0,
                    }
                ]
            },
        )
        assert resp.status_code == 404

    def test_400_empty_body(self, client):
        tag_id = _seed_tag(client)
        client.post(f"/api/tags/{tag_id}/rules/l2", json=VALID_L2_RULE_PAYLOAD)
        resp = client.put(f"/api/tags/{tag_id}/rules/l2", json={})
        assert resp.status_code == 400

    def test_rejects_empty_state_mapping(self, client):
        tag_id = _seed_tag(client)
        client.post(f"/api/tags/{tag_id}/rules/l2", json=VALID_L2_RULE_PAYLOAD)
        resp = client.put(f"/api/tags/{tag_id}/rules/l2", json={"stateMapping": []})
        assert resp.status_code == 400


class TestDeleteL2Rule:
    def test_delete_returns_204(self, client):
        tag_id = _seed_tag(client)
        client.post(f"/api/tags/{tag_id}/rules/l2", json=VALID_L2_RULE_PAYLOAD)
        resp = client.delete(f"/api/tags/{tag_id}/rules/l2")
        assert resp.status_code == 204
        assert resp.content == b""

    def test_rule_gone_after_delete(self, client):
        tag_id = _seed_tag(client)
        client.post(f"/api/tags/{tag_id}/rules/l2", json=VALID_L2_RULE_PAYLOAD)
        client.delete(f"/api/tags/{tag_id}/rules/l2")
        resp = client.get(f"/api/tags/{tag_id}/rules/l2")
        assert resp.status_code == 404

    def test_404_when_no_rule(self, client):
        tag_id = _seed_tag(client)
        resp = client.delete(f"/api/tags/{tag_id}/rules/l2")
        assert resp.status_code == 404

    def test_404_when_tag_missing(self, client):
        resp = client.delete("/api/tags/nonexistent/rules/l2")
        assert resp.status_code == 404
