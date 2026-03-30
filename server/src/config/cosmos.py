import os

from azure.cosmos import CosmosClient, PartitionKey

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
    return CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)


def get_database(client: CosmosClient | None = None):
    if client is None:
        client = get_cosmos_client()
    return client.get_database_client(COSMOS_DATABASE)


def get_container(container_name: str, client: CosmosClient | None = None):
    db = get_database(client)
    return db.get_container_client(container_name)


def ensure_containers(client: CosmosClient | None = None):
    """Create database and all containers if they don't exist."""
    if client is None:
        client = get_cosmos_client()
    db = client.create_database_if_not_exists(COSMOS_DATABASE)
    for name, pk_path in CONTAINERS.items():
        db.create_container_if_not_exists(
            id=name,
            partition_key=PartitionKey(path=pk_path),
        )
    return db
