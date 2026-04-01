"""Azure AI Search + embeddings client for tag-name suggestions.

Self-contained module — queries the ``golden-tags`` Azure AI Search index
using hybrid vector search (OData hard filters + semantic embedding) to
return ranked tag-name suggestions.

Required environment variables (loaded by ``main.py`` via ``dotenv``):
    SEARCH_ENDPOINT, SEARCH_INDEX_NAME,
    PROJECT_ENDPOINT, PROJECT_EMBEDDING_DEPLOYMENT
Optional:
    SEARCH_API_KEY  — falls back to DefaultAzureCredential when unset.
"""

import logging
import os

from azure.core.exceptions import HttpResponseError, ServiceRequestError
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

from src.models.suggest_name import SuggestionMatch, SuggestionResult

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


class SearchServiceError(Exception):
    """Raised when the search or embedding service fails."""


# ---------------------------------------------------------------------------
# Client helpers
# ---------------------------------------------------------------------------


def _get_search_credential():
    """Return DefaultAzureCredential for AI Search access."""
    return DefaultAzureCredential()


def _get_search_client() -> SearchClient:
    """Return a ``SearchClient`` pointed at the golden-tags index."""
    endpoint = os.environ.get("SEARCH_ENDPOINT", "")
    index_name = os.environ.get("SEARCH_INDEX_NAME", "golden-tags")
    if not endpoint:
        raise ValueError("SEARCH_ENDPOINT environment variable must be set")
    return SearchClient(
        endpoint=endpoint,
        index_name=index_name,
        credential=_get_search_credential(),
    )


def _get_embeddings_client():
    """Return an Azure AI Foundry embeddings client."""
    from azure.ai.projects import AIProjectClient

    project_endpoint = os.environ.get("PROJECT_ENDPOINT", "")
    if not project_endpoint:
        raise ValueError("PROJECT_ENDPOINT environment variable must be set")
    deployment = os.environ.get("PROJECT_EMBEDDING_DEPLOYMENT", "")
    if not deployment:
        raise ValueError("PROJECT_EMBEDDING_DEPLOYMENT environment variable must be set")

    project = AIProjectClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential(),
    )
    return project.inference.get_embeddings_client()


# ---------------------------------------------------------------------------
# Query construction helpers
# ---------------------------------------------------------------------------


def _build_odata_filter(
    site: str,
    line: str,
    equipment: str | None = None,
) -> str:
    """Build an OData filter string from hard-filter parameters."""
    clauses = [f"site eq '{site}'", f"line eq '{line}'"]
    if equipment:
        clauses.append(f"equipment eq '{equipment}'")
    return " and ".join(clauses)


def _build_query_text(
    description: str,
    unit: str | None = None,
    datatype: str | None = None,
) -> str:
    """Combine free-text inputs into a single string for embedding."""
    parts = [description]
    if unit:
        parts.append(unit)
    if datatype:
        parts.append(datatype)
    return " ".join(parts)


def _generate_query_embedding(text: str) -> list[float]:
    """Generate a single embedding vector for *text*."""
    deployment = os.environ.get("PROJECT_EMBEDDING_DEPLOYMENT", "")
    try:
        client = _get_embeddings_client()
        response = client.embed(model=deployment, input=[text])
        return response.data[0].embedding
    except (HttpResponseError, ServiceRequestError) as exc:
        raise SearchServiceError(f"Embedding generation failed: {exc}") from exc


def _build_evidence(
    request_description: str,
    top_match: SuggestionMatch,
) -> str:
    """Build a human-readable evidence string from the top match."""
    return (
        f"Similar to tag '{top_match.tagName}' — "
        f"same site/line, description match on "
        f"'{request_description}' ↔ '{top_match.description}' "
        f"({top_match.score:.2f} similarity)"
    )


# ---------------------------------------------------------------------------
# Main query function
# ---------------------------------------------------------------------------


async def suggest_tag_name(
    site: str,
    line: str,
    description: str,
    equipment: str | None = None,
    unit: str | None = None,
    datatype: str | None = None,
    top_k: int = 5,
) -> SuggestionResult:
    """Return ranked tag-name suggestions using hybrid vector search.

    Builds an OData filter from *site*, *line*, and optional *equipment*,
    generates an embedding from the free-text *description* (plus optional
    *unit* / *datatype*), and executes a hybrid vector + filter query
    against the ``golden-tags`` Azure AI Search index.

    Returns a :class:`SuggestionResult` with the best match as
    ``suggestedName`` and remaining matches as ``alternatives``.

    Raises:
        SearchServiceError: If the embedding or search API call fails.
        ValueError: If required environment variables are missing.
    """
    odata_filter = _build_odata_filter(site, line, equipment)
    query_text = _build_query_text(description, unit, datatype)

    # 1. Generate embedding
    embedding = _generate_query_embedding(query_text)

    # 2. Build vector query
    vector_query = VectorizedQuery(
        vector=embedding,
        k_nearest_neighbors=top_k,
        fields="semanticVector",
    )

    # 3. Execute hybrid search
    try:
        client = _get_search_client()
        results = client.search(
            search_text=query_text,
            vector_queries=[vector_query],
            filter=odata_filter,
            select=_SELECT_FIELDS,
            top=top_k,
        )

        matches: list[SuggestionMatch] = []
        for result in results:
            matches.append(
                SuggestionMatch(
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

    # 4. Build result
    if not matches:
        return SuggestionResult(
            suggestedName="",
            alternatives=[],
            evidence="",
            matches=[],
        )

    return SuggestionResult(
        suggestedName=matches[0].tagName,
        alternatives=[m.tagName for m in matches[1:]],
        evidence=_build_evidence(description, matches[0]),
        matches=matches,
    )
