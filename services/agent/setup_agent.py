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
return null for both site and line — do NOT copy from the search result. \
If the tools fail or time out, infer the site/line from the search result \
using these mappings: LUX=Plant-Luxembourg, BEL=Plant-Brussels, \
NED=Plant-Amsterdam. L1=Line-1, L2=Line-2, L3=Line-3, L4=Line-4.

2. **Equipment**: If the query mentions equipment (pump, motor, compressor, \
etc.), use `get_available_equipment` with the resolved site and line to \
find valid equipment. Return the DISPLAY NAME exactly as returned by the \
tool (e.g. "Pump-001", "Compressor-001"). If the query doesn't mention \
equipment, return null. If the tool fails, return the display name format: \
"{Type}-001" (e.g. "Pump-001").

3. **Unit/Datatype**: ALWAYS copy these from the search result. The search \
result includes unit and datatype — keep them. Only override if the query \
explicitly describes a DIFFERENT measurement than the search result.

4. **Name**: Build the tag name using SHORT CODES, not display names. \
Format: `SITE_CODE.LINE_CODE.EQUIPMENT_CODE.MEASUREMENT.UNIT_CODE` \
(no ID suffix — the system adds it). \
Site codes: Plant-Luxembourg→LUX, Plant-Brussels→BEL, Plant-Amsterdam→NED. \
Line codes: Line-1→L1, Line-2→L2, Line-3→L3, Line-4→L4. \
Equipment codes: Pump→PMP, Compressor→CMP, Motor→MOT, Conveyor→CNV, \
Valve→VLV, HeatExchanger→HEX, Boiler→BLR, Tank→TNK (append 001). \
Example: LUX.L1.PMP001.Pressure.Bar \
Only build the name if you have site, line, and equipment; otherwise null.

5. **Description**: Clean up the user's query into a proper one-line description.

6. **Criticality**: Only set if the query contains criticality hints (e.g. \
"critical", "safety", "important"). Otherwise null.

## Unit and Measurement Reference
Unit codes: bar→Bar, °C→Cel, RPM→Rpm, mm/s→Mms, L/min→Lpm, kW→KW, A→Amp, \
m→M, kg→Kg, %→Pct, pH→Ph, m/s→Ms, bool→Bool

Measurement from unit: bar→Pressure, °C→Temperature, RPM→Speed, \
mm/s→Vibration, L/min→FlowRate, kW→Power, A→Current, m→Level, kg→Weight, \
m/s→Velocity, bool→Status

## Output Format
Return ONLY valid JSON with these keys:
{
  "site": "display name or null",
  "line": "display name or null",
  "equipment": "display name or null",
  "unit": "engineering unit (e.g. bar, °C) or null",
  "datatype": "float, int, or bool — or null",
  "name": "CODE.FORMAT.TAG.NAME or null",
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

    get_equipment = FunctionTool(
        name="get_available_equipment",
        description=(
            "Get available equipment for a specific site and line. "
            "Returns a list of equipment with display names."
        ),
        parameters={
            "type": "object",
            "properties": {
                "site": {
                    "type": "string",
                    "description": "The site display name (e.g. 'Plant-Luxembourg')",
                },
                "line": {
                    "type": "string",
                    "description": "The line display name (e.g. 'Line-1')",
                },
            },
            "required": ["site", "line"],
            "additionalProperties": False,
        },
        strict=True,
    )

    return [get_sites, get_lines, get_equipment]


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
