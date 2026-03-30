"""Repository factory functions.

Each helper returns a ``CosmosRepository`` instance bound to the
corresponding Cosmos DB container.  Import and call these from route
handlers or FastAPI dependency-injection functions.
"""

from src.config.cosmos import get_container
from .cosmos_repository import CosmosRepository


def get_assets_repo() -> CosmosRepository:
    """Return a repository for the *assets* container."""
    return CosmosRepository(get_container("assets"))


def get_tags_repo() -> CosmosRepository:
    """Return a repository for the *tags* container."""
    return CosmosRepository(get_container("tags"))


def get_sources_repo() -> CosmosRepository:
    """Return a repository for the *sources* container."""
    return CosmosRepository(get_container("sources"))


def get_l1_rules_repo() -> CosmosRepository:
    """Return a repository for the *l1Rules* container."""
    return CosmosRepository(get_container("l1Rules"))


def get_l2_rules_repo() -> CosmosRepository:
    """Return a repository for the *l2Rules* container."""
    return CosmosRepository(get_container("l2Rules"))


__all__ = [
    "CosmosRepository",
    "get_assets_repo",
    "get_tags_repo",
    "get_sources_repo",
    "get_l1_rules_repo",
    "get_l2_rules_repo",
]