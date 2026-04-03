"""Azure Functions for tag auto-fill agent tools.

Provides HTTP-triggered functions that query the Cosmos DB assets container
to return available sites and lines. Used as tools by the Foundry AI agent.
"""

import json
import logging
import os

import azure.functions as func
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

logger = logging.getLogger("functions.autofill_tools")

_cached_container = None


def _get_assets_container():
    """Return a cached reference to the Cosmos DB assets container."""
    global _cached_container
    if _cached_container is not None:
        return _cached_container

    endpoint = os.environ["COSMOS_ENDPOINT"]
    database_name = os.environ.get("COSMOS_DATABASE", "ot-tag-registry")

    client = CosmosClient(url=endpoint, credential=DefaultAzureCredential())
    database = client.get_database_client(database_name)
    _cached_container = database.get_container_client("assets")
    return _cached_container


@app.route(route="get-sites", methods=["GET"])
def get_sites(req: func.HttpRequest) -> func.HttpResponse:
    """Return all available plant sites with display names and codes.

    Response: [{"display": "Plant-Luxembourg", "code": "LUX"}, ...]
    """
    try:
        container = _get_assets_container()
        results = list(container.query_items(
            query="SELECT DISTINCT c.site FROM c",
            enable_cross_partition_query=True,
        ))

        site_code_map = {
            "Plant-Luxembourg": "LUX",
            "Plant-Brussels": "BEL",
            "Plant-Amsterdam": "NED",
        }

        sites = []
        for row in results:
            display = row["site"]
            code = site_code_map.get(display, display[:3].upper())
            sites.append({"display": display, "code": code})

        sites.sort(key=lambda s: s["display"])

        return func.HttpResponse(
            json.dumps(sites),
            mimetype="application/json",
        )
    except Exception as exc:
        logger.exception("Failed to query sites")
        return func.HttpResponse(
            json.dumps({"error": str(exc)}),
            status_code=500,
            mimetype="application/json",
        )


@app.route(route="get-lines", methods=["GET"])
def get_lines(req: func.HttpRequest) -> func.HttpResponse:
    """Return available production lines for a given site.

    Query param: site (display name, e.g. "Plant-Luxembourg")
    Response: [{"display": "Line-1", "code": "L1"}, ...]
    """
    site = req.params.get("site")
    if not site:
        return func.HttpResponse(
            json.dumps({"error": "Missing required query parameter: site"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        container = _get_assets_container()
        results = list(container.query_items(
            query="SELECT DISTINCT c.line FROM c WHERE c.site = @site",
            parameters=[{"name": "@site", "value": site}],
            partition_key=site,
        ))

        lines = []
        for row in results:
            display = row["line"]
            code = display.replace("Line-", "L")
            lines.append({"display": display, "code": code})

        lines.sort(key=lambda l: l["display"])

        return func.HttpResponse(
            json.dumps(lines),
            mimetype="application/json",
        )
    except Exception as exc:
        logger.exception("Failed to query lines for site %s", site)
        return func.HttpResponse(
            json.dumps({"error": str(exc)}),
            status_code=500,
            mimetype="application/json",
        )
