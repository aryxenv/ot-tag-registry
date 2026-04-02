"""Tests for the auto-fill endpoint."""

from unittest.mock import AsyncMock, patch

import pytest
from conftest import VALID_TAG_PAYLOAD  # noqa: F401 — keeps conftest fixtures active

from src.models.auto_fill import AutoFillMatch, AutoFillResult
from src.utils.search import SearchServiceError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

AUTOFILL_URL = "/api/tags/auto-fill"

VALID_AUTOFILL_PAYLOAD = {
    "query": "outlet pressure sensor on the main cooling pump in Luxembourg Line 1",
}

MOCK_MATCHES = [
    AutoFillMatch(
        tagName="LUX.L1.PMP001.Pressure.Bar.1",
        description="Outlet pressure of primary coolant pump",
        score=0.94,
        site="LUX",
        line="L1",
        equipment="PMP001",
        unit="bar",
        datatype="float",
    ),
    AutoFillMatch(
        tagName="LUX.L1.PMP001.Pressure.Bar.2",
        description="Discharge pressure of primary coolant pump",
        score=0.89,
        site="LUX",
        line="L1",
        equipment="PMP001",
        unit="bar",
        datatype="float",
    ),
    AutoFillMatch(
        tagName="LUX.L1.PMP002.Pressure.Bar.1",
        description="Outlet pressure of secondary coolant pump",
        score=0.82,
        site="LUX",
        line="L1",
        equipment="PMP002",
        unit="bar",
        datatype="float",
    ),
]

MOCK_RESULT = AutoFillResult(
    site="Plant-Luxembourg",
    line="Line-1",
    equipment="Pump-001",
    unit="bar",
    datatype="float",
    name="LUX.L1.PMP001.Pressure.Bar",
    description="Outlet pressure of primary coolant pump",
    criticality="medium",
    confidence=0.94,
    matches=MOCK_MATCHES,
)

EMPTY_RESULT = AutoFillResult(
    confidence=0.0,
    matches=[],
)

FALLBACK_RESULT = AutoFillResult(
    confidence=0.94,
    matches=MOCK_MATCHES,
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAutoFill:
    """Tests for POST /api/tags/auto-fill."""

    def test_autofill_returns_200_with_matches(self, client):
        with patch(
            "src.routes.auto_fill.auto_fill_tag",
            new_callable=AsyncMock,
            return_value=MOCK_RESULT,
        ):
            resp = client.post(AUTOFILL_URL, json=VALID_AUTOFILL_PAYLOAD)

        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "LUX.L1.PMP001.Pressure.Bar"
        assert data["site"] == "Plant-Luxembourg"
        assert data["line"] == "Line-1"
        assert data["equipment"] == "Pump-001"
        assert data["unit"] == "bar"
        assert data["datatype"] == "float"
        assert data["criticality"] == "medium"
        assert data["confidence"] == 0.94
        assert len(data["matches"]) == 3

    def test_autofill_returns_200_with_no_matches(self, client):
        with patch(
            "src.routes.auto_fill.auto_fill_tag",
            new_callable=AsyncMock,
            return_value=EMPTY_RESULT,
        ):
            resp = client.post(AUTOFILL_URL, json=VALID_AUTOFILL_PAYLOAD)

        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] is None
        assert data["matches"] == []
        assert data["confidence"] == 0.0

    def test_autofill_passes_query_to_search(self, client):
        with patch(
            "src.routes.auto_fill.auto_fill_tag",
            new_callable=AsyncMock,
            return_value=MOCK_RESULT,
        ) as mock_fn:
            resp = client.post(AUTOFILL_URL, json=VALID_AUTOFILL_PAYLOAD)

        assert resp.status_code == 200
        call_kwargs = mock_fn.call_args.kwargs
        assert call_kwargs["query"] == VALID_AUTOFILL_PAYLOAD["query"]

    def test_autofill_missing_query_returns_422(self, client):
        resp = client.post(AUTOFILL_URL, json={})
        assert resp.status_code == 422

    def test_autofill_search_service_error_returns_502(self, client):
        with patch(
            "src.routes.auto_fill.auto_fill_tag",
            new_callable=AsyncMock,
            side_effect=SearchServiceError("Search query failed: connection timeout"),
        ):
            resp = client.post(AUTOFILL_URL, json=VALID_AUTOFILL_PAYLOAD)

        assert resp.status_code == 502
        assert "error" in resp.json()["detail"]

    def test_autofill_config_error_returns_400(self, client):
        with patch(
            "src.routes.auto_fill.auto_fill_tag",
            new_callable=AsyncMock,
            side_effect=ValueError("SEARCH_ENDPOINT environment variable must be set"),
        ):
            resp = client.post(AUTOFILL_URL, json=VALID_AUTOFILL_PAYLOAD)

        assert resp.status_code == 400
        assert "SEARCH_ENDPOINT" in resp.json()["detail"]["error"]

    def test_autofill_response_has_all_match_fields(self, client):
        with patch(
            "src.routes.auto_fill.auto_fill_tag",
            new_callable=AsyncMock,
            return_value=MOCK_RESULT,
        ):
            resp = client.post(AUTOFILL_URL, json=VALID_AUTOFILL_PAYLOAD)

        match = resp.json()["matches"][0]
        assert "tagName" in match
        assert "description" in match
        assert "score" in match
        assert "site" in match
        assert "line" in match
        assert "equipment" in match
        assert "unit" in match
        assert "datatype" in match

    def test_autofill_ai_extraction_fields(self, client):
        """Verify AI-extracted fields use display names for frontend dropdowns."""
        with patch(
            "src.routes.auto_fill.auto_fill_tag",
            new_callable=AsyncMock,
            return_value=MOCK_RESULT,
        ):
            resp = client.post(AUTOFILL_URL, json=VALID_AUTOFILL_PAYLOAD)

        data = resp.json()
        assert data["site"] == "Plant-Luxembourg"
        assert data["line"] == "Line-1"
        assert data["equipment"] == "Pump-001"
        assert data["name"] == "LUX.L1.PMP001.Pressure.Bar"
        assert data["description"] is not None
        assert data["criticality"] in ("low", "medium", "high", "critical")

    def test_autofill_ai_fallback_on_error(self, client):
        """When AI extraction fails, response still includes matches."""
        with patch(
            "src.routes.auto_fill.auto_fill_tag",
            new_callable=AsyncMock,
            return_value=FALLBACK_RESULT,
        ):
            resp = client.post(AUTOFILL_URL, json=VALID_AUTOFILL_PAYLOAD)

        data = resp.json()
        assert data["name"] is None
        assert data["equipment"] is None
        assert len(data["matches"]) == 3
        assert data["confidence"] == 0.94

    def test_autofill_partial_results(self, client):
        """Some extracted fields may be null if AI can't determine them."""
        partial = AutoFillResult(
            site="Plant-Luxembourg",
            line="Line-1",
            equipment=None,
            unit="bar",
            datatype=None,
            name=None,
            description="Pressure sensor on pump",
            criticality=None,
            confidence=0.80,
            matches=MOCK_MATCHES[:1],
        )
        with patch(
            "src.routes.auto_fill.auto_fill_tag",
            new_callable=AsyncMock,
            return_value=partial,
        ):
            resp = client.post(AUTOFILL_URL, json=VALID_AUTOFILL_PAYLOAD)

        data = resp.json()
        assert data["site"] == "Plant-Luxembourg"
        assert data["equipment"] is None
        assert data["name"] is None
        assert data["unit"] == "bar"
