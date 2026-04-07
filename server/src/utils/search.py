"""Azure AI Search + Foundry Agent client for tag auto-fill.

Self-contained module — queries the ``golden-tags`` Azure AI Search index
using hybrid search (keyword text + semantic embedding, no OData filters),
then invokes the ``tag-auto-fill`` Foundry Agent (gpt-4.1-mini with
function-calling tools) to clean and structure the result.

Agent tools (``get_available_sites``, ``get_available_lines``) are fulfilled
by direct Cosmos DB queries against the ``assets`` container.

Required environment variables (loaded by ``main.py`` via ``dotenv``):
    SEARCH_ENDPOINT, SEARCH_INDEX_NAME,
    PROJECT_ENDPOINT, PROJECT_EMBEDDING_DEPLOYMENT,
    PROJECT_CHAT_DEPLOYMENT
Optional:
    SEARCH_API_KEY  — falls back to DefaultAzureCredential when unset.
    AUTOFILL_AGENT_NAME — defaults to ``tag-auto-fill``.
"""

import asyncio
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

AGENT_NAME = "tag-auto-fill"
_MAX_TOOL_ITERATIONS = 3


class SearchServiceError(Exception):
    """Raised when the search or embedding service fails."""


# ---------------------------------------------------------------------------
# Client helpers
# ---------------------------------------------------------------------------


_cached_search_credential: DefaultAzureCredential | None = None
_cached_search_client: SearchClient | None = None
_cached_openai_client = None
_cached_agent_client = None


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
    """Return a cached OpenAI client for embeddings (account-level endpoint)."""
    global _cached_openai_client
    if _cached_openai_client is not None:
        return _cached_openai_client
    from azure.ai.projects import AIProjectClient

    # Embeddings are deployed at the account level, not the project level.
    # AI_SERVICES_ENDPOINT is the account-level endpoint; fall back to
    # stripping the /api/projects/* suffix from PROJECT_ENDPOINT.
    endpoint = os.environ.get("AI_SERVICES_ENDPOINT", "")
    if not endpoint:
        project_endpoint = os.environ.get("PROJECT_ENDPOINT", "")
        if not project_endpoint:
            raise ValueError("AI_SERVICES_ENDPOINT or PROJECT_ENDPOINT must be set")
        endpoint = project_endpoint.split("/api/projects/")[0]

    project = AIProjectClient(
        endpoint=endpoint,
        credential=DefaultAzureCredential(),
    )
    _cached_openai_client = project.get_openai_client()
    return _cached_openai_client


def _get_agent_client():
    """Return a cached OpenAI client for agent calls (project-scoped endpoint)."""
    global _cached_agent_client
    if _cached_agent_client is not None:
        return _cached_agent_client
    from azure.ai.projects import AIProjectClient

    project_endpoint = os.environ.get("PROJECT_ENDPOINT", "")
    if not project_endpoint:
        raise ValueError("PROJECT_ENDPOINT environment variable must be set")

    project = AIProjectClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential(),
    )
    _cached_agent_client = project.get_openai_client()
    return _cached_agent_client


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
    """Execute a function tool by querying Cosmos DB directly.

    Replaces the previous Azure Functions HTTP calls with direct DB access
    via ``get_container("assets")`` to avoid cold-start timeouts.
    """
    from src.utils.db import get_container

    try:
        args = json.loads(arguments) if arguments else {}

        if name == "get_available_sites":
            container = get_container("assets")
            results = list(container.query_items(
                query="SELECT DISTINCT c.site FROM c",
                enable_cross_partition_query=True,
            ))
            site_code_map = {
                "Plant-Luxembourg": "LUX",
                "Plant-Brussels": "BEL",
                "Plant-Amsterdam": "NED",
            }
            sites = []
            for row in results:
                display = row["site"]
                code = site_code_map.get(display, display[:3].upper())
                sites.append({"display": display, "code": code})
            sites.sort(key=lambda s: s["display"])
            return json.dumps(sites)

        if name == "get_available_lines":
            site = args.get("site", "")
            container = get_container("assets")
            results = list(container.query_items(
                query="SELECT DISTINCT c.line FROM c WHERE c.site = @site",
                parameters=[{"name": "@site", "value": site}],
                partition_key=site,
            ))
            lines = []
            for row in results:
                display = row["line"]
                code = display.replace("Line-", "L")
                lines.append({"display": display, "code": code})
            lines.sort(key=lambda l: l["display"])
            return json.dumps(lines)

        if name == "get_available_equipment":
            site = args.get("site", "")
            line = args.get("line", "")
            container = get_container("assets")
            results = list(container.query_items(
                query=(
                    "SELECT DISTINCT c.equipment FROM c"
                    " WHERE c.site = @site AND c.line = @line"
                ),
                parameters=[
                    {"name": "@site", "value": site},
                    {"name": "@line", "value": line},
                ],
                partition_key=site,
            ))
            equipment = [{"display": r["equipment"]} for r in results]
            equipment.sort(key=lambda e: e["display"])
            return json.dumps(equipment)

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

        client = _get_agent_client()

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
# Search execution with retry on stale SSL connections
# ---------------------------------------------------------------------------


def _execute_search(
    query: str,
    vector_query: VectorizedQuery,
    top_k: int,
) -> list[AutoFillMatch]:
    """Run the hybrid search, retrying once with a fresh client on SSL errors."""
    global _cached_search_client

    for attempt in range(2):
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
            return matches
        except (HttpResponseError, ServiceRequestError) as exc:
            if attempt == 0:
                logger.warning("Search failed (attempt 1), retrying with fresh client: %s", exc)
                _cached_search_client = None
                continue
            raise SearchServiceError(f"Search query failed: {exc}") from exc

    return []  # unreachable, but satisfies type checker


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
    # 0. Normalise query to English (non-blocking — falls back to original)
    from src.utils.translate import normalise_to_english as _translate
    translate_result = await _translate(query)
    normalised_query = translate_result.text

    # 1. Generate embedding (from normalised text)
    embedding = _generate_query_embedding(normalised_query)

    # 2. Build vector query
    vector_query = VectorizedQuery(
        vector=embedding,
        k_nearest_neighbors=top_k,
        fields="semanticVector",
    )

    # 3. Execute hybrid search (keyword + vector, no OData filter)
    #    Run the sync SearchClient off the event loop and retry once on
    #    transient SSL errors (stale cached connection).
    matches = await asyncio.to_thread(
        _execute_search, normalised_query, vector_query, top_k,
    )

    # 4. Agent extraction (sync HTTP calls — run off the event loop)
    extracted = await asyncio.to_thread(_extract_structured_fields, normalised_query, matches)

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
