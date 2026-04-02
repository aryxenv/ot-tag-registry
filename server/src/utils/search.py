"""Azure AI Search + AI extraction client for tag auto-fill.

Self-contained module — queries the ``golden-tags`` Azure AI Search index
using hybrid search (keyword text + semantic embedding, no OData filters),
then passes the results through Mistral-Large-3 (via Azure AI Foundry) to
extract structured form fields.

Required environment variables (loaded by ``main.py`` via ``dotenv``):
    SEARCH_ENDPOINT, SEARCH_INDEX_NAME,
    PROJECT_ENDPOINT, PROJECT_EMBEDDING_DEPLOYMENT, PROJECT_CHAT_DEPLOYMENT
Optional:
    SEARCH_API_KEY  — falls back to DefaultAzureCredential when unset.
"""

import json
import logging
import os

from azure.core.exceptions import HttpResponseError, ServiceRequestError
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

from src.models.auto_fill import AutoFillMatch, AutoFillResult

logger = logging.getLogger("ot_tag_registry.search")

_SELECT_FIELDS = [
    "tagName",
    "description",
    "site",
    "line",
    "equipment",
    "unit",
    "datatype",
]

# Display name mappings — keep in sync with client/src/utils/tagNameMappings.ts
_SITE_DISPLAY = {"LUX": "Plant-Luxembourg", "BEL": "Plant-Brussels", "NED": "Plant-Amsterdam"}
_EQUIP_PREFIX_DISPLAY = {
    "PMP": "Pump", "CMP": "Compressor", "MOT": "Motor", "CNV": "Conveyor",
    "VLV": "Valve", "HEX": "HeatExchanger", "BLR": "Boiler", "TNK": "Tank",
}

_AUTOFILL_SYSTEM_PROMPT = """\
You are a tag naming assistant for an industrial IoT tag registry.

## Tag Naming Format
`SITE.LINE.EQUIPMENT.MEASUREMENT.UNIT.ID`

| Segment | Description | Examples |
|---------|-------------|----------|
| SITE | 3-letter plant code | LUX, BEL, NED |
| LINE | Production line | L1, L2, L3 |
| EQUIPMENT | Type abbreviation + 3-digit number | PMP001, CMP003, MOT004 |
| MEASUREMENT | PascalCase measurement name | Pressure, Temperature, Speed |
| UNIT | PascalCase unit code | Bar, Cel, Rpm, Mms, Lpm |
| ID | Numeric (omit — the system adds it) | — |

## Equipment Codes
PMP = Pump, CMP = Compressor, MOT = Motor, CNV = Conveyor, VLV = Valve, HEX = Heat Exchanger, BLR = Boiler, TNK = Tank

## Frontend Display Names
Sites: LUX → "Plant-Luxembourg", BEL → "Plant-Brussels", NED → "Plant-Amsterdam"
Lines: L1 → "Line-1", L2 → "Line-2", etc.
Equipment: PMP001 → "Pump-001", CMP003 → "Compressor-003", MOT004 → "Motor-004"

## Your Task
Given the user's query and similar existing tags from the registry, extract structured fields. Return a JSON object with these keys:
- "site": display name (e.g. "Plant-Luxembourg") or null
- "line": display name (e.g. "Line-1") or null
- "equipment": display name (e.g. "Pump-001") or null
- "unit": engineering unit in lowercase (e.g. "bar", "°C", "RPM") or null
- "datatype": "float", "int", or "bool" — or null
- "name": tag name WITHOUT the ID suffix (e.g. "LUX.L1.PMP001.Pressure.Bar") or null
- "description": cleaned-up one-line description or null
- "criticality": "low", "medium", "high", or "critical" — or null

Return ONLY valid JSON, no markdown fences, no explanation."""


class SearchServiceError(Exception):
    """Raised when the search or embedding service fails."""


# ---------------------------------------------------------------------------
# Client helpers
# ---------------------------------------------------------------------------


_cached_search_credential: DefaultAzureCredential | None = None
_cached_search_client: SearchClient | None = None
_cached_ai_client = None


def _get_search_credential() -> DefaultAzureCredential:
    """Return a cached DefaultAzureCredential for AI Search access."""
    global _cached_search_credential
    if _cached_search_credential is None:
        _cached_search_credential = DefaultAzureCredential()
    return _cached_search_credential


def _get_search_client() -> SearchClient:
    """Return a cached ``SearchClient`` pointed at the golden-tags index."""
    global _cached_search_client
    if _cached_search_client is not None:
        return _cached_search_client
    endpoint = os.environ.get("SEARCH_ENDPOINT", "")
    index_name = os.environ.get("SEARCH_INDEX_NAME", "golden-tags")
    if not endpoint:
        raise ValueError("SEARCH_ENDPOINT environment variable must be set")
    _cached_search_client = SearchClient(
        endpoint=endpoint,
        index_name=index_name,
        credential=_get_search_credential(),
    )
    return _cached_search_client


_cached_ai_client = None


