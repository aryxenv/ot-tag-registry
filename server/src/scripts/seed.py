"""Seed script — creates Cosmos DB containers and inserts realistic sample data.

Populates:
  • 12 assets across 3 sites (Munich, Detroit, Shanghai)
  • 6  data sources (PLC, SCADA, Historian)
  • 31 tags with deterministic names
  • 26 L1 range-validation rules (one per numeric tag)
  • 5  L2 state-profile rules (pump pressures, motor speeds)

Usage:
    cd server
    uv run python -m src.scripts.seed
"""

from dotenv import load_dotenv

load_dotenv()

from src.config.cosmos import ensure_containers, get_cosmos_client
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
from src.repositories import (
    get_assets_repo,
    get_tags_repo,
    get_sources_repo,
    get_l1_rules_repo,
    get_l2_rules_repo,
)


# ──────────────────────────────────────────────────────────────────────
# Helper — insert a Pydantic model via the repository layer
# ──────────────────────────────────────────────────────────────────────
def _insert(repo, model, label: str) -> None:
    """Serialize *model* and persist it through *repo*.create()."""
    repo.create(model.model_dump(mode="json"))
    print(f"  ✔ {label}")


# ──────────────────────────────────────────────────────────────────────
# ASSETS
# ──────────────────────────────────────────────────────────────────────
def _build_assets() -> list[Asset]:
    """Return 12 assets across Munich, Detroit, and Shanghai."""

    # --- Plant-Munich (MUN) ---
    mun_pmp001 = Asset(
        site="Plant-Munich", line="Line-1", equipment="Pump-001",
        description="Primary coolant circulation pump",
    )
    mun_pmp002 = Asset(
        site="Plant-Munich", line="Line-1", equipment="Pump-002",
        description="Secondary coolant circulation pump (standby)",
    )
    mun_cmp003 = Asset(
        site="Plant-Munich", line="Line-2", equipment="Compressor-003",
        description="Instrument-air compressor unit 3",
    )
    mun_mot004 = Asset(
        site="Plant-Munich", line="Line-2", equipment="Motor-004",
        description="Main drive motor for compressor 3",
    )

    # --- Plant-Detroit (DET) ---
    det_cnv001 = Asset(
        site="Plant-Detroit", line="Line-1", equipment="Conveyor-001",
        description="Raw-material intake belt conveyor",
    )
    det_vlv002 = Asset(
        site="Plant-Detroit", line="Line-1", equipment="Valve-002",
        description="Feed-water isolation valve",
    )
    det_pmp003 = Asset(
        site="Plant-Detroit", line="Line-3", equipment="Pump-003",
        description="Boiler feed-water pump",
    )
    det_mot004 = Asset(
        site="Plant-Detroit", line="Line-3", equipment="Motor-004",
        description="Variable-frequency drive motor for pump 3",
    )

    # --- Plant-Shanghai (SHA) ---
    sha_cmp001 = Asset(
        site="Plant-Shanghai", line="Line-2", equipment="Compressor-001",
        description="Refrigerant compressor for chiller system",
    )
    sha_pmp002 = Asset(
        site="Plant-Shanghai", line="Line-2", equipment="Pump-002",
        description="Chilled-water recirculation pump",
    )
    sha_vlv003 = Asset(
        site="Plant-Shanghai", line="Line-4", equipment="Valve-003",
        description="Steam header pressure-control valve",
    )
    sha_cnv004 = Asset(
        site="Plant-Shanghai", line="Line-4", equipment="Conveyor-004",
        description="Finished-goods packaging conveyor",
    )

    return [
        mun_pmp001, mun_pmp002, mun_cmp003, mun_mot004,
        det_cnv001, det_vlv002, det_pmp003, det_mot004,
        sha_cmp001, sha_pmp002, sha_vlv003, sha_cnv004,
    ]


