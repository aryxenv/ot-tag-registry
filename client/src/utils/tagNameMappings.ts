/**
 * Hardcoded mapping dictionaries for converting asset display names
 * to tag name code segments.
 *
 * Tag name format: SITE.LINE.EQUIPMENT.MEASUREMENT.UNIT.ID
 * Example: LUX.L1.PMP001.Pressure.Bar.1
 */

const SITE_CODES: Record<string, string> = {
  "Plant-Luxembourg": "LUX",
  "Plant-Brussels": "BEL",
  "Plant-Amsterdam": "NED",
};

const EQUIPMENT_PREFIXES: Record<string, string> = {
  Pump: "PMP",
  Compressor: "CMP",
  Motor: "MOT",
  Conveyor: "CNV",
  Valve: "VLV",
  HeatExchanger: "HEX",
  Boiler: "BLR",
  Tank: "TNK",
};

const UNIT_TO_MEASUREMENT: Record<string, string> = {
  bar: "Pressure",
  Pa: "Pressure",
  "°C": "Temperature",
  "°F": "Temperature",
  RPM: "Speed",
  "m/s": "Velocity",
  "L/min": "FlowRate",
  "m³/h": "FlowRate",
  kW: "Power",
  A: "Current",
  V: "Voltage",
  "%": "Level",
  m: "Level",
  "mm/s": "Vibration",
  kg: "Weight",
  "kg/m³": "Density",
  Hz: "Frequency",
  Nm: "Torque",
  pH: "Acidity",
  "%RH": "Humidity",
  "—": "Status",
  "-": "Status",
};

const UNIT_CODE: Record<string, string> = {
  bar: "Bar",
  Pa: "Pa",
  "°C": "Cel",
  "°F": "Fah",
  RPM: "Rpm",
  "m/s": "Ms",
  "L/min": "Lpm",
  "m³/h": "Cmh",
  kW: "KW",
  A: "Amp",
  V: "Volt",
  "%": "Pct",
  m: "M",
  "mm/s": "Mms",
  kg: "Kg",
  "kg/m³": "Kgm3",
  Hz: "Hz",
  Nm: "Nm",
  pH: "Ph",
  "%RH": "Rh",
  "—": "Bool",
  "-": "Bool",
};

function siteCode(site: string): string {
  return SITE_CODES[site] ?? "";
}

function lineCode(line: string): string {
  return line.replace("Line-", "L");
}

function equipmentCode(equipment: string): string {
  const dashIdx = equipment.indexOf("-");
  if (dashIdx === -1) return equipment;
  const type = equipment.substring(0, dashIdx);
  const num = equipment.substring(dashIdx + 1);
  const prefix = EQUIPMENT_PREFIXES[type] ?? type.substring(0, 3).toUpperCase();
  return prefix + num.replace(/-/g, "").padStart(3, "0");
}

function measurementFromUnit(unit: string): string {
  if (UNIT_TO_MEASUREMENT[unit]) return UNIT_TO_MEASUREMENT[unit];
  const cleaned = unit.replace(/[^a-zA-Z0-9]/g, "");
  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1) || "";
}

function unitCode(unit: string): string {
  if (UNIT_CODE[unit]) return UNIT_CODE[unit];
  const cleaned = unit.replace(/[^a-zA-Z0-9]/g, "");
  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1) || "";
}

/**
 * Generate the base tag name (without the ID suffix) from form field values.
 * Returns empty string if any required field is missing.
 */
export function generateBaseTagName(
  site: string,
  line: string,
  equipment: string,
  unit: string,
): string {
  const s = siteCode(site);
  const l = lineCode(line);
  const e = equipmentCode(equipment);
  const m = measurementFromUnit(unit);
  const u = unitCode(unit);
  if (!s || !l || !e || !m || !u) return "";
  return `${s}.${l}.${e}.${m}.${u}`;
}
