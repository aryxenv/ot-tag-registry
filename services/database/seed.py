"""Seed script — creates Cosmos DB containers and inserts realistic sample data.

Populates:
  * 21 assets across 3 sites (Luxembourg, Brussels, Amsterdam)
  * 5  data sources (PLC, SCADA, Historian)
  * 35 tags with deterministic names (including 4 intentionally inconsistent)
  * L1 range-validation rules (one per numeric tag)
  * 5  L2 state-profile rules (pump pressures, motor speeds)

Usage:
    cd services
    uv run python -m database.seed
"""

import sys
from pathlib import Path

# Resolve repo root for cross-package imports and .env loading
_repo_root = Path(__file__).resolve().parent.parent.parent

from dotenv import load_dotenv

load_dotenv(_repo_root / "server" / ".env")

# Add server/ to sys.path for cross-package imports (local-only)
sys.path.insert(0, str(_repo_root / "server"))

from database.cosmos_setup import ensure_containers, get_cosmos_client
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
from src.utils.db import (
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
# ASSETS — 21 pieces of equipment across LUX, BEL, NED
# ──────────────────────────────────────────────────────────────────────
def _build_assets() -> list[Asset]:
    """Return 21 assets across Luxembourg, Brussels, and Amsterdam."""

    # --- Plant-Luxembourg (LUX) — Lines 1–3 ---
    lux_l1_pmp001 = Asset(
        site="Plant-Luxembourg", line="Line-1", equipment="Pump-001",
        description="Primary coolant circulation pump",
    )
    lux_l1_mot001 = Asset(
        site="Plant-Luxembourg", line="Line-1", equipment="Motor-001",
        description="Coolant pump drive motor",
    )
    lux_l2_cmp001 = Asset(
        site="Plant-Luxembourg", line="Line-2", equipment="Compressor-001",
        description="Instrument-air compressor unit 1",
    )
    lux_l2_hex001 = Asset(
        site="Plant-Luxembourg", line="Line-2", equipment="HeatExchanger-001",
        description="Process cooling heat exchanger",
    )
    lux_l3_vlv001 = Asset(
        site="Plant-Luxembourg", line="Line-3", equipment="Valve-001",
        description="Steam header pressure-control valve",
    )
    lux_l3_tnk001 = Asset(
        site="Plant-Luxembourg", line="Line-3", equipment="Tank-001",
        description="Process liquid storage tank",
    )
    lux_l3_blr001 = Asset(
        site="Plant-Luxembourg", line="Line-3", equipment="Boiler-001",
        description="Steam generation boiler",
    )

    # --- Plant-Brussels (BEL) — Lines 1–3 ---
    bel_l1_pmp001 = Asset(
        site="Plant-Brussels", line="Line-1", equipment="Pump-001",
        description="Process water circulation pump",
    )
    bel_l1_cnv001 = Asset(
        site="Plant-Brussels", line="Line-1", equipment="Conveyor-001",
        description="Raw-material intake belt conveyor",
    )
    bel_l2_mot001 = Asset(
        site="Plant-Brussels", line="Line-2", equipment="Motor-001",
        description="VFD motor for compressor drive",
    )
    bel_l2_cmp001 = Asset(
        site="Plant-Brussels", line="Line-2", equipment="Compressor-001",
        description="Refrigerant compressor for chiller system",
    )
    bel_l3_vlv001 = Asset(
        site="Plant-Brussels", line="Line-3", equipment="Valve-001",
        description="Cooling water isolation valve",
    )
    bel_l3_tnk001 = Asset(
        site="Plant-Brussels", line="Line-3", equipment="Tank-001",
        description="Chemical dosing tank",
    )

    # --- Plant-Amsterdam (NED) — Lines 1–4 ---
    ned_l1_pmp001 = Asset(
        site="Plant-Amsterdam", line="Line-1", equipment="Pump-001",
        description="Boiler feed-water pump",
    )
    ned_l1_hex001 = Asset(
        site="Plant-Amsterdam", line="Line-1", equipment="HeatExchanger-001",
        description="Shell-and-tube heat exchanger",
    )
    ned_l2_mot001 = Asset(
        site="Plant-Amsterdam", line="Line-2", equipment="Motor-001",
        description="Compressor drive motor",
    )
    ned_l2_blr001 = Asset(
        site="Plant-Amsterdam", line="Line-2", equipment="Boiler-001",
        description="Natural gas fired boiler",
    )
    ned_l3_cnv001 = Asset(
        site="Plant-Amsterdam", line="Line-3", equipment="Conveyor-001",
        description="Raw-material intake conveyor",
    )
    ned_l3_vlv001 = Asset(
        site="Plant-Amsterdam", line="Line-3", equipment="Valve-001",
        description="Steam header control valve",
    )
    ned_l4_tnk001 = Asset(
        site="Plant-Amsterdam", line="Line-4", equipment="Tank-001",
        description="Raw-water storage tank",
    )
    ned_l4_cmp001 = Asset(
        site="Plant-Amsterdam", line="Line-4", equipment="Compressor-001",
        description="Air compressor unit 1",
    )

    return [
        lux_l1_pmp001, lux_l1_mot001, lux_l2_cmp001, lux_l2_hex001,
        lux_l3_vlv001, lux_l3_tnk001, lux_l3_blr001,
        bel_l1_pmp001, bel_l1_cnv001, bel_l2_mot001, bel_l2_cmp001,
        bel_l3_vlv001, bel_l3_tnk001,
        ned_l1_pmp001, ned_l1_hex001, ned_l2_mot001, ned_l2_blr001,
        ned_l3_cnv001, ned_l3_vlv001, ned_l4_tnk001, ned_l4_cmp001,
    ]


# ──────────────────────────────────────────────────────────────────────
# SOURCES
# ──────────────────────────────────────────────────────────────────────
def _build_sources() -> list[Source]:
    """Return 5 data-source definitions."""

    src_siemens = Source(
        systemType=SystemType.PLC,
        connectorType="OPC-UA",
        topicOrPath="opc.tcp://lux-plc01:4840/ns=2;s=S7-1500",
        description="Siemens S7-1500 PLC — Luxembourg plant floor",
    )
    src_schneider = Source(
        systemType=SystemType.PLC,
        connectorType="OPC-UA",
        topicOrPath="opc.tcp://bel-plc01:4840/ns=2;s=M340",
        description="Schneider Modicon M340 PLC — Brussels plant floor",
    )
    src_ignition = Source(
        systemType=SystemType.SCADA,
        connectorType="MQTT",
        topicOrPath="mqtt://lux-scada01:1883/plant-luxembourg/#",
        description="Ignition SCADA gateway — Luxembourg",
    )
    src_wonderware = Source(
        systemType=SystemType.SCADA,
        connectorType="MQTT",
        topicOrPath="mqtt://ned-scada01:1883/plant-amsterdam/#",
        description="Wonderware InTouch SCADA — Amsterdam",
    )
    src_aveva = Source(
        systemType=SystemType.HISTORIAN,
        connectorType="REST",
        topicOrPath="https://ned-hist01:8443/aveva/historian/v2",
        description="AVEVA Historian — Amsterdam",
    )

    return [src_siemens, src_schneider, src_ignition, src_wonderware, src_aveva]


# ──────────────────────────────────────────────────────────────────────
# TAGS — well-named tags matching golden tag vocabulary
# ──────────────────────────────────────────────────────────────────────
def _build_tags(assets: list[Asset], sources: list[Source]) -> list[Tag]:
    """Return ~35 tags wired to the given assets and sources."""

    # Destructure assets in creation order
    (
        lux_l1_pmp001, lux_l1_mot001, lux_l2_cmp001, lux_l2_hex001,
        lux_l3_vlv001, lux_l3_tnk001, lux_l3_blr001,
        bel_l1_pmp001, bel_l1_cnv001, bel_l2_mot001, bel_l2_cmp001,
        bel_l3_vlv001, bel_l3_tnk001,
        ned_l1_pmp001, ned_l1_hex001, ned_l2_mot001, ned_l2_blr001,
        ned_l3_cnv001, ned_l3_vlv001, ned_l4_tnk001, ned_l4_cmp001,
    ) = assets

    # Destructure sources
    src_siemens, src_schneider, src_ignition, src_wonderware, src_aveva = sources

    tags: list[Tag] = []

    # ── LUX Line-1 Pump-001 (3 tags) ────────────────────────────────
    tags.append(Tag(
        name="LUX.L1.PMP001.OutletPressure",
        description="Outlet pressure of primary coolant pump",
        unit="bar", datatype=DataType.FLOAT, samplingFrequency=1.0,
        criticality=Criticality.HIGH, status=TagStatus.ACTIVE,
        assetId=lux_l1_pmp001.id, sourceId=src_siemens.id,
    ))
    tags.append(Tag(
        name="LUX.L1.PMP001.FlowRate",
        description="Volumetric flow rate of primary coolant pump",
        unit="L/min", datatype=DataType.FLOAT, samplingFrequency=2.0,
        criticality=Criticality.HIGH, status=TagStatus.ACTIVE,
        assetId=lux_l1_pmp001.id, sourceId=src_siemens.id,
    ))
    tags.append(Tag(
        name="LUX.L1.PMP001.MotorCurrent",
        description="Motor winding current draw of pump 001",
        unit="A", datatype=DataType.FLOAT, samplingFrequency=1.0,
        criticality=Criticality.MEDIUM, status=TagStatus.ACTIVE,
        assetId=lux_l1_pmp001.id, sourceId=src_siemens.id,
    ))

    # ── LUX Line-1 Motor-001 (3 tags) ───────────────────────────────
    tags.append(Tag(
        name="LUX.L1.MOT001.Speed",
        description="Rotational speed of coolant pump drive motor",
        unit="RPM", datatype=DataType.FLOAT, samplingFrequency=1.0,
        criticality=Criticality.HIGH, status=TagStatus.ACTIVE,
        assetId=lux_l1_mot001.id, sourceId=src_siemens.id,
    ))
    tags.append(Tag(
        name="LUX.L1.MOT001.Temperature",
        description="Stator winding temperature of motor 001",
        unit="°C", datatype=DataType.FLOAT, samplingFrequency=10.0,
        criticality=Criticality.MEDIUM, status=TagStatus.ACTIVE,
        assetId=lux_l1_mot001.id, sourceId=src_siemens.id,
    ))
    tags.append(Tag(
        name="LUX.L1.MOT001.PowerConsumption",
        description="Active power consumption of motor 001",
        unit="kW", datatype=DataType.FLOAT, samplingFrequency=5.0,
        criticality=Criticality.LOW, status=TagStatus.ACTIVE,
        assetId=lux_l1_mot001.id, sourceId=src_siemens.id,
    ))

    # ── LUX Line-2 Compressor-001 (3 tags) ──────────────────────────
    tags.append(Tag(
        name="LUX.L2.CMP001.DischargeTemp",
        description="Discharge temperature of instrument-air compressor",
        unit="°C", datatype=DataType.FLOAT, samplingFrequency=5.0,
        criticality=Criticality.HIGH, status=TagStatus.ACTIVE,
        assetId=lux_l2_cmp001.id, sourceId=src_ignition.id,
    ))
    tags.append(Tag(
        name="LUX.L2.CMP001.InletPressure",
        description="Inlet suction pressure of compressor 001",
        unit="bar", datatype=DataType.FLOAT, samplingFrequency=5.0,
        criticality=Criticality.MEDIUM, status=TagStatus.ACTIVE,
        assetId=lux_l2_cmp001.id, sourceId=src_ignition.id,
    ))
    tags.append(Tag(
        name="LUX.L2.CMP001.VibrationLevel",
        description="Bearing vibration level of compressor 001",
        unit="mm/s", datatype=DataType.FLOAT, samplingFrequency=0.5,
        criticality=Criticality.CRITICAL, status=TagStatus.ACTIVE,
        assetId=lux_l2_cmp001.id, sourceId=src_ignition.id,
    ))

    # ── LUX Line-2 HeatExchanger-001 (1 tag — draft) ────────────────
    tags.append(Tag(
        name="LUX.L2.HEX001.InletTemp",
        description="Hot-side inlet temperature of heat exchanger 001",
        unit="°C", datatype=DataType.FLOAT, samplingFrequency=10.0,
        criticality=Criticality.MEDIUM, status=TagStatus.DRAFT,
        assetId=lux_l2_hex001.id, sourceId=src_ignition.id,
    ))

    # ── LUX Line-3 Boiler-001 (1 tag) ───────────────────────────────
    tags.append(Tag(
        name="LUX.L3.BLR001.SteamPressure",
        description="Steam output pressure of boiler 001",
        unit="bar", datatype=DataType.FLOAT, samplingFrequency=2.0,
        criticality=Criticality.HIGH, status=TagStatus.ACTIVE,
        assetId=lux_l3_blr001.id, sourceId=src_ignition.id,
    ))

    # ── BEL Line-1 Pump-001 (3 tags) ────────────────────────────────
    tags.append(Tag(
        name="BEL.L1.PMP001.OutletPressure",
        description="Discharge pressure of process water pump",
        unit="bar", datatype=DataType.FLOAT, samplingFrequency=1.0,
        criticality=Criticality.HIGH, status=TagStatus.ACTIVE,
        assetId=bel_l1_pmp001.id, sourceId=src_schneider.id,
    ))
    tags.append(Tag(
        name="BEL.L1.PMP001.FlowRate",
        description="Volumetric flow rate of process water pump",
        unit="L/min", datatype=DataType.FLOAT, samplingFrequency=2.0,
        criticality=Criticality.HIGH, status=TagStatus.ACTIVE,
        assetId=bel_l1_pmp001.id, sourceId=src_schneider.id,
    ))
    tags.append(Tag(
        name="BEL.L1.PMP001.BearingTemp",
        description="Pump bearing temperature on drive-end",
        unit="°C", datatype=DataType.FLOAT, samplingFrequency=10.0,
        criticality=Criticality.MEDIUM, status=TagStatus.ACTIVE,
        assetId=bel_l1_pmp001.id, sourceId=src_schneider.id,
    ))

    # ── BEL Line-1 Conveyor-001 (2 tags) ────────────────────────────
    tags.append(Tag(
        name="BEL.L1.CNV001.BeltSpeed",
        description="Belt linear speed of intake conveyor",
        unit="m/s", datatype=DataType.FLOAT, samplingFrequency=2.0,
        criticality=Criticality.MEDIUM, status=TagStatus.ACTIVE,
        assetId=bel_l1_cnv001.id, sourceId=src_schneider.id,
    ))
    tags.append(Tag(
        name="BEL.L1.CNV001.Running",
        description="Conveyor running status (true = running)",
        unit="-", datatype=DataType.BOOL, samplingFrequency=10.0,
        criticality=Criticality.LOW, status=TagStatus.ACTIVE,
        assetId=bel_l1_cnv001.id, sourceId=src_schneider.id,
    ))

    # ── BEL Line-2 Motor-001 (2 tags) ───────────────────────────────
    tags.append(Tag(
        name="BEL.L2.MOT001.Speed",
        description="Rotational speed of VFD motor 001",
        unit="RPM", datatype=DataType.FLOAT, samplingFrequency=1.0,
        criticality=Criticality.HIGH, status=TagStatus.ACTIVE,
        assetId=bel_l2_mot001.id, sourceId=src_schneider.id,
    ))
    tags.append(Tag(
        name="BEL.L2.MOT001.PowerConsumption",
        description="Active power consumption of motor 001",
        unit="kW", datatype=DataType.FLOAT, samplingFrequency=5.0,
        criticality=Criticality.LOW, status=TagStatus.ACTIVE,
        assetId=bel_l2_mot001.id, sourceId=src_schneider.id,
    ))

    # ── BEL Line-2 Compressor-001 (1 tag — retired) ─────────────────
    tags.append(Tag(
        name="BEL.L2.CMP001.DischargeTemp",
        description="Discharge temperature of refrigerant compressor",
        unit="°C", datatype=DataType.FLOAT, samplingFrequency=5.0,
        criticality=Criticality.HIGH, status=TagStatus.RETIRED,
        assetId=bel_l2_cmp001.id, sourceId=src_schneider.id,
    ))

    # ── BEL Line-3 Tank-001 (1 tag — draft) ─────────────────────────
    tags.append(Tag(
        name="BEL.L3.TNK001.Level",
        description="Liquid level in chemical dosing tank",
        unit="m", datatype=DataType.FLOAT, samplingFrequency=10.0,
        criticality=Criticality.MEDIUM, status=TagStatus.DRAFT,
        assetId=bel_l3_tnk001.id, sourceId=src_schneider.id,
    ))

    # ── NED Line-1 Pump-001 (3 tags) ────────────────────────────────
    tags.append(Tag(
        name="NED.L1.PMP001.OutletPressure",
        description="Outlet pressure of boiler feed-water pump",
        unit="bar", datatype=DataType.FLOAT, samplingFrequency=1.0,
        criticality=Criticality.CRITICAL, status=TagStatus.ACTIVE,
        assetId=ned_l1_pmp001.id, sourceId=src_aveva.id,
    ))
    tags.append(Tag(
        name="NED.L1.PMP001.FlowRate",
        description="Volumetric flow rate of boiler feed-water pump",
        unit="L/min", datatype=DataType.FLOAT, samplingFrequency=2.0,
        criticality=Criticality.HIGH, status=TagStatus.ACTIVE,
        assetId=ned_l1_pmp001.id, sourceId=src_aveva.id,
    ))
    tags.append(Tag(
        name="NED.L1.PMP001.MotorCurrent",
        description="Motor current draw of feed-water pump 001",
        unit="A", datatype=DataType.FLOAT, samplingFrequency=1.0,
        criticality=Criticality.MEDIUM, status=TagStatus.ACTIVE,
        assetId=ned_l1_pmp001.id, sourceId=src_aveva.id,
    ))

    # ── NED Line-2 Motor-001 (2 tags, 1 retired) ────────────────────
    tags.append(Tag(
        name="NED.L2.MOT001.Speed",
        description="Rotational speed of compressor drive motor",
        unit="RPM", datatype=DataType.FLOAT, samplingFrequency=1.0,
        criticality=Criticality.HIGH, status=TagStatus.ACTIVE,
        assetId=ned_l2_mot001.id, sourceId=src_wonderware.id,
    ))
    tags.append(Tag(
        name="NED.L2.MOT001.BearingTemp",
        description="Drive-end bearing temperature of motor 001",
        unit="°C", datatype=DataType.FLOAT, samplingFrequency=10.0,
        criticality=Criticality.MEDIUM, status=TagStatus.RETIRED,
        assetId=ned_l2_mot001.id, sourceId=src_wonderware.id,
    ))

    # ── NED Line-2 Boiler-001 (1 tag) ───────────────────────────────
    tags.append(Tag(
        name="NED.L2.BLR001.SteamPressure",
        description="Steam drum pressure of boiler 001",
        unit="bar", datatype=DataType.FLOAT, samplingFrequency=2.0,
        criticality=Criticality.HIGH, status=TagStatus.ACTIVE,
        assetId=ned_l2_blr001.id, sourceId=src_wonderware.id,
    ))

    # ── NED Line-3 Conveyor-001 (2 tags) ────────────────────────────
    tags.append(Tag(
        name="NED.L3.CNV001.BeltSpeed",
        description="Belt speed of raw-material intake conveyor",
        unit="m/s", datatype=DataType.FLOAT, samplingFrequency=2.0,
        criticality=Criticality.MEDIUM, status=TagStatus.ACTIVE,
        assetId=ned_l3_cnv001.id, sourceId=src_wonderware.id,
    ))
    tags.append(Tag(
        name="NED.L3.CNV001.LoadWeight",
        description="Instantaneous belt load weight of conveyor",
        unit="kg", datatype=DataType.FLOAT, samplingFrequency=5.0,
        criticality=Criticality.LOW, status=TagStatus.DRAFT,
        assetId=ned_l3_cnv001.id, sourceId=src_wonderware.id,
    ))

    # ── NED Line-4 Compressor-001 (1 tag) ────────────────────────────
    tags.append(Tag(
        name="NED.L4.CMP001.VibrationLevel",
        description="Bearing vibration of air compressor 001",
        unit="mm/s", datatype=DataType.FLOAT, samplingFrequency=0.5,
        criticality=Criticality.CRITICAL, status=TagStatus.ACTIVE,
        assetId=ned_l4_cmp001.id, sourceId=src_aveva.id,
    ))

    # ── NED Line-4 Tank-001 (1 tag — draft) ──────────────────────────
    tags.append(Tag(
        name="NED.L4.TNK001.Level",
        description="Liquid level in raw-water storage tank",
        unit="m", datatype=DataType.FLOAT, samplingFrequency=10.0,
        criticality=Criticality.MEDIUM, status=TagStatus.DRAFT,
        assetId=ned_l4_tnk001.id, sourceId=src_aveva.id,
    ))

    # ══════════════════════════════════════════════════════════════════
    # INTENTIONALLY INCONSISTENT TAGS — demo the naming problem
    # These bypass API validation (inserted directly via repository).
    # ══════════════════════════════════════════════════════════════════

    # 1) Underscores instead of dots
    tags.append(Tag(
        name="LUX_L2_CMP001_InletPressure",
        description="Suction inlet pressure of compressor 001",
        unit="bar", datatype=DataType.FLOAT, samplingFrequency=5.0,
        criticality=Criticality.MEDIUM, status=TagStatus.DRAFT,
        assetId=lux_l2_cmp001.id, sourceId=src_ignition.id,
    ))

    # 2) All lowercase
    tags.append(Tag(
        name="brussels.line2.motor001.speed",
        description="Rotational speed of motor in Brussels plant",
        unit="RPM", datatype=DataType.FLOAT, samplingFrequency=1.0,
        criticality=Criticality.HIGH, status=TagStatus.DRAFT,
        assetId=bel_l2_mot001.id, sourceId=src_schneider.id,
    ))

    # 3) Hyphens instead of dots
    tags.append(Tag(
        name="NED-L3-CNV001-BeltSpeed",
        description="Belt speed of raw-material intake conveyor",
        unit="m/s", datatype=DataType.FLOAT, samplingFrequency=2.0,
        criticality=Criticality.MEDIUM, status=TagStatus.DRAFT,
        assetId=ned_l3_cnv001.id, sourceId=src_wonderware.id,
    ))

    # 4) Wrong segment order + underscores + informal naming
    tags.append(Tag(
        name="Vibration_CMP001_Amsterdam",
        description="Vibration sensor on air compressor in Amsterdam",
        unit="mm/s", datatype=DataType.FLOAT, samplingFrequency=0.5,
        criticality=Criticality.CRITICAL, status=TagStatus.DRAFT,
        assetId=ned_l4_cmp001.id, sourceId=src_aveva.id,
    ))

    return tags


# ──────────────────────────────────────────────────────────────────────
# L1 RULES — one per numeric (float) tag
# ──────────────────────────────────────────────────────────────────────
# Physical-range lookup keyed by the measurement suffix of a tag name.
_L1_RANGES: dict[str, dict] = {
    "OutletPressure":   dict(min=0.0, max=16.0, spikeThreshold=5.0),
    "InletPressure":    dict(min=0.0, max=16.0, spikeThreshold=5.0),
    "SteamPressure":    dict(min=0.0, max=25.0, spikeThreshold=8.0),
    "DischargeTemp":    dict(min=-20.0, max=200.0, spikeThreshold=30.0),
    "Temperature":      dict(min=-20.0, max=200.0, spikeThreshold=30.0),
    "InletTemp":        dict(min=-20.0, max=200.0, spikeThreshold=30.0),
    "BearingTemp":      dict(min=0.0, max=150.0, spikeThreshold=20.0),
    "FlowRate":         dict(min=0.0, max=500.0, spikeThreshold=100.0),
    "MotorCurrent":     dict(min=0.0, max=100.0, spikeThreshold=20.0),
    "Speed":            dict(min=0.0, max=3600.0, spikeThreshold=500.0),
    "PowerConsumption": dict(min=0.0, max=500.0, spikeThreshold=100.0),
    "VibrationLevel":   dict(min=0.0, max=25.0, spikeThreshold=10.0),
    "BeltSpeed":        dict(min=0.0, max=5.0, spikeThreshold=2.0),
    "LoadWeight":       dict(min=0.0, max=2000.0, spikeThreshold=500.0),
    "Position":         dict(min=0.0, max=100.0, spikeThreshold=30.0),
    "Level":            dict(min=0.0, max=20.0, spikeThreshold=5.0),
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
        # Extract the final segment after the last separator (or use full name
        # for inconsistently-named tags where rsplit may not find a dot).
        measurement = tag.name.rsplit(".", maxsplit=1)[-1]
        # Also try splitting on underscores/hyphens for inconsistent names
        if measurement == tag.name:
            measurement = tag.name.rsplit("_", maxsplit=1)[-1]
        if measurement == tag.name:
            measurement = tag.name.rsplit("-", maxsplit=1)[-1]
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

    by_name: dict[str, Tag] = {t.name: t for t in tags}

    rules: list[L2Rule] = []

    # 1) LUX Pump-001 outlet pressure — Running / Idle / Stop
    rules.append(L2Rule(
        tagId=by_name["LUX.L1.PMP001.OutletPressure"].id,
        stateMapping=[
            StateMapping(
                state=OperationalState.RUNNING,
                conditionField="LUX.L1.PMP001.MotorCurrent",
                conditionOperator=ConditionOperator.GT,
                conditionValue=5.0,
                rangeMin=4.0, rangeMax=14.0,
            ),
            StateMapping(
                state=OperationalState.IDLE,
                conditionField="LUX.L1.PMP001.MotorCurrent",
                conditionOperator=ConditionOperator.BETWEEN,
                conditionValue=[0.5, 5.0],
                rangeMin=0.5, rangeMax=4.0,
            ),
            StateMapping(
                state=OperationalState.STOP,
                conditionField="LUX.L1.PMP001.MotorCurrent",
                conditionOperator=ConditionOperator.LTE,
                conditionValue=0.5,
                rangeMin=None, rangeMax=0.5,
            ),
        ],
    ))

    # 2) LUX Motor-001 speed — Running / Idle / Stop
    rules.append(L2Rule(
        tagId=by_name["LUX.L1.MOT001.Speed"].id,
        stateMapping=[
            StateMapping(
                state=OperationalState.RUNNING,
                conditionField="LUX.L1.MOT001.PowerConsumption",
                conditionOperator=ConditionOperator.GT,
                conditionValue=10.0,
                rangeMin=900.0, rangeMax=3600.0,
            ),
            StateMapping(
                state=OperationalState.IDLE,
                conditionField="LUX.L1.MOT001.PowerConsumption",
                conditionOperator=ConditionOperator.BETWEEN,
                conditionValue=[1.0, 10.0],
                rangeMin=50.0, rangeMax=900.0,
            ),
            StateMapping(
                state=OperationalState.STOP,
                conditionField="LUX.L1.MOT001.PowerConsumption",
                conditionOperator=ConditionOperator.LTE,
                conditionValue=1.0,
                rangeMin=None, rangeMax=50.0,
            ),
        ],
    ))

    # 3) BEL Pump-001 outlet pressure — Running / Idle / Stop
    rules.append(L2Rule(
        tagId=by_name["BEL.L1.PMP001.OutletPressure"].id,
        stateMapping=[
            StateMapping(
                state=OperationalState.RUNNING,
                conditionField="BEL.L1.PMP001.FlowRate",
                conditionOperator=ConditionOperator.GT,
                conditionValue=50.0,
                rangeMin=4.0, rangeMax=14.0,
            ),
            StateMapping(
                state=OperationalState.IDLE,
                conditionField="BEL.L1.PMP001.FlowRate",
                conditionOperator=ConditionOperator.BETWEEN,
                conditionValue=[5.0, 50.0],
                rangeMin=0.5, rangeMax=4.0,
            ),
            StateMapping(
                state=OperationalState.STOP,
                conditionField="BEL.L1.PMP001.FlowRate",
                conditionOperator=ConditionOperator.LTE,
                conditionValue=5.0,
                rangeMin=None, rangeMax=0.5,
            ),
        ],
    ))

    # 4) NED Pump-001 outlet pressure — Running / Idle / Stop
    rules.append(L2Rule(
        tagId=by_name["NED.L1.PMP001.OutletPressure"].id,
        stateMapping=[
            StateMapping(
                state=OperationalState.RUNNING,
                conditionField="NED.L1.PMP001.MotorCurrent",
                conditionOperator=ConditionOperator.GT,
                conditionValue=8.0,
                rangeMin=6.0, rangeMax=15.0,
            ),
            StateMapping(
                state=OperationalState.IDLE,
                conditionField="NED.L1.PMP001.MotorCurrent",
                conditionOperator=ConditionOperator.BETWEEN,
                conditionValue=[1.0, 8.0],
                rangeMin=1.0, rangeMax=6.0,
            ),
            StateMapping(
                state=OperationalState.STOP,
                conditionField="NED.L1.PMP001.MotorCurrent",
                conditionOperator=ConditionOperator.LTE,
                conditionValue=1.0,
                rangeMin=None, rangeMax=1.0,
            ),
        ],
    ))

    # 5) BEL Motor-001 speed — Running / Idle / Stop
    rules.append(L2Rule(
        tagId=by_name["BEL.L2.MOT001.Speed"].id,
        stateMapping=[
            StateMapping(
                state=OperationalState.RUNNING,
                conditionField="BEL.L2.MOT001.PowerConsumption",
                conditionOperator=ConditionOperator.GT,
                conditionValue=10.0,
                rangeMin=600.0, rangeMax=3000.0,
            ),
            StateMapping(
                state=OperationalState.IDLE,
                conditionField="BEL.L2.MOT001.PowerConsumption",
                conditionOperator=ConditionOperator.BETWEEN,
                conditionValue=[1.0, 10.0],
                rangeMin=50.0, rangeMax=600.0,
            ),
            StateMapping(
                state=OperationalState.STOP,
                conditionField="BEL.L2.MOT001.PowerConsumption",
                conditionOperator=ConditionOperator.LTE,
                conditionValue=1.0,
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
    assets = _build_assets()
    print(f"\n🏭 Seeding assets ({len(assets)}) ...")
    for asset in assets:
        _insert(assets_repo, asset, f"Asset  {asset.hierarchy}")

    # ── Sources ──────────────────────────────────────────────────────
    sources = _build_sources()
    print(f"\n🔗 Seeding sources ({len(sources)}) ...")
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
