"""Cosmos DB setup utilities — container creation and database initialisation.

This module is used locally during development, NOT at server runtime.
The server assumes containers already exist.
"""

import logging
import os

from azure.cosmos import CosmosClient, DatabaseProxy, PartitionKey
from azure.identity import DefaultAzureCredential

logger = logging.getLogger("cosmos.setup")

COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT", "")
COSMOS_DATABASE = os.environ.get("COSMOS_DATABASE", "ot-tag-registry")

CONTAINERS: dict[str, str] = {
    "assets": "/site",
    "tags": "/assetId",
    "sources": "/systemType",
    "l1Rules": "/tagId",
    "l2Rules": "/tagId",
}


_cached_credential: DefaultAzureCredential | None = None


def _get_credential() -> DefaultAzureCredential:
    """Return a cached DefaultAzureCredential instance."""
    global _cached_credential
    if _cached_credential is None:
        logger.info("Using DefaultAzureCredential (managed identity / Azure CLI)")
        _cached_credential = DefaultAzureCredential()
    return _cached_credential


def get_cosmos_client() -> CosmosClient:
    """Create and return a Cosmos DB client.

    Uses ``DefaultAzureCredential`` by default (managed identity in Azure,
    Azure CLI / VS Code locally).  Falls back to ``COSMOS_KEY`` if set.
    """
    if not COSMOS_ENDPOINT:
        logger.error("COSMOS_ENDPOINT must be set (endpoint=%r)", COSMOS_ENDPOINT)
        raise ValueError("COSMOS_ENDPOINT must be set")
    try:
        credential = _get_credential()
        return CosmosClient(COSMOS_ENDPOINT, credential=credential)
    except Exception as e:
        logger.error("Failed to connect to Cosmos DB at %s: %s", COSMOS_ENDPOINT, e)
        raise


def ensure_containers(client: CosmosClient | None = None) -> DatabaseProxy:
    """Create database and all containers if they don't exist."""
    if client is None:
        client = get_cosmos_client()
    db = client.create_database_if_not_exists(COSMOS_DATABASE)
    for name, pk_path in CONTAINERS.items():
        logger.info("Ensuring container '%s' with partition key '%s'", name, pk_path)
        db.create_container_if_not_exists(
            id=name,
            partition_key=PartitionKey(path=pk_path),
        )
    logger.info(
        "Database '%s' ready with %d containers", COSMOS_DATABASE, len(CONTAINERS)
    )
    return db