# ──────────────────────────────────────────────────────────────────────
# SOURCES
# ──────────────────────────────────────────────────────────────────────
def _build_sources() -> list[Source]:
    """Return 6 data-source definitions."""

    src_siemens = Source(
        systemType=SystemType.PLC,
        connectorType="OPC-UA",
        topicOrPath="opc.tcp://mun-plc01:4840/ns=2;s=S7-1500",
        description="Siemens S7-1500 PLC — Munich plant floor",
    )
    src_ab = Source(
        systemType=SystemType.PLC,
        connectorType="OPC-UA",
        topicOrPath="opc.tcp://det-plc01:4840/ns=2;s=ControlLogix",
        description="Allen-Bradley ControlLogix PLC — Detroit plant floor",
    )
    src_ignition = Source(
        systemType=SystemType.SCADA,
        connectorType="MQTT",
        topicOrPath="mqtt://mun-scada01:1883/plant-munich/#",
        description="Ignition SCADA gateway — Munich",
    )
    src_wonderware = Source(
        systemType=SystemType.SCADA,
        connectorType="MQTT",
        topicOrPath="mqtt://sha-scada01:1883/plant-shanghai/#",
        description="Wonderware InTouch SCADA — Shanghai",
    )
    src_osisoft = Source(
        systemType=SystemType.HISTORIAN,
        connectorType="PI-SDK",
        topicOrPath="pisrv://det-hist01:5450/piarchive",
        description="OSIsoft PI Data Archive — Detroit",
    )
    src_aveva = Source(
        systemType=SystemType.HISTORIAN,
        connectorType="REST",
        topicOrPath="https://sha-hist01:8443/aveva/historian/v2",
        description="AVEVA Historian — Shanghai",
    )

    return [src_siemens, src_ab, src_ignition, src_wonderware, src_osisoft, src_aveva]