def _get_ai_client():
    """Return a cached OpenAI-compatible client via Azure AI Foundry."""
    global _cached_ai_client
    if _cached_ai_client is not None:
        return _cached_ai_client
    from azure.ai.projects import AIProjectClient

    project_endpoint = os.environ.get("PROJECT_ENDPOINT", "")
    if not project_endpoint:
        raise ValueError("PROJECT_ENDPOINT environment variable must be set")

    project = AIProjectClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential(),
    )
    _cached_ai_client = project.get_openai_client()
    return _cached_ai_client


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------


def _generate_query_embedding(text: str) -> list[float]:
    """Generate a single embedding vector for *text*."""
    deployment = os.environ.get("PROJECT_EMBEDDING_DEPLOYMENT", "")
    if not deployment:
        raise ValueError("PROJECT_EMBEDDING_DEPLOYMENT environment variable must be set")
    try:
        client = _get_ai_client()
        response = client.embeddings.create(model=deployment, input=[text])
        return response.data[0].embedding
    except (HttpResponseError, ServiceRequestError) as exc:
        raise SearchServiceError(f"Embedding generation failed: {exc}") from exc


# ---------------------------------------------------------------------------
# AI extraction
# ---------------------------------------------------------------------------


def _format_matches_for_prompt(matches: list[AutoFillMatch]) -> str:
    """Format search matches as context for the LLM prompt."""
    if not matches:
        return "No similar tags found in the registry."
    lines = []
    for m in matches:
        lines.append(
            f"- {m.tagName} (score: {m.score:.2f}): {m.description} "
            f"[site={m.site}, line={m.line}, equip={m.equipment}, "
            f"unit={m.unit}, datatype={m.datatype}]"
        )
    return "\n".join(lines)


def _extract_structured_fields(
    query: str,
    matches: list[AutoFillMatch],
) -> dict:
    """Use Mistral-Large-3 via AIProjectClient to extract structured fields.

    Returns a dict with keys: site, line, equipment, unit, datatype, name,
    description, criticality.  Values are strings or ``None``.
    On any failure, returns an empty dict (caller falls back gracefully).
    """
    deployment = os.environ.get("PROJECT_CHAT_DEPLOYMENT", "")
    if not deployment:
        logger.warning("PROJECT_CHAT_DEPLOYMENT not set — skipping AI extraction")
        return {}

    matches_context = _format_matches_for_prompt(matches)

    user_msg = (
        f"User query: {query}\n\n"
        f"Similar tags from the registry:\n{matches_context}"
    )

    try:
        client = _get_ai_client()
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": _AUTOFILL_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.1,
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if the model wraps its response
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            raw = raw.rsplit("```", 1)[0]
        extracted: dict = json.loads(raw)

        return extracted
    except Exception:
        logger.exception("AI extraction failed — falling back to search-only results")
        return {}


# ---------------------------------------------------------------------------
# Main query function
# ---------------------------------------------------------------------------


async def auto_fill_tag(
    query: str,
    top_k: int = 1,
) -> AutoFillResult:
    """Return AI-extracted tag fields using hybrid search + LLM.

    Generates an embedding from the user's free-text *query* and executes a
    hybrid search (keyword text + semantic vector, no OData filters) against
    the ``golden-tags`` Azure AI Search index.

    The top matches are then passed to Mistral-Large-3 along with the
    user's query to extract structured form fields (site, line, equipment,
    unit, datatype, tag name, criticality, etc.).

    Raises:
        SearchServiceError: If the embedding or search API call fails.
        ValueError: If required environment variables are missing.
    """
    # 1. Generate embedding
    embedding = _generate_query_embedding(query)

    # 2. Build vector query
    vector_query = VectorizedQuery(
        vector=embedding,
        k_nearest_neighbors=top_k,
        fields="semanticVector",
    )

    # 3. Execute hybrid search (keyword + vector, no OData filter)
    try:
        client = _get_search_client()
        results = client.search(
            search_text=query,
            vector_queries=[vector_query],
            select=_SELECT_FIELDS,
            top=top_k,
        )

        matches: list[AutoFillMatch] = []
        for result in results:
            matches.append(
                AutoFillMatch(
                    tagName=result["tagName"],
                    description=result.get("description", ""),
                    score=result["@search.score"],
                    site=result.get("site", ""),
                    line=result.get("line", ""),
                    equipment=result.get("equipment", ""),
                    unit=result.get("unit", ""),
                    datatype=result.get("datatype", ""),
                )
            )
    except (HttpResponseError, ServiceRequestError) as exc:
        raise SearchServiceError(f"Search query failed: {exc}") from exc

    # 4. AI extraction
    extracted = _extract_structured_fields(query, matches)

    # 5. Build result
    confidence = matches[0].score if matches else 0.0

    return AutoFillResult(
        site=extracted.get("site"),
        line=extracted.get("line"),
        equipment=extracted.get("equipment"),
        unit=extracted.get("unit"),
        datatype=extracted.get("datatype"),
        name=extracted.get("name"),
        description=extracted.get("description"),
        criticality=extracted.get("criticality"),
        confidence=confidence,
        matches=matches,
    )
