"""Cosmos DB setup utilities — container creation and database initialisation.

This module is used locally during development, NOT at server runtime.
The server assumes containers already exist.
"""

import logging
import os

from azure.cosmos import CosmosClient, DatabaseProxy, PartitionKey

logger = logging.getLogger("cosmos.setup")

COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT", "")
COSMOS_KEY = os.environ.get("COSMOS_KEY", "")
COSMOS_DATABASE = os.environ.get("COSMOS_DATABASE", "ot-tag-registry")

CONTAINERS: dict[str, str] = {
    "assets": "/site",
    "tags": "/assetId",
    "sources": "/systemType",
    "l1Rules": "/tagId",
    "l2Rules": "/tagId",
}


def get_cosmos_client() -> CosmosClient:
    """Create and return a Cosmos DB client, validating env vars first."""
    if not COSMOS_ENDPOINT or not COSMOS_KEY:
        logger.error(
            "COSMOS_ENDPOINT and COSMOS_KEY must be set (endpoint=%r)",
            COSMOS_ENDPOINT,
        )
        raise ValueError("COSMOS_ENDPOINT and COSMOS_KEY must be set")
    try:
        client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)
        return client
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
