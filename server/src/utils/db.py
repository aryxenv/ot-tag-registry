"""Cosmos DB runtime helpers — client connection, CRUD repository, and
per-container factory functions.

This module is the server's only touchpoint with Azure Cosmos DB.
Container *creation* and data *seeding* live in ``services/database/``.
"""

import logging
import os
from datetime import datetime, timezone

from azure.cosmos import ContainerProxy, CosmosClient, DatabaseProxy
from azure.cosmos.exceptions import (
    CosmosHttpResponseError,
    CosmosResourceNotFoundError,
)
from azure.identity import DefaultAzureCredential

# ---------------------------------------------------------------------------
# Cosmos client
# ---------------------------------------------------------------------------

logger = logging.getLogger("cosmos")

COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT", "")
COSMOS_KEY = os.environ.get("COSMOS_KEY", "")
COSMOS_DATABASE = os.environ.get("COSMOS_DATABASE", "ot-tag-registry")


_cached_credential: DefaultAzureCredential | str | None = None


def _get_credential() -> DefaultAzureCredential | str:
    """Return an API key if COSMOS_KEY is set, otherwise DefaultAzureCredential.

    The result is cached at module level so ``DefaultAzureCredential`` (which
    probes multiple providers on first use) is only instantiated once.
    """
    global _cached_credential
    if _cached_credential is None:
        if COSMOS_KEY:
            logger.info("Using API key credential (COSMOS_KEY is set)")
            _cached_credential = COSMOS_KEY
        else:
            logger.info("Using DefaultAzureCredential (managed identity)")
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


def get_database(client: CosmosClient | None = None) -> DatabaseProxy:
    if client is None:
        client = get_cosmos_client()
    return client.get_database_client(COSMOS_DATABASE)


def get_container(container_name: str, client: CosmosClient | None = None):
    db = get_database(client)
    return db.get_container_client(container_name)


# ---------------------------------------------------------------------------
# Generic CRUD repository
# ---------------------------------------------------------------------------


