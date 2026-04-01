"""Suggest tag names via hybrid vector search against the ``golden-tags`` index.

Combines OData hard filters (site, line, equipment) with a vector query
generated from the user's free-text description to return ranked tag-name
suggestions.

Prerequisites:
    1. The ``golden-tags`` index must exist (run ``create_index.py``).
    2. The index must be seeded (run ``seed_index.py``).
    3. Environment variables in ``services/.env``:
       SEARCH_ENDPOINT, SEARCH_API_KEY (optional), SEARCH_INDEX_NAME,
       PROJECT_ENDPOINT, PROJECT_EMBEDDING_DEPLOYMENT

Usage (standalone test)::

    cd services
    uv run python -m search.suggest_name
"""

import logging
import os
from pathlib import Path

from azure.core.exceptions import HttpResponseError, ServiceRequestError
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from dotenv import load_dotenv
from pydantic import BaseModel

_repo_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_repo_root / "services" / ".env")

logger = logging.getLogger("search.suggest_name")
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

SEARCH_ENDPOINT = os.environ.get("SEARCH_ENDPOINT", "")
SEARCH_INDEX_NAME = os.environ.get("SEARCH_INDEX_NAME", "golden-tags")
PROJECT_ENDPOINT = os.environ.get("PROJECT_ENDPOINT", "")
PROJECT_EMBEDDING_DEPLOYMENT = os.environ.get("PROJECT_EMBEDDING_DEPLOYMENT", "")

_SELECT_FIELDS = [
    "tagName",
    "description",
    "site",
    "line",
    "equipment",
    "unit",
    "datatype",
]


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


class SuggestionMatch(BaseModel):
    """A single search hit with its relevance score."""

    tagName: str
    description: str
    score: float
    site: str
    line: str
    equipment: str
    unit: str
    datatype: str


class SuggestionResult(BaseModel):
    """Ranked suggestions returned by :func:`suggest_tag_name`."""

    suggestedName: str
    alternatives: list[str]
    matches: list[SuggestionMatch]


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class SearchServiceError(Exception):
    """Raised when the search or embedding service fails."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_search_credential():
    """Return DefaultAzureCredential for AI Search access."""
    return DefaultAzureCredential()


def _get_search_client() -> SearchClient:
    """Return a ``SearchClient`` pointed at the golden-tags index."""
    if not SEARCH_ENDPOINT:
        raise ValueError("SEARCH_ENDPOINT must be set")
    return SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=SEARCH_INDEX_NAME,
        credential=_get_search_credential(),
    )


def _get_embeddings_client():
    """Return an Azure AI Foundry embeddings client."""
    from azure.ai.projects import AIProjectClient

    if not PROJECT_ENDPOINT:
        raise ValueError("PROJECT_ENDPOINT must be set for embedding generation")
    if not PROJECT_EMBEDDING_DEPLOYMENT:
        raise ValueError("PROJECT_EMBEDDING_DEPLOYMENT must be set")

    project = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    )
    return project.inference.get_embeddings_client()


def _build_odata_filter(
    site: str,
    line: str,
    equipment: str | None = None,
) -> str:
    """Build an OData filter string from the hard filter parameters."""
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
    try:
        client = _get_embeddings_client()
        response = client.embed(
            model=PROJECT_EMBEDDING_DEPLOYMENT,
            input=[text],
        )
        return response.data[0].embedding
    except (HttpResponseError, ServiceRequestError) as exc:
        raise SearchServiceError(f"Embedding generation failed: {exc}") from exc


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
            matches=[],
        )

    return SuggestionResult(
        suggestedName=matches[0].tagName,
        alternatives=[m.tagName for m in matches[1:]],
        matches=matches,
    )


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import asyncio

    async def _demo():
        result = await suggest_tag_name(
            site="LUX",
            line="L1",
            description="outlet pressure of primary coolant pump",
            equipment="PMP001",
            unit="bar",
        )
        print(f"\nSuggested: {result.suggestedName}")
        print(f"Alternatives: {result.alternatives}")
        for m in result.matches:
            print(f"  {m.score:.4f}  {m.tagName}  —  {m.description}")

    asyncio.run(_demo())