# ──────────────────────────────────────────────────────────────────────
# TAGS
# ──────────────────────────────────────────────────────────────────────
def _build_tags(assets: list[Asset], sources: list[Source]) -> list[Tag]:
    """Return 31 tags wired to the given assets and sources."""

    # Destructure assets in creation order
    (
        mun_pmp001, mun_pmp002, mun_cmp003, mun_mot004,
        det_cnv001, det_vlv002, det_pmp003, det_mot004,
        sha_cmp001, sha_pmp002, sha_vlv003, sha_cnv004,
    ) = assets

    # Destructure sources
    (
        src_siemens, src_ab, src_ignition,
        src_wonderware, src_osisoft, src_aveva,
    ) = sources

    tags: list[Tag] = []

    # ── Munich Line-1 Pump-001 (3 tags) ─────────────────────────────
    tags.append(Tag(
        name="MUN.L1.PMP001.OutletPressure",
        description="Outlet pressure of primary coolant pump",
        unit="bar", datatype=DataType.FLOAT, samplingFrequency=1.0,
        criticality=Criticality.HIGH, status=TagStatus.ACTIVE,
        assetId=mun_pmp001.id, sourceId=src_siemens.id,
    ))
    tags.append(Tag(
        name="MUN.L1.PMP001.FlowRate",
        description="Volumetric flow rate of primary coolant pump",
        unit="L/min", datatype=DataType.FLOAT, samplingFrequency=2.0,
        criticality=Criticality.HIGH, status=TagStatus.ACTIVE,
        assetId=mun_pmp001.id, sourceId=src_siemens.id,
    ))
    tags.append(Tag(
        name="MUN.L1.PMP001.MotorCurrent",
        description="Motor winding current draw — pump 001",
        unit="A", datatype=DataType.FLOAT, samplingFrequency=1.0,
        criticality=Criticality.MEDIUM, status=TagStatus.ACTIVE,
        assetId=mun_pmp001.id, sourceId=src_siemens.id,
    ))

    # ── Munich Line-1 Pump-002 (2 tags) ─────────────────────────────
    tags.append(Tag(
        name="MUN.L1.PMP002.OutletPressure",
        description="Outlet pressure of standby coolant pump",
        unit="bar", datatype=DataType.FLOAT, samplingFrequency=1.0,
        criticality=Criticality.MEDIUM, status=TagStatus.DRAFT,
        assetId=mun_pmp002.id, sourceId=src_siemens.id,
    ))
    tags.append(Tag(
        name="MUN.L1.PMP002.FlowRate",
        description="Volumetric flow rate of standby coolant pump",
        unit="L/min", datatype=DataType.FLOAT, samplingFrequency=2.0,
        criticality=Criticality.MEDIUM, status=TagStatus.DRAFT,
        assetId=mun_pmp002.id, sourceId=src_siemens.id,
    ))

    # ── Munich Line-2 Compressor-003 (3 tags) ───────────────────────
    tags.append(Tag(
        name="MUN.L2.CMP003.DischargeTemp",
        description="Discharge temperature of instrument-air compressor 3",
        unit="°C", datatype=DataType.FLOAT, samplingFrequency=5.0,
        criticality=Criticality.HIGH, status=TagStatus.ACTIVE,
        assetId=mun_cmp003.id, sourceId=src_ignition.id,
    ))
    tags.append(Tag(
        name="MUN.L2.CMP003.InletPressure",
        description="Inlet suction pressure of compressor 3",
        unit="bar", datatype=DataType.FLOAT, samplingFrequency=5.0,
        criticality=Criticality.MEDIUM, status=TagStatus.ACTIVE,
        assetId=mun_cmp003.id, sourceId=src_ignition.id,
    ))
    tags.append(Tag(
        name="MUN.L2.CMP003.VibrationLevel",
        description="Bearing vibration level — compressor 3",
        unit="mm/s", datatype=DataType.FLOAT, samplingFrequency=0.5,
        criticality=Criticality.CRITICAL, status=TagStatus.ACTIVE,
        assetId=mun_cmp003.id, sourceId=src_ignition.id,
    ))

    # ── Munich Line-2 Motor-004 (3 tags) ────────────────────────────
    tags.append(Tag(
        name="MUN.L2.MOT004.Speed",
        description="Rotational speed of compressor drive motor",
        unit="RPM", datatype=DataType.FLOAT, samplingFrequency=1.0,
        criticality=Criticality.HIGH, status=TagStatus.ACTIVE,
        assetId=mun_mot004.id, sourceId=src_ignition.id,
    ))
    tags.append(Tag(
        name="MUN.L2.MOT004.Temperature",
        description="Stator winding temperature — motor 004",
        unit="°C", datatype=DataType.FLOAT, samplingFrequency=10.0,
        criticality=Criticality.MEDIUM, status=TagStatus.ACTIVE,
        assetId=mun_mot004.id, sourceId=src_ignition.id,
    ))
    tags.append(Tag(
        name="MUN.L2.MOT004.PowerConsumption",
        description="Active power consumption of motor 004",
        unit="kW", datatype=DataType.FLOAT, samplingFrequency=5.0,
        criticality=Criticality.LOW, status=TagStatus.ACTIVE,
        assetId=mun_mot004.id, sourceId=src_siemens.id,
    ))

    # ── Detroit Line-1 Conveyor-001 (3 tags) ────────────────────────
    tags.append(Tag(
        name="DET.L1.CNV001.BeltSpeed",
        description="Belt linear speed of intake conveyor",
        unit="m/s", datatype=DataType.FLOAT, samplingFrequency=2.0,
        criticality=Criticality.MEDIUM, status=TagStatus.ACTIVE,
        assetId=det_cnv001.id, sourceId=src_ab.id,
    ))
    tags.append(Tag(
        name="DET.L1.CNV001.LoadWeight",
        description="Instantaneous belt load weight",
        unit="kg", datatype=DataType.FLOAT, samplingFrequency=5.0,
        criticality=Criticality.LOW, status=TagStatus.ACTIVE,
        assetId=det_cnv001.id, sourceId=src_ab.id,
    ))
    tags.append(Tag(
        name="DET.L1.CNV001.Running",
        description="Conveyor running status (true = running)",
        unit="-", datatype=DataType.BOOL, samplingFrequency=10.0,
        criticality=Criticality.LOW, status=TagStatus.ACTIVE,
        assetId=det_cnv001.id, sourceId=src_ab.id,
    ))

    # ── Detroit Line-1 Valve-002 (2 tags) ───────────────────────────
    tags.append(Tag(
        name="DET.L1.VLV002.Position",
        description="Valve stem position (0%=closed, 100%=open)",
        unit="%", datatype=DataType.FLOAT, samplingFrequency=1.0,
        criticality=Criticality.HIGH, status=TagStatus.ACTIVE,
        assetId=det_vlv002.id, sourceId=src_ab.id,
    ))
    tags.append(Tag(
        name="DET.L1.VLV002.OpenClose",
        description="Discrete open/close limit-switch feedback",
        unit="-", datatype=DataType.BOOL, samplingFrequency=10.0,
        criticality=Criticality.MEDIUM, status=TagStatus.ACTIVE,
        assetId=det_vlv002.id, sourceId=src_ab.id,
    ))

    # ── Detroit Line-3 Pump-003 (3 tags) ────────────────────────────
    tags.append(Tag(
        name="DET.L3.PMP003.OutletPressure",
        description="Discharge pressure of boiler feed-water pump",
        unit="bar", datatype=DataType.FLOAT, samplingFrequency=1.0,
        criticality=Criticality.CRITICAL, status=TagStatus.ACTIVE,
        assetId=det_pmp003.id, sourceId=src_osisoft.id,
    ))
    tags.append(Tag(
        name="DET.L3.PMP003.FlowRate",
        description="Feed-water volumetric flow rate",
        unit="L/min", datatype=DataType.FLOAT, samplingFrequency=2.0,
        criticality=Criticality.HIGH, status=TagStatus.ACTIVE,
        assetId=det_pmp003.id, sourceId=src_osisoft.id,
    ))
    tags.append(Tag(
        name="DET.L3.PMP003.MotorCurrent",
        description="Motor current draw — feed-water pump 003",
        unit="A", datatype=DataType.FLOAT, samplingFrequency=1.0,
        criticality=Criticality.MEDIUM, status=TagStatus.ACTIVE,
        assetId=det_pmp003.id, sourceId=src_osisoft.id,
    ))

    # ── Detroit Line-3 Motor-004 (2 tags) ───────────────────────────
    tags.append(Tag(
        name="DET.L3.MOT004.Speed",
        description="VFD motor speed — feed-water pump drive",
        unit="RPM", datatype=DataType.FLOAT, samplingFrequency=1.0,
        criticality=Criticality.HIGH, status=TagStatus.ACTIVE,
        assetId=det_mot004.id, sourceId=src_osisoft.id,
    ))
    tags.append(Tag(
        name="DET.L3.MOT004.Temperature",
        description="Stator temperature — motor 004 Detroit",
        unit="°C", datatype=DataType.FLOAT, samplingFrequency=10.0,
        criticality=Criticality.MEDIUM, status=TagStatus.RETIRED,
        assetId=det_mot004.id, sourceId=src_osisoft.id,
    ))

    # ── Shanghai Line-2 Compressor-001 (3 tags) ─────────────────────
    tags.append(Tag(
        name="SHA.L2.CMP001.DischargeTemp",
        description="Refrigerant discharge temperature — compressor 1",
        unit="°C", datatype=DataType.FLOAT, samplingFrequency=5.0,
        criticality=Criticality.HIGH, status=TagStatus.ACTIVE,
        assetId=sha_cmp001.id, sourceId=src_wonderware.id,
    ))
    tags.append(Tag(
        name="SHA.L2.CMP001.InletPressure",
        description="Refrigerant suction pressure — compressor 1",
        unit="bar", datatype=DataType.FLOAT, samplingFrequency=5.0,
        criticality=Criticality.MEDIUM, status=TagStatus.ACTIVE,
        assetId=sha_cmp001.id, sourceId=src_wonderware.id,
    ))
    tags.append(Tag(
        name="SHA.L2.CMP001.VibrationLevel",
        description="Bearing vibration — compressor 1 Shanghai",
        unit="mm/s", datatype=DataType.FLOAT, samplingFrequency=0.5,
        criticality=Criticality.CRITICAL, status=TagStatus.ACTIVE,
        assetId=sha_cmp001.id, sourceId=src_wonderware.id,
    ))

    # ── Shanghai Line-2 Pump-002 (2 tags) ───────────────────────────
    tags.append(Tag(
        name="SHA.L2.PMP002.OutletPressure",
        description="Discharge pressure of chilled-water pump",
        unit="bar", datatype=DataType.FLOAT, samplingFrequency=2.0,
        criticality=Criticality.HIGH, status=TagStatus.ACTIVE,
        assetId=sha_pmp002.id, sourceId=src_aveva.id,
    ))
    tags.append(Tag(
        name="SHA.L2.PMP002.FlowRate",
        description="Chilled-water volumetric flow rate",
        unit="L/min", datatype=DataType.FLOAT, samplingFrequency=2.0,
        criticality=Criticality.MEDIUM, status=TagStatus.ACTIVE,
        assetId=sha_pmp002.id, sourceId=src_aveva.id,
    ))

    # ── Shanghai Line-4 Valve-003 (2 tags) ──────────────────────────
    tags.append(Tag(
        name="SHA.L4.VLV003.Position",
        description="Control-valve position — steam header",
        unit="%", datatype=DataType.FLOAT, samplingFrequency=1.0,
        criticality=Criticality.HIGH, status=TagStatus.ACTIVE,
        assetId=sha_vlv003.id, sourceId=src_aveva.id,
    ))
    tags.append(Tag(
        name="SHA.L4.VLV003.OpenClose",
        description="Discrete open/close status — steam valve",
        unit="-", datatype=DataType.BOOL, samplingFrequency=10.0,
        criticality=Criticality.LOW, status=TagStatus.RETIRED,
        assetId=sha_vlv003.id, sourceId=src_aveva.id,
    ))

    # ── Shanghai Line-4 Conveyor-004 (3 tags) ───────────────────────
    tags.append(Tag(
        name="SHA.L4.CNV004.BeltSpeed",
        description="Belt speed of packaging conveyor",
        unit="m/s", datatype=DataType.FLOAT, samplingFrequency=2.0,
        criticality=Criticality.MEDIUM, status=TagStatus.ACTIVE,
        assetId=sha_cnv004.id, sourceId=src_wonderware.id,
    ))
    tags.append(Tag(
        name="SHA.L4.CNV004.LoadWeight",
        description="Instantaneous belt load — packaging conveyor",
        unit="kg", datatype=DataType.FLOAT, samplingFrequency=5.0,
        criticality=Criticality.LOW, status=TagStatus.DRAFT,
        assetId=sha_cnv004.id, sourceId=src_wonderware.id,
    ))
    tags.append(Tag(
        name="SHA.L4.CNV004.Running",
        description="Conveyor running status (true = running)",
        unit="-", datatype=DataType.BOOL, samplingFrequency=10.0,
        criticality=Criticality.LOW, status=TagStatus.ACTIVE,
        assetId=sha_cnv004.id, sourceId=src_wonderware.id,
    ))

    return tags


