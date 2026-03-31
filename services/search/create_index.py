"""Create the ``golden-tags`` Azure AI Search index.

Defines the index schema with vector search (HNSW, 3072 dims, cosine) for
the ``text-embedding-3-large`` model.  Run once to create or update the
index definition — it does **not** populate documents.

Usage:
    cd services
    uv run python -m search.create_index
"""

import logging
import os
from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SearchableField,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)
from dotenv import load_dotenv

_repo_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_repo_root / "services" / ".env")

logger = logging.getLogger("search.create_index")
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

SEARCH_ENDPOINT = os.environ.get("SEARCH_ENDPOINT", "")
SEARCH_API_KEY = os.environ.get("SEARCH_API_KEY", "")
SEARCH_INDEX_NAME = os.environ.get("SEARCH_INDEX_NAME", "golden-tags")

VECTOR_DIMENSIONS = 3072  # text-embedding-3-large


def _get_credential():
    """Return AzureKeyCredential if SEARCH_API_KEY is set, else DefaultAzureCredential."""
    if SEARCH_API_KEY:
        from azure.core.credentials import AzureKeyCredential

        logger.info("Using API key credential (SEARCH_API_KEY is set)")
        return AzureKeyCredential(SEARCH_API_KEY)
    logger.info("Using DefaultAzureCredential (managed identity)")
    return DefaultAzureCredential()


def build_index() -> SearchIndex:
    """Build the ``golden-tags`` index definition."""

    fields: list[SearchField] = [
        # --- Key ---
        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
            filterable=False,
        ),
        # --- Searchable text fields ---
        SearchableField(
            name="tagName",
            type=SearchFieldDataType.String,
            retrievable=True,
        ),
        SearchableField(
            name="description",
            type=SearchFieldDataType.String,
            retrievable=True,
        ),
        SearchableField(
            name="measurementTokens",
            type=SearchFieldDataType.String,
            retrievable=True,
        ),
        SearchableField(
            name="synonyms",
            type=SearchFieldDataType.String,
            retrievable=True,
        ),
        # --- Filterable metadata ---
        SimpleField(
            name="site",
            type=SearchFieldDataType.String,
            filterable=True,
            retrievable=True,
        ),
        SimpleField(
            name="line",
            type=SearchFieldDataType.String,
            filterable=True,
            retrievable=True,
        ),
        SimpleField(
            name="equipment",
            type=SearchFieldDataType.String,
            filterable=True,
            retrievable=True,
        ),
        SimpleField(
            name="unit",
            type=SearchFieldDataType.String,
            filterable=True,
            retrievable=True,
        ),
        SimpleField(
            name="datatype",
            type=SearchFieldDataType.String,
            filterable=True,
            retrievable=True,
        ),
        # --- Semantic / vector fields (not retrievable) ---
        SimpleField(
            name="semanticText",
            type=SearchFieldDataType.String,
            searchable=False,
            filterable=False,
            hidden=True,
        ),
        SearchField(
            name="semanticVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            hidden=True,
            vector_search_dimensions=VECTOR_DIMENSIONS,
            vector_search_profile_name="hnsw-profile",
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="hnsw-config",
                parameters=HnswParameters(metric="cosine"),
            ),
        ],
        profiles=[
            VectorSearchProfile(
                name="hnsw-profile",
                algorithm_configuration_name="hnsw-config",
            ),
        ],
    )

    return SearchIndex(
        name=SEARCH_INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
    )


def create_or_update_index() -> None:
    """Create or update the golden-tags index in Azure AI Search."""
    if not SEARCH_ENDPOINT:
        raise ValueError("SEARCH_ENDPOINT must be set")

    client = SearchIndexClient(
        endpoint=SEARCH_ENDPOINT,
        credential=_get_credential(),
    )
    index = build_index()
    result = client.create_or_update_index(index)
    print(f"  ✔ Index '{result.name}' created/updated successfully")


if __name__ == "__main__":
    create_or_update_index()
