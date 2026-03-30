import logging
import os

from azure.cosmos import CosmosClient, DatabaseProxy

logger = logging.getLogger("cosmos.config")

COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT", "")
COSMOS_KEY = os.environ.get("COSMOS_KEY", "")
COSMOS_DATABASE = os.environ.get("COSMOS_DATABASE", "ot-tag-registry")


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


def get_database(client: CosmosClient | None = None) -> DatabaseProxy:
    if client is None:
        client = get_cosmos_client()
    return client.get_database_client(COSMOS_DATABASE)


def get_container(container_name: str, client: CosmosClient | None = None):
    db = get_database(client)
    return db.get_container_client(container_name)