# ──────────────────────────────────────────────────────────────────────
# L1 RULES — one per numeric (float) tag
# ──────────────────────────────────────────────────────────────────────
# Physical-range lookup keyed by the measurement suffix of a tag name.
_L1_RANGES: dict[str, dict] = {
    "OutletPressure": dict(min=0.0, max=16.0, spikeThreshold=5.0),
    "InletPressure":  dict(min=0.0, max=16.0, spikeThreshold=5.0),
    "DischargeTemp":  dict(min=-20.0, max=200.0, spikeThreshold=30.0),
    "Temperature":    dict(min=-20.0, max=200.0, spikeThreshold=30.0),
    "FlowRate":       dict(min=0.0, max=500.0, spikeThreshold=100.0),
    "MotorCurrent":   dict(min=0.0, max=100.0, spikeThreshold=20.0),
    "Speed":          dict(min=0.0, max=3600.0, spikeThreshold=500.0),
    "PowerConsumption": dict(min=0.0, max=500.0, spikeThreshold=100.0),
    "VibrationLevel": dict(min=0.0, max=25.0, spikeThreshold=10.0),
    "BeltSpeed":      dict(min=0.0, max=5.0, spikeThreshold=2.0),
    "LoadWeight":     dict(min=0.0, max=2000.0, spikeThreshold=500.0),
    "Position":       dict(min=0.0, max=100.0, spikeThreshold=30.0),
}

