from dotenv import load_dotenv

load_dotenv()

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.config.cosmos import get_cosmos_client, get_database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("ot_tag_registry")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup / shutdown lifecycle for the FastAPI app."""
    # --- startup ---
    try:
        client = get_cosmos_client()
        app.state.cosmos_client = client
        logger.info("Cosmos DB connection established")
    except Exception as e:
        logger.error("Failed to initialize Cosmos DB: %s", e)
        app.state.cosmos_client = None
    yield
    # --- shutdown ---
    logger.info("Shutting down")


app = FastAPI(title="OT Tag Registry API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db(request: Request):
    """FastAPI dependency that returns the Cosmos database client."""
    client = getattr(request.app.state, "cosmos_client", None)
    if client is None:
        raise RuntimeError("Cosmos DB client is not available")
    return get_database(client)


@app.get("/")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/test")
async def test() -> dict[str, str]:
    return {"message": "hello world"}
