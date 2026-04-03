"""Create or update the tag auto-fill agent on Azure AI Foundry.

Uses the azure-ai-projects SDK to register an agent with function-calling
tools for site/line lookup.  Run after provisioning infrastructure.

Usage:
    cd services
    uv run python -m agent.setup_agent
"""

import logging
import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FunctionTool, PromptAgentDefinition, Tool
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

_repo_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_repo_root / "services" / ".env")

logger = logging.getLogger("agent.setup_agent")
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

AGENT_NAME = "tag-auto-fill"

SYSTEM_PROMPT = """\
You are a tag auto-fill agent for an industrial IoT tag registry.

## Your Role
You receive a user's free-text query and the closest matching tag from the \
golden-tags search index. Your job is to CLEAN and VALIDATE the search result \
against the user's query, producing structured form fields.

## Rules
1. **Site/Line**: If the query mentions a location (city name, plant name, or \
site code), use your `get_available_sites` tool to find the matching site, then \
`get_available_lines` to find valid lines. Return the DISPLAY NAME (e.g. \
"Plant-Luxembourg", "Line-1"). If the query does NOT mention any location, \
return null for both site and line — do NOT copy from the search result.

2. **Equipment**: If the query mentions equipment (pump, motor, compressor, \
etc.), return the display name format: "{Type}-001" (e.g. "Pump-001", \
"Compressor-001"). If the query doesn't mention equipment, return null.

3. **Unit/Datatype**: Keep from the search result if the measurement concept \
matches the query. Override if the query describes a different measurement \
(e.g. query says "temperature" but search result is a pressure tag).

4. **Name**: Build the tag name in format SITE.LINE.EQUIPMENT.MEASUREMENT.UNIT \
(no ID suffix — the system adds it). Only if you have enough fields to build it; \
otherwise null.

5. **Description**: Clean up the user's query into a proper one-line description.

6. **Criticality**: Only set if the query contains criticality hints (e.g. \
"critical", "safety", "important"). Otherwise null.

## Tag Naming Format
`SITE.LINE.EQUIPMENT.MEASUREMENT.UNIT`

Equipment codes: PMP=Pump, CMP=Compressor, MOT=Motor, CNV=Conveyor, \
VLV=Valve, HEX=HeatExchanger, BLR=Boiler, TNK=Tank

Unit codes: bar→Bar, °C→Cel, RPM→Rpm, mm/s→Mms, L/min→Lpm, kW→KW, A→Amp, \
m→M, kg→Kg, %→Pct, pH→Ph

Measurement from unit: bar→Pressure, °C→Temperature, RPM→Speed, \
mm/s→Vibration, L/min→FlowRate, kW→Power, A→Current

## Output Format
Return ONLY valid JSON with these keys:
{
  "site": "display name or null",
  "line": "display name or null",
  "equipment": "display name or null",
  "unit": "engineering unit (e.g. bar, °C) or null",
  "datatype": "float, int, or bool — or null",
  "name": "TAG.NAME.FORMAT or null",
  "description": "cleaned one-line description or null",
  "criticality": "low/medium/high/critical or null"
}

Return ONLY valid JSON, no markdown fences, no explanation."""


def _build_tools() -> list[Tool]:
    """Define the function-calling tools for the agent."""
    get_sites = FunctionTool(
        name="get_available_sites",
        description=(
            "Get all available plant sites in the registry. "
            "Returns a list of sites with display names and short codes."
        ),
        parameters={
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        strict=True,
    )

    get_lines = FunctionTool(
        name="get_available_lines",
        description=(
            "Get available production lines for a specific site. "
            "Returns a list of lines with display names and short codes."
        ),
        parameters={
            "type": "object",
            "properties": {
                "site": {
                    "type": "string",
                    "description": "The site display name (e.g. 'Plant-Luxembourg')",
                },
            },
            "required": ["site"],
            "additionalProperties": False,
        },
        strict=True,
    )

    return [get_sites, get_lines]


def setup() -> None:
    """Create or update the tag auto-fill agent on AI Foundry."""
    project_endpoint = os.environ.get("PROJECT_ENDPOINT", "")
    chat_deployment = os.environ.get("PROJECT_CHAT_DEPLOYMENT", "")

    if not project_endpoint:
        raise ValueError("PROJECT_ENDPOINT must be set")
    if not chat_deployment:
        raise ValueError("PROJECT_CHAT_DEPLOYMENT must be set")

    project = AIProjectClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential(),
    )

    tools = _build_tools()

    agent = project.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(
            model=chat_deployment,
            instructions=SYSTEM_PROMPT,
            tools=tools,
        ),
    )

    print(f"  ✔ Agent '{agent.name}' created/updated (model: {chat_deployment})")
    print(f"    Tools: {[t.name for t in tools if hasattr(t, 'name')]}")


if __name__ == "__main__":
    setup()