# Rotate policies so the seed data exercises all four variants.
_POLICIES = [
    MissingDataPolicy.ALERT,
    MissingDataPolicy.IGNORE,
    MissingDataPolicy.LAST_KNOWN,
    MissingDataPolicy.INTERPOLATE,
]


def _build_l1_rules(tags: list[Tag]) -> list[L1Rule]:
    """Create an L1Rule for every numeric (non-bool) tag."""
    rules: list[L1Rule] = []
    policy_idx = 0
    for tag in tags:
        if tag.datatype == DataType.BOOL:
            continue  # booleans don't have numeric ranges
        measurement = tag.name.rsplit(".", maxsplit=1)[-1]
        ranges = _L1_RANGES.get(measurement, dict(min=0.0, max=100.0, spikeThreshold=25.0))
        rules.append(L1Rule(
            tagId=tag.id,
            min=ranges["min"],
            max=ranges["max"],
            spikeThreshold=ranges["spikeThreshold"],
            missingDataPolicy=_POLICIES[policy_idx % len(_POLICIES)],
        ))
        policy_idx += 1
    return rules


# ──────────────────────────────────────────────────────────────────────
# L2 RULES — state-profile rules for key equipment tags
# ──────────────────────────────────────────────────────────────────────
def _build_l2_rules(tags: list[Tag]) -> list[L2Rule]:
    """Create L2 state-profile rules for 5 critical tags."""

    # Build a quick lookup: tag name → Tag object
    by_name: dict[str, Tag] = {t.name: t for t in tags}

    rules: list[L2Rule] = []

    # 1) Munich Pump-001 outlet pressure — Running / Idle / Stop
    rules.append(L2Rule(
        tagId=by_name["MUN.L1.PMP001.OutletPressure"].id,
        stateMapping=[
            StateMapping(
                state=OperationalState.RUNNING,
                conditionField="MUN.L1.PMP001.MotorCurrent",
                conditionOperator=ConditionOperator.GT,
                conditionValue=5.0,
                rangeMin=4.0, rangeMax=14.0,
            ),
            StateMapping(
                state=OperationalState.IDLE,
                conditionField="MUN.L1.PMP001.MotorCurrent",
                conditionOperator=ConditionOperator.BETWEEN,
                conditionValue=[0.5, 5.0],
                rangeMin=0.5, rangeMax=4.0,
            ),
            StateMapping(
                state=OperationalState.STOP,
                conditionField="MUN.L1.PMP001.MotorCurrent",
                conditionOperator=ConditionOperator.LTE,
                conditionValue=0.5,
                rangeMin=None, rangeMax=0.5,
            ),
        ],
    ))

    # 2) Munich Motor-004 speed — Running / Idle / Stop
    rules.append(L2Rule(
        tagId=by_name["MUN.L2.MOT004.Speed"].id,
        stateMapping=[
            StateMapping(
                state=OperationalState.RUNNING,
                conditionField="MUN.L2.MOT004.PowerConsumption",
                conditionOperator=ConditionOperator.GT,
                conditionValue=10.0,
                rangeMin=900.0, rangeMax=3600.0,
            ),
            StateMapping(
                state=OperationalState.IDLE,
                conditionField="MUN.L2.MOT004.PowerConsumption",
                conditionOperator=ConditionOperator.BETWEEN,
                conditionValue=[1.0, 10.0],
                rangeMin=50.0, rangeMax=900.0,
            ),
            StateMapping(
                state=OperationalState.STOP,
                conditionField="MUN.L2.MOT004.PowerConsumption",
                conditionOperator=ConditionOperator.LTE,
                conditionValue=1.0,
                rangeMin=None, rangeMax=50.0,
            ),
        ],
    ))

    # 3) Detroit Pump-003 outlet pressure — Running / Idle / Stop
    rules.append(L2Rule(
        tagId=by_name["DET.L3.PMP003.OutletPressure"].id,
        stateMapping=[
            StateMapping(
                state=OperationalState.RUNNING,
                conditionField="DET.L3.PMP003.MotorCurrent",
                conditionOperator=ConditionOperator.GT,
                conditionValue=8.0,
                rangeMin=6.0, rangeMax=15.0,
            ),
            StateMapping(
                state=OperationalState.IDLE,
                conditionField="DET.L3.PMP003.MotorCurrent",
                conditionOperator=ConditionOperator.BETWEEN,
                conditionValue=[1.0, 8.0],
                rangeMin=1.0, rangeMax=6.0,
            ),
            StateMapping(
                state=OperationalState.STOP,
                conditionField="DET.L3.PMP003.MotorCurrent",
                conditionOperator=ConditionOperator.LTE,
                conditionValue=1.0,
                rangeMin=None, rangeMax=1.0,
            ),
        ],
    ))

    # 4) Shanghai Pump-002 outlet pressure — Running / Idle / Stop
    rules.append(L2Rule(
        tagId=by_name["SHA.L2.PMP002.OutletPressure"].id,
        stateMapping=[
            StateMapping(
                state=OperationalState.RUNNING,
                conditionField="SHA.L2.PMP002.FlowRate",
                conditionOperator=ConditionOperator.GT,
                conditionValue=50.0,
                rangeMin=3.0, rangeMax=12.0,
            ),
            StateMapping(
                state=OperationalState.IDLE,
                conditionField="SHA.L2.PMP002.FlowRate",
                conditionOperator=ConditionOperator.BETWEEN,
                conditionValue=[5.0, 50.0],
                rangeMin=0.5, rangeMax=3.0,
            ),
            StateMapping(
                state=OperationalState.STOP,
                conditionField="SHA.L2.PMP002.FlowRate",
                conditionOperator=ConditionOperator.LTE,
                conditionValue=5.0,
                rangeMin=None, rangeMax=0.5,
            ),
        ],
    ))

    # 5) Detroit Motor-004 speed — Running / Idle / Stop
    rules.append(L2Rule(
        tagId=by_name["DET.L3.MOT004.Speed"].id,
        stateMapping=[
            StateMapping(
                state=OperationalState.RUNNING,
                conditionField="DET.L3.MOT004.Temperature",
                conditionOperator=ConditionOperator.GT,
                conditionValue=40.0,
                rangeMin=600.0, rangeMax=3000.0,
            ),
            StateMapping(
                state=OperationalState.IDLE,
                conditionField="DET.L3.MOT004.Temperature",
                conditionOperator=ConditionOperator.BETWEEN,
                conditionValue=[25.0, 40.0],
                rangeMin=50.0, rangeMax=600.0,
            ),
            StateMapping(
                state=OperationalState.STOP,
                conditionField="DET.L3.MOT004.Temperature",
                conditionOperator=ConditionOperator.LTE,
                conditionValue=25.0,
                rangeMin=None, rangeMax=50.0,
            ),
        ],
    ))

    return rules


