"""Seed the ``golden-tags`` Azure AI Search index with embeddings.

Reads the curated golden-tag dataset, generates vector embeddings via
Azure AI Foundry (``text-embedding-3-large``), and uploads documents to
the index.

Prerequisites:
    1. Run ``create_index.py`` first to create the index schema.
    2. Set environment variables in ``services/.env``:
       SEARCH_ENDPOINT, SEARCH_INDEX_NAME,
       PROJECT_ENDPOINT, PROJECT_EMBEDDING_DEPLOYMENT

Usage:
    cd services
    uv run python -m search.seed_index
"""

import logging
import os
from pathlib import Path
from uuid import uuid4

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv

_repo_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_repo_root / "services" / ".env")

logger = logging.getLogger("search.seed_index")
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

SEARCH_ENDPOINT = os.environ.get("SEARCH_ENDPOINT", "")
SEARCH_INDEX_NAME = os.environ.get("SEARCH_INDEX_NAME", "golden-tags")
PROJECT_ENDPOINT = os.environ.get("PROJECT_ENDPOINT", "")
PROJECT_EMBEDDING_DEPLOYMENT = os.environ.get("PROJECT_EMBEDDING_DEPLOYMENT", "")

# Maximum texts per embedding API call
_EMBED_BATCH_SIZE = 16


def _get_search_credential():
    """Return DefaultAzureCredential for AI Search access."""
    return DefaultAzureCredential()


def _get_openai_client():
    """Return an OpenAI client authenticated via Azure AI Foundry."""
    from azure.ai.projects import AIProjectClient

    if not PROJECT_ENDPOINT:
        raise ValueError("PROJECT_ENDPOINT must be set for embedding generation")
    if not PROJECT_EMBEDDING_DEPLOYMENT:
        raise ValueError("PROJECT_EMBEDDING_DEPLOYMENT must be set")

    project = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    )
    return project.get_openai_client()


def _build_semantic_text(tag: dict) -> str:
    """Combine description, measurement tokens, synonyms, and unit into a
    single text blob for embedding."""
    parts = [
        tag.get("description", ""),
        tag.get("measurementTokens", ""),
        tag.get("synonyms", ""),
        tag.get("unit", ""),
    ]
    return " ".join(p for p in parts if p)


def _generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts using Azure AI Foundry.

    Batches requests to respect API limits.
    """
    client = _get_openai_client()
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), _EMBED_BATCH_SIZE):
        batch = texts[i : i + _EMBED_BATCH_SIZE]
        response = client.embeddings.create(
            model=PROJECT_EMBEDDING_DEPLOYMENT,
            input=batch,
        )
        for item in response.data:
            all_embeddings.append(item.embedding)
        logger.info(
            "  Embedded batch %d–%d of %d",
            i + 1,
            min(i + _EMBED_BATCH_SIZE, len(texts)),
            len(texts),
        )

    return all_embeddings


def seed() -> None:
    """Generate embeddings and upload all golden tags to the search index."""
    from search.golden_tags import GOLDEN_TAGS

    if not SEARCH_ENDPOINT:
        raise ValueError("SEARCH_ENDPOINT must be set")

    print(f"\n📦 Seeding {len(GOLDEN_TAGS)} golden tags into '{SEARCH_INDEX_NAME}'…\n")

    # 1. Build semantic text for each tag
    semantic_texts = [_build_semantic_text(tag) for tag in GOLDEN_TAGS]
    print(f"  ✔ Built semantic text for {len(semantic_texts)} tags")

    # 2. Generate embeddings
    print("  ⏳ Generating embeddings (this may take a moment)…")
    embeddings = _generate_embeddings(semantic_texts)
    print(f"  ✔ Generated {len(embeddings)} embeddings ({len(embeddings[0])} dimensions)")

    # 3. Build search documents
    documents = []
    for tag, sem_text, embedding in zip(GOLDEN_TAGS, semantic_texts, embeddings):
        doc = {
            "id": str(uuid4()),
            "tagName": tag["tagName"],
            "site": tag["site"],
            "line": tag["line"],
            "equipment": tag["equipment"],
            "unit": tag["unit"],
            "datatype": tag["datatype"],
            "description": tag["description"],
            "measurementTokens": tag["measurementTokens"],
            "synonyms": tag["synonyms"],
            "semanticText": sem_text,
            "semanticVector": embedding,
        }
        documents.append(doc)

    # 4. Upload to index
    print("  ⏳ Uploading documents to index…")
    search_client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=SEARCH_INDEX_NAME,
        credential=_get_search_credential(),
    )
    result = search_client.upload_documents(documents)

    succeeded = sum(1 for r in result if r.succeeded)
    failed = sum(1 for r in result if not r.succeeded)

    print(f"  ✔ Upload complete: {succeeded} succeeded, {failed} failed")

    if failed:
        for r in result:
            if not r.succeeded:
                print(f"  ✘ {r.key}: {r.error_message}")

    print(f"\n✅ Index '{SEARCH_INDEX_NAME}' seeded with {succeeded} golden tags\n")


if __name__ == "__main__":
    seed()
