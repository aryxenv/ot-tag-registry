"""Tests for the suggest-name endpoint."""

from unittest.mock import AsyncMock, patch

import pytest
from conftest import VALID_TAG_PAYLOAD  # noqa: F401 — keeps conftest fixtures active

from src.models.suggest_name import SuggestionMatch, SuggestionResult
from src.utils.search import SearchServiceError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SUGGEST_URL = "/api/tags/suggest-name"

VALID_SUGGEST_PAYLOAD = {
    "site": "LUX",
    "line": "L1",
    "description": "outlet pressure of primary coolant pump",
    "equipment": "PMP001",
    "unit": "bar",
    "datatype": "float",
}

MINIMAL_SUGGEST_PAYLOAD = {
    "site": "LUX",
    "line": "L1",
    "description": "outlet pressure",
}

MOCK_RESULT = SuggestionResult(
    suggestedName="LUX.L1.PMP001.OutletPressure",
    alternatives=[
        "LUX.L1.PMP001.DischargePressure",
        "LUX.L1.PMP002.OutletPressure",
    ],
    evidence=(
        "Similar to tag 'LUX.L1.PMP001.OutletPressure' — "
        "same site/line, description match on "
        "'outlet pressure of primary coolant pump' ↔ "
        "'Outlet pressure of primary coolant pump' "
        "(0.94 similarity)"
    ),
    matches=[
        SuggestionMatch(
            tagName="LUX.L1.PMP001.OutletPressure",
            description="Outlet pressure of primary coolant pump",
            score=0.94,
            site="LUX",
            line="L1",
            equipment="PMP001",
            unit="bar",
            datatype="float",
        ),
        SuggestionMatch(
            tagName="LUX.L1.PMP001.DischargePressure",
            description="Discharge pressure of primary coolant pump",
            score=0.89,
            site="LUX",
            line="L1",
            equipment="PMP001",
            unit="bar",
            datatype="float",
        ),
        SuggestionMatch(
            tagName="LUX.L1.PMP002.OutletPressure",
            description="Outlet pressure of secondary coolant pump",
            score=0.82,
            site="LUX",
            line="L1",
            equipment="PMP002",
            unit="bar",
            datatype="float",
        ),
    ],
)

EMPTY_RESULT = SuggestionResult(
    suggestedName="",
    alternatives=[],
    evidence="",
    matches=[],
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSuggestName:
    """Tests for POST /api/tags/suggest-name."""

    def test_suggest_returns_200_with_matches(self, client):
        with patch(
            "src.routes.suggest_name.suggest_tag_name",
            new_callable=AsyncMock,
            return_value=MOCK_RESULT,
        ):
            resp = client.post(SUGGEST_URL, json=VALID_SUGGEST_PAYLOAD)

        assert resp.status_code == 200
        data = resp.json()
        assert data["suggestedName"] == "LUX.L1.PMP001.OutletPressure"
        assert len(data["alternatives"]) == 2
        assert len(data["matches"]) == 3
        assert data["evidence"] != ""

    def test_suggest_returns_200_with_no_matches(self, client):
        with patch(
            "src.routes.suggest_name.suggest_tag_name",
            new_callable=AsyncMock,
            return_value=EMPTY_RESULT,
        ):
            resp = client.post(SUGGEST_URL, json=VALID_SUGGEST_PAYLOAD)

        assert resp.status_code == 200
        data = resp.json()
        assert data["suggestedName"] == ""
        assert data["alternatives"] == []
        assert data["matches"] == []
        assert data["evidence"] == ""

    def test_suggest_minimal_payload(self, client):
        with patch(
            "src.routes.suggest_name.suggest_tag_name",
            new_callable=AsyncMock,
            return_value=MOCK_RESULT,
        ) as mock_fn:
            resp = client.post(SUGGEST_URL, json=MINIMAL_SUGGEST_PAYLOAD)

        assert resp.status_code == 200
        call_kwargs = mock_fn.call_args.kwargs
        assert call_kwargs["site"] == "LUX"
        assert call_kwargs["line"] == "L1"
        assert call_kwargs["description"] == "outlet pressure"
        assert call_kwargs["equipment"] is None
        assert call_kwargs["unit"] is None
        assert call_kwargs["datatype"] is None

    def test_suggest_missing_required_field(self, client):
        # Missing 'description'
        payload = {"site": "LUX", "line": "L1"}
        resp = client.post(SUGGEST_URL, json=payload)
        assert resp.status_code == 422

    def test_suggest_missing_site(self, client):
        payload = {"line": "L1", "description": "pressure"}
        resp = client.post(SUGGEST_URL, json=payload)
        assert resp.status_code == 422

    def test_suggest_search_service_error_returns_502(self, client):
        with patch(
            "src.routes.suggest_name.suggest_tag_name",
            new_callable=AsyncMock,
            side_effect=SearchServiceError("Search query failed: connection timeout"),
        ):
            resp = client.post(SUGGEST_URL, json=VALID_SUGGEST_PAYLOAD)

        assert resp.status_code == 502
        assert "error" in resp.json()["detail"]

    def test_suggest_config_error_returns_400(self, client):
        with patch(
            "src.routes.suggest_name.suggest_tag_name",
            new_callable=AsyncMock,
            side_effect=ValueError("SEARCH_ENDPOINT environment variable must be set"),
        ):
            resp = client.post(SUGGEST_URL, json=VALID_SUGGEST_PAYLOAD)

        assert resp.status_code == 400
        assert "SEARCH_ENDPOINT" in resp.json()["detail"]["error"]

    def test_suggest_response_has_all_match_fields(self, client):
        with patch(
            "src.routes.suggest_name.suggest_tag_name",
            new_callable=AsyncMock,
            return_value=MOCK_RESULT,
        ):
            resp = client.post(SUGGEST_URL, json=VALID_SUGGEST_PAYLOAD)

        match = resp.json()["matches"][0]
        assert "tagName" in match
        assert "description" in match
        assert "score" in match
        assert "site" in match
        assert "line" in match
        assert "equipment" in match
        assert "unit" in match
        assert "datatype" in match

    def test_suggest_evidence_present_when_matches_exist(self, client):
        with patch(
            "src.routes.suggest_name.suggest_tag_name",
            new_callable=AsyncMock,
            return_value=MOCK_RESULT,
        ):
            resp = client.post(SUGGEST_URL, json=VALID_SUGGEST_PAYLOAD)

        data = resp.json()
        assert "similarity" in data["evidence"]
        assert "LUX.L1.PMP001.OutletPressure" in data["evidence"]

    def test_suggest_alternatives_exclude_top_match(self, client):
        with patch(
            "src.routes.suggest_name.suggest_tag_name",
            new_callable=AsyncMock,
            return_value=MOCK_RESULT,
        ):
            resp = client.post(SUGGEST_URL, json=VALID_SUGGEST_PAYLOAD)

        data = resp.json()
        assert data["suggestedName"] not in data["alternatives"]