# ══════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════
def seed() -> None:
    """Create containers and populate them with realistic sample data."""

    print("🔌 Connecting to Cosmos DB ...")
    client = get_cosmos_client()

    print("📦 Ensuring database & containers exist ...")
    ensure_containers(client)

    # Instantiate repository helpers (one per container)
    assets_repo = get_assets_repo()
    sources_repo = get_sources_repo()
    tags_repo = get_tags_repo()
    l1_repo = get_l1_rules_repo()
    l2_repo = get_l2_rules_repo()

    # ── Assets ───────────────────────────────────────────────────────
    print("\n🏭 Seeding assets (12) ...")
    assets = _build_assets()
    for asset in assets:
        _insert(assets_repo, asset, f"Asset  {asset.hierarchy}")

    # ── Sources ──────────────────────────────────────────────────────
    print("\n🔗 Seeding sources (6) ...")
    sources = _build_sources()
    for source in sources:
        _insert(sources_repo, source, f"Source {source.description}")

    # ── Tags ─────────────────────────────────────────────────────────
    tags = _build_tags(assets, sources)
    print(f"\n🏷️  Seeding tags ({len(tags)}) ...")
    for tag in tags:
        _insert(tags_repo, tag, f"Tag    {tag.name}  [{tag.status.value}]")

    # ── L1 Rules ─────────────────────────────────────────────────────
    l1_rules = _build_l1_rules(tags)
    print(f"\n📏 Seeding L1 rules ({len(l1_rules)}) ...")
    for rule in l1_rules:
        # Resolve the tag name for display
        tag_name = next(t.name for t in tags if t.id == rule.tagId)
        _insert(l1_repo, rule, f"L1Rule {tag_name}  [{rule.min}..{rule.max}]")

    # ── L2 Rules ─────────────────────────────────────────────────────
    l2_rules = _build_l2_rules(tags)
    print(f"\n🔀 Seeding L2 rules ({len(l2_rules)}) ...")
    for rule in l2_rules:
        tag_name = next(t.name for t in tags if t.id == rule.tagId)
        states = ", ".join(sm.state.value for sm in rule.stateMapping)
        _insert(l2_repo, rule, f"L2Rule {tag_name}  [{states}]")

    # ── Summary ──────────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print(f"  ✅ Seed complete!")
    print(f"     Assets:   {len(assets)}")
    print(f"     Sources:  {len(sources)}")
    print(f"     Tags:     {len(tags)}")
    print(f"     L1 Rules: {len(l1_rules)}")
    print(f"     L2 Rules: {len(l2_rules)}")
    print("═" * 60)


if __name__ == "__main__":
    seed()