class CosmosRepository:
    """Generic CRUD helper wrapping an Azure Cosmos DB container.

    Every public method logs its operations and wraps Cosmos SDK calls
    in structured error handling.  Timestamps are always UTC ISO-8601.
    """

    def __init__(self, container_client: ContainerProxy) -> None:
        self._container: ContainerProxy = container_client
        self._logger: logging.Logger = logging.getLogger(
            f"cosmos.{container_client.id}"
        )

    def create(self, item: dict) -> dict:
        """Upsert *item* into the container and return the persisted document."""
        try:
            result: dict = self._container.upsert_item(body=item)
            self._logger.info("Created item id=%s", result.get("id"))
            return result
        except CosmosHttpResponseError as exc:
            self._logger.error(
                "Failed to create item: %s (status %s)", exc.message, exc.status_code
            )
            raise

    def get_by_id(self, item_id: str, partition_key: str) -> dict | None:
        """Point-read a single document.  Returns *None* on 404."""
        try:
            item: dict = self._container.read_item(
                item=item_id, partition_key=partition_key
            )
            self._logger.info("Read item id=%s", item_id)
            return item
        except CosmosResourceNotFoundError:
            self._logger.warning("Item id=%s not found", item_id)
            return None
        except CosmosHttpResponseError as exc:
            self._logger.error(
                "Failed to read item id=%s: %s (status %s)",
                item_id,
                exc.message,
                exc.status_code,
            )
            raise

    def get_all(self, partition_key: str | None = None) -> list[dict]:
        """Return every document in the container.

        If *partition_key* is provided the query is scoped to that single
        logical partition; otherwise a cross-partition fan-out is used.
        """
        query_str = "SELECT * FROM c"
        try:
            if partition_key is not None:
                items = list(
                    self._container.query_items(
                        query=query_str,
                        partition_key=partition_key,
                    )
                )
            else:
                items = list(
                    self._container.query_items(
                        query=query_str,
                        enable_cross_partition_query=True,
                    )
                )
            self._logger.info(
                "get_all returned %d items (partition_key=%s)",
                len(items),
                partition_key,
            )
            return items
        except CosmosHttpResponseError as exc:
            self._logger.error(
                "Failed to get_all: %s (status %s)", exc.message, exc.status_code
            )
            raise

    def query(
        self,
        query_str: str,
        parameters: list[dict] | None = None,
        partition_key: str | None = None,
    ) -> list[dict]:
        """Execute a parameterised SQL query and return matching documents."""
        try:
            kwargs: dict = {"query": query_str}
            if parameters is not None:
                kwargs["parameters"] = parameters
            if partition_key is not None:
                kwargs["partition_key"] = partition_key
            else:
                kwargs["enable_cross_partition_query"] = True

            items = list(self._container.query_items(**kwargs))
            self._logger.info(
                "query returned %d items for: %s", len(items), query_str
            )
            return items
        except CosmosHttpResponseError as exc:
            self._logger.error(
                "Query failed: %s (status %s)", exc.message, exc.status_code
            )
            raise

    def update(self, item_id: str, partition_key: str, updates: dict) -> dict:
        """Point-read the document, merge *updates* over it, and upsert back.

        ``updatedAt`` is always overwritten with the current UTC timestamp.
        """
        try:
            existing: dict = self._container.read_item(
                item=item_id, partition_key=partition_key
            )
        except CosmosResourceNotFoundError:
            self._logger.error("Cannot update – item id=%s not found", item_id)
            raise
        except CosmosHttpResponseError as exc:
            self._logger.error(
                "Failed to read item id=%s for update: %s (status %s)",
                item_id,
                exc.message,
                exc.status_code,
            )
            raise

        existing.update(updates)
        existing["updatedAt"] = datetime.now(timezone.utc).isoformat()

        try:
            result: dict = self._container.upsert_item(body=existing)
            self._logger.info("Updated item id=%s", item_id)
            return result
        except CosmosHttpResponseError as exc:
            self._logger.error(
                "Failed to upsert updated item id=%s: %s (status %s)",
                item_id,
                exc.message,
                exc.status_code,
            )
            raise

    def delete(self, item_id: str, partition_key: str) -> None:
        """Soft-delete: set ``status`` to ``retired`` and update timestamp."""
        try:
            existing: dict = self._container.read_item(
                item=item_id, partition_key=partition_key
            )
        except CosmosResourceNotFoundError:
            self._logger.error("Cannot delete – item id=%s not found", item_id)
            raise
        except CosmosHttpResponseError as exc:
            self._logger.error(
                "Failed to read item id=%s for delete: %s (status %s)",
                item_id,
                exc.message,
                exc.status_code,
            )
            raise

        existing["status"] = "retired"
        existing["updatedAt"] = datetime.now(timezone.utc).isoformat()

        try:
            self._container.upsert_item(body=existing)
            self._logger.info("Soft-deleted (retired) item id=%s", item_id)
        except CosmosHttpResponseError as exc:
            self._logger.error(
                "Failed to upsert retired item id=%s: %s (status %s)",
                item_id,
                exc.message,
                exc.status_code,
            )
            raise

    def hard_delete(self, item_id: str, partition_key: str) -> None:
        """Permanently remove a document from the container."""
        try:
            self._container.delete_item(item=item_id, partition_key=partition_key)
            self._logger.info("Hard-deleted item id=%s", item_id)
        except CosmosResourceNotFoundError:
            self._logger.error("Cannot hard_delete – item id=%s not found", item_id)
            raise
        except CosmosHttpResponseError as exc:
            self._logger.error(
                "Failed to hard_delete item id=%s: %s (status %s)",
                item_id,
                exc.message,
                exc.status_code,
            )
            raise


# ---------------------------------------------------------------------------
# Per-container repository factories
# ---------------------------------------------------------------------------


def get_assets_repo() -> CosmosRepository:
    return CosmosRepository(get_container("assets"))


def get_tags_repo() -> CosmosRepository:
    return CosmosRepository(get_container("tags"))


def get_sources_repo() -> CosmosRepository:
    return CosmosRepository(get_container("sources"))


def get_l1_rules_repo() -> CosmosRepository:
    return CosmosRepository(get_container("l1Rules"))


def get_l2_rules_repo() -> CosmosRepository:
    return CosmosRepository(get_container("l2Rules"))
