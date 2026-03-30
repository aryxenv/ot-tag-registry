"""Generic CRUD helper wrapping an Azure Cosmos DB container."""

import logging
from datetime import datetime, timezone

from azure.cosmos import ContainerProxy
from azure.cosmos.exceptions import (
    CosmosHttpResponseError,
    CosmosResourceNotFoundError,
)


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

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Read – single item
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Read – list
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Query – parameterised SQL
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Update (partial merge)
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Delete (soft-delete → status = "retired")
    # ------------------------------------------------------------------
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
