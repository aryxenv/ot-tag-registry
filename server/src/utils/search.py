"""Azure AI Search + Foundry Agent client for tag auto-fill.

Self-contained module — queries the ``golden-tags`` Azure AI Search index
using hybrid search (keyword text + semantic embedding, no OData filters),
then invokes the ``tag-auto-fill`` Foundry Agent (gpt-4.1-mini with
function-calling tools) to clean and structure the result.

Required environment variables (loaded by ``main.py`` via ``dotenv``):
    SEARCH_ENDPOINT, SEARCH_INDEX_NAME,
    PROJECT_ENDPOINT, PROJECT_EMBEDDING_DEPLOYMENT,
    PROJECT_CHAT_DEPLOYMENT, FUNCTION_APP_URL
Optional:
    SEARCH_API_KEY  — falls back to DefaultAzureCredential when unset.
    AUTOFILL_AGENT_NAME — defaults to ``tag-auto-fill``.
"""

import json
import logging
import os

import httpx
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

AGENT_NAME = "tag-auto-fill"
_MAX_TOOL_ITERATIONS = 3


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
# Agent tool execution
# ---------------------------------------------------------------------------


def _execute_tool(name: str, arguments: str) -> str:
    """Execute a function tool by calling the Azure Functions HTTP endpoint."""
    func_url = os.environ.get("FUNCTION_APP_URL", "")
    if not func_url:
        return json.dumps({"error": "FUNCTION_APP_URL not configured"})

    try:
        args = json.loads(arguments) if arguments else {}

        if name == "get_available_sites":
            resp = httpx.get(f"{func_url}/api/get-sites", timeout=10)
            resp.raise_for_status()
            return resp.text

        if name == "get_available_lines":
            site = args.get("site", "")
            resp = httpx.get(
                f"{func_url}/api/get-lines",
                params={"site": site},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.text

        return json.dumps({"error": f"Unknown tool: {name}"})
    except Exception as exc:
        logger.warning("Tool %s failed: %s", name, exc)
        return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# AI extraction via Foundry Agent
# ---------------------------------------------------------------------------


def _format_matches_for_prompt(matches: list[AutoFillMatch]) -> str:
    """Format search matches as context for the agent prompt."""
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
    """Invoke the Foundry Agent to clean and structure the search result.

    Uses the ``tag-auto-fill`` agent (gpt-4.1-mini with function-calling
    tools).  The agent may call ``get_available_sites`` /
    ``get_available_lines`` via Azure Functions to validate site/line.

    Returns a dict with keys: site, line, equipment, unit, datatype, name,
    description, criticality.  Values are strings or ``None``.
    On any failure, returns an empty dict (caller falls back gracefully).
    """
    agent_name = os.environ.get("AUTOFILL_AGENT_NAME", AGENT_NAME)
    if not os.environ.get("PROJECT_CHAT_DEPLOYMENT"):
        logger.warning("PROJECT_CHAT_DEPLOYMENT not set — skipping agent extraction")
        return {}

    matches_context = _format_matches_for_prompt(matches)
    user_msg = (
        f"User query: {query}\n\n"
        f"Closest matching tag from the registry:\n{matches_context}"
    )

    try:
        from openai.types.responses.response_input_param import (
            FunctionCallOutput,
        )

        client = _get_ai_client()

        # First call: send query + match context to the agent
        response = client.responses.create(
            input=user_msg,
            extra_body={
                "agent_reference": {"name": agent_name, "type": "agent_reference"},
            },
        )

        # Tool-calling loop: handle function calls from the agent
        for _ in range(_MAX_TOOL_ITERATIONS):
            tool_outputs = []
            for item in response.output:
                if item.type == "function_call":
                    result = _execute_tool(item.name, item.arguments)
                    tool_outputs.append(
                        FunctionCallOutput(
                            type="function_call_output",
                            call_id=item.call_id,
                            output=result,
                        )
                    )

            if not tool_outputs:
                break

            # Submit tool results and get next response
            response = client.responses.create(
                input=tool_outputs,
                previous_response_id=response.id,
                extra_body={
                    "agent_reference": {"name": agent_name, "type": "agent_reference"},
                },
            )

        # Parse the final text response as JSON
        raw = response.output_text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            raw = raw.rsplit("```", 1)[0]
        return json.loads(raw)

    except Exception:
        logger.exception("Agent extraction failed — falling back to search-only results")
        return {}


# ---------------------------------------------------------------------------
# Main query function
# ---------------------------------------------------------------------------


async def auto_fill_tag(
    query: str,
    top_k: int = 1,
) -> AutoFillResult:
    """Return AI-extracted tag fields using hybrid search + Foundry Agent.

    Generates an embedding from the user's free-text *query* and executes a
    hybrid search (keyword text + semantic vector, no OData filters) against
    the ``golden-tags`` Azure AI Search index.

    The top match is then passed to the ``tag-auto-fill`` Foundry Agent
    (gpt-4.1-mini) which cleans and validates the result against the user's
    query, optionally calling Azure Functions to look up valid sites/lines.

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

    # 4. Agent extraction
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
