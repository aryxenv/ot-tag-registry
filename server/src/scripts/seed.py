"""Seed script — creates Cosmos DB containers and inserts sample documents.

Usage:
    cd server
    uv run python -m src.scripts.seed
"""

from dotenv import load_dotenv

load_dotenv()

from src.config.cosmos import ensure_containers, get_container, get_cosmos_client
from src.models import (
    Asset,
    Tag,
    DataType,
    Criticality,
    TagStatus,
    Source,
    SystemType,
    L1Rule,
    MissingDataPolicy,
    L2Rule,
    StateMapping,
    OperationalState,
    ConditionOperator,
)


def seed():
    print("Connecting to Cosmos DB...")
    client = get_cosmos_client()

    print("Creating database and containers...")
    ensure_containers(client)

    # --- Assets ---
    asset1 = Asset(site="Plant-Munich", line="Line-2", equipment="Pump-001", description="Main cooling pump")
    asset2 = Asset(site="Plant-Munich", line="Line-2", equipment="Compressor-003", description="Air compressor unit 3")

    assets_container = get_container("assets", client)
    for asset in [asset1, asset2]:
        assets_container.upsert_item(asset.model_dump(mode="json"))
        print(f"  Upserted asset: {asset.hierarchy}")

    # --- Sources ---
    source1 = Source(
        systemType=SystemType.PLC,
        connectorType="OPC-UA",
        topicOrPath="ns=2;s=Pump001.OutletPressure",
        description="Siemens S7-1500 PLC",
    )
    source2 = Source(
        systemType=SystemType.SCADA,
        connectorType="MQTT",
        topicOrPath="plant-munich/line-2/compressor-003/temperature",
        description="Ignition SCADA gateway",
    )

    sources_container = get_container("sources", client)
    for source in [source1, source2]:
        sources_container.upsert_item(source.model_dump(mode="json"))
        print(f"  Upserted source: {source.systemType.value} — {source.connectorType}")

    # --- Tags ---
    tag1 = Tag(
        name="MUN.L2.PMP001.OutletPressure",
        description="Outlet pressure of main cooling pump",
        unit="bar",
        datatype=DataType.FLOAT,
        samplingFrequency=1.0,
        criticality=Criticality.HIGH,
        status=TagStatus.ACTIVE,
        assetId=asset1.id,
        sourceId=source1.id,
    )
    tag2 = Tag(
        name="MUN.L2.CMP003.Temperature",
        description="Discharge temperature of compressor unit 3",
        unit="°C",
        datatype=DataType.FLOAT,
        samplingFrequency=5.0,
        criticality=Criticality.MEDIUM,
        status=TagStatus.ACTIVE,
        assetId=asset2.id,
        sourceId=source2.id,
    )

    tags_container = get_container("tags", client)
    for tag in [tag1, tag2]:
        tags_container.upsert_item(tag.model_dump(mode="json"))
        print(f"  Upserted tag: {tag.name}")

    # --- L1 Rules ---
    l1_rule1 = L1Rule(
        tagId=tag1.id,
        min=0.5,
        max=12.0,
        missingDataPolicy=MissingDataPolicy.ALERT,
        spikeThreshold=3.0,
    )
    l1_rule2 = L1Rule(
        tagId=tag2.id,
        min=-10.0,
        max=120.0,
        missingDataPolicy=MissingDataPolicy.LAST_KNOWN,
        spikeThreshold=15.0,
    )

    l1_container = get_container("l1Rules", client)
    for rule in [l1_rule1, l1_rule2]:
        l1_container.upsert_item(rule.model_dump(mode="json"))
        print(f"  Upserted L1 rule for tag: {rule.tagId[:8]}...")

    # --- L2 Rules ---
    l2_rule1 = L2Rule(
        tagId=tag1.id,
        stateMapping=[
            StateMapping(
                state=OperationalState.RUNNING,
                conditionField="MUN.L2.PMP001.Status",
                conditionOperator=ConditionOperator.EQ,
                conditionValue=1.0,
                rangeMin=2.0,
                rangeMax=10.0,
            ),
            StateMapping(
                state=OperationalState.IDLE,
                conditionField="MUN.L2.PMP001.Status",
                conditionOperator=ConditionOperator.EQ,
                conditionValue=0.0,
                rangeMin=0.5,
                rangeMax=2.0,
            ),
            StateMapping(
                state=OperationalState.STOP,
                conditionField="MUN.L2.PMP001.Status",
                conditionOperator=ConditionOperator.LT,
                conditionValue=0.0,
                rangeMin=None,
                rangeMax=0.5,
            ),
        ],
    )

    l2_container = get_container("l2Rules", client)
    l2_container.upsert_item(l2_rule1.model_dump(mode="json"))
    print(f"  Upserted L2 rule for tag: {l2_rule1.tagId[:8]}...")

    print("\nSeed complete!")


if __name__ == "__main__":
    seed()
