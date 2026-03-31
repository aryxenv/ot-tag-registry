"""Golden tag dataset — 54 curated OT tag definitions for the AI Search index.

Each entry represents an *approved* tag name in the naming registry.  The
``seed_index.py`` script reads these, generates embeddings, and uploads them
to the ``golden-tags`` Azure AI Search index.

Sites: Luxembourg (LUX), Belgium (BEL), France (FRA)
"""

GOLDEN_TAGS: list[dict] = [
    # ╔═══════════════════════════════════════════════════════════════════╗
    # ║  LUX — Luxembourg                                               ║
    # ╚═══════════════════════════════════════════════════════════════════╝

    # ── LUX Line-1 Pump-001 ─────────────────────────────────────────────
    {
        "tagName": "LUX.L1.PMP001.OutletPressure",
        "site": "LUX", "line": "L1", "equipment": "PMP001",
        "unit": "bar", "datatype": "float",
        "description": "Outlet pressure of primary coolant pump",
        "measurementTokens": "outlet pressure discharge",
        "synonyms": "pump discharge pressure head pressure",
    },
    {
        "tagName": "LUX.L1.PMP001.FlowRate",
        "site": "LUX", "line": "L1", "equipment": "PMP001",
        "unit": "L/min", "datatype": "float",
        "description": "Volumetric flow rate of primary coolant pump",
        "measurementTokens": "flow rate volume throughput",
        "synonyms": "volumetric flow pump output liquid flow",
    },
    {
        "tagName": "LUX.L1.PMP001.MotorCurrent",
        "site": "LUX", "line": "L1", "equipment": "PMP001",
        "unit": "A", "datatype": "float",
        "description": "Motor winding current draw of pump 001",
        "measurementTokens": "motor current amperage draw",
        "synonyms": "winding current amp draw electrical current",
    },
    {
        "tagName": "LUX.L1.PMP001.InletPressure",
        "site": "LUX", "line": "L1", "equipment": "PMP001",
        "unit": "bar", "datatype": "float",
        "description": "Suction inlet pressure of primary coolant pump",
        "measurementTokens": "inlet pressure suction",
        "synonyms": "suction pressure intake pressure",
    },

    # ── LUX Line-1 Motor-001 ────────────────────────────────────────────
    {
        "tagName": "LUX.L1.MOT001.Speed",
        "site": "LUX", "line": "L1", "equipment": "MOT001",
        "unit": "RPM", "datatype": "float",
        "description": "Rotational speed of coolant pump drive motor",
        "measurementTokens": "speed rpm rotational",
        "synonyms": "motor speed rotation shaft speed revolutions",
    },
    {
        "tagName": "LUX.L1.MOT001.Temperature",
        "site": "LUX", "line": "L1", "equipment": "MOT001",
        "unit": "°C", "datatype": "float",
        "description": "Stator winding temperature of motor 001",
        "measurementTokens": "temperature winding stator",
        "synonyms": "motor temp winding temperature thermal",
    },
    {
        "tagName": "LUX.L1.MOT001.PowerConsumption",
        "site": "LUX", "line": "L1", "equipment": "MOT001",
        "unit": "kW", "datatype": "float",
        "description": "Active power consumption of motor 001",
        "measurementTokens": "power consumption active energy",
        "synonyms": "energy use power draw wattage electrical power",
    },
    {
        "tagName": "LUX.L1.MOT001.VibrationLevel",
        "site": "LUX", "line": "L1", "equipment": "MOT001",
        "unit": "mm/s", "datatype": "float",
        "description": "Bearing vibration level of motor 001",
        "measurementTokens": "vibration bearing level",
        "synonyms": "vibration amplitude oscillation bearing vibration",
    },
    {
        "tagName": "LUX.L1.MOT001.Torque",
        "site": "LUX", "line": "L1", "equipment": "MOT001",
        "unit": "Nm", "datatype": "float",
        "description": "Output shaft torque of motor 001",
        "measurementTokens": "torque shaft output",
        "synonyms": "rotational force moment turning force",
    },

    # ── LUX Line-2 Compressor-001 ───────────────────────────────────────
    {
        "tagName": "LUX.L2.CMP001.DischargeTemp",
        "site": "LUX", "line": "L2", "equipment": "CMP001",
        "unit": "°C", "datatype": "float",
        "description": "Discharge temperature of instrument-air compressor",
        "measurementTokens": "discharge temperature outlet temp",
        "synonyms": "outlet temperature exhaust temp compressor discharge",
    },
    {
        "tagName": "LUX.L2.CMP001.InletPressure",
        "site": "LUX", "line": "L2", "equipment": "CMP001",
        "unit": "bar", "datatype": "float",
        "description": "Inlet suction pressure of compressor 001",
        "measurementTokens": "inlet pressure suction",
        "synonyms": "suction pressure intake pressure low-side pressure",
    },
    {
        "tagName": "LUX.L2.CMP001.VibrationLevel",
        "site": "LUX", "line": "L2", "equipment": "CMP001",
        "unit": "mm/s", "datatype": "float",
        "description": "Bearing vibration level of compressor 001",
        "measurementTokens": "vibration bearing level",
        "synonyms": "vibration amplitude oscillation mechanical vibration",
    },
    {
        "tagName": "LUX.L2.CMP001.OutletPressure",
        "site": "LUX", "line": "L2", "equipment": "CMP001",
        "unit": "bar", "datatype": "float",
        "description": "Discharge outlet pressure of compressor 001",
        "measurementTokens": "outlet pressure discharge",
        "synonyms": "discharge pressure high-side pressure head pressure",
    },

    # ── LUX Line-2 HeatExchanger-001 ────────────────────────────────────
    {
        "tagName": "LUX.L2.HEX001.InletTemp",
        "site": "LUX", "line": "L2", "equipment": "HEX001",
        "unit": "°C", "datatype": "float",
        "description": "Hot-side inlet temperature of heat exchanger 001",
        "measurementTokens": "inlet temperature hot side",
        "synonyms": "entry temperature incoming temp feed temperature",
    },
    {
        "tagName": "LUX.L2.HEX001.OutletTemp",
        "site": "LUX", "line": "L2", "equipment": "HEX001",
        "unit": "°C", "datatype": "float",
        "description": "Hot-side outlet temperature of heat exchanger 001",
        "measurementTokens": "outlet temperature hot side exit",
        "synonyms": "exit temperature outgoing temp return temperature",
    },
    {
        "tagName": "LUX.L2.HEX001.DifferentialPressure",
        "site": "LUX", "line": "L2", "equipment": "HEX001",
        "unit": "bar", "datatype": "float",
        "description": "Differential pressure across heat exchanger 001",
        "measurementTokens": "differential pressure drop delta",
        "synonyms": "pressure drop delta P pressure difference",
    },

    # ── LUX Line-3 Valve-001 ────────────────────────────────────────────
    {
        "tagName": "LUX.L3.VLV001.Position",
        "site": "LUX", "line": "L3", "equipment": "VLV001",
        "unit": "%", "datatype": "float",
        "description": "Valve stem position (0% closed, 100% open)",
        "measurementTokens": "position opening percentage",
        "synonyms": "valve opening stroke position travel",
    },
    {
        "tagName": "LUX.L3.VLV001.OpenClose",
        "site": "LUX", "line": "L3", "equipment": "VLV001",
        "unit": "-", "datatype": "bool",
        "description": "Discrete open/close limit-switch feedback",
        "measurementTokens": "open close status",
        "synonyms": "valve state limit switch on off",
    },

    # ── LUX Line-3 Tank-001 ─────────────────────────────────────────────
    {
        "tagName": "LUX.L3.TNK001.Level",
        "site": "LUX", "line": "L3", "equipment": "TNK001",
        "unit": "m", "datatype": "float",
        "description": "Liquid level in storage tank 001",
        "measurementTokens": "level height fill",
        "synonyms": "tank level fill level liquid height fluid level",
    },
    {
        "tagName": "LUX.L3.TNK001.Temperature",
        "site": "LUX", "line": "L3", "equipment": "TNK001",
        "unit": "°C", "datatype": "float",
        "description": "Liquid temperature inside storage tank 001",
        "measurementTokens": "temperature tank liquid",
        "synonyms": "tank temperature fluid temp process temperature",
    },
    {
        "tagName": "LUX.L3.TNK001.Pressure",
        "site": "LUX", "line": "L3", "equipment": "TNK001",
        "unit": "bar", "datatype": "float",
        "description": "Internal pressure of storage tank 001",
        "measurementTokens": "pressure tank internal",
        "synonyms": "vessel pressure tank pressure headspace pressure",
    },

    # ── LUX Line-3 Boiler-001 ───────────────────────────────────────────
    {
        "tagName": "LUX.L3.BLR001.SteamPressure",
        "site": "LUX", "line": "L3", "equipment": "BLR001",
        "unit": "bar", "datatype": "float",
        "description": "Steam output pressure of boiler 001",
        "measurementTokens": "steam pressure output",
        "synonyms": "boiler pressure steam header drum pressure",
    },
    {
        "tagName": "LUX.L3.BLR001.FeedWaterTemp",
        "site": "LUX", "line": "L3", "equipment": "BLR001",
        "unit": "°C", "datatype": "float",
        "description": "Feed-water inlet temperature of boiler 001",
        "measurementTokens": "feed water temperature inlet",
        "synonyms": "make-up water temp boiler feed temperature",
    },

    # ╔═══════════════════════════════════════════════════════════════════╗
    # ║  BEL — Belgium                                                   ║
    # ╚═══════════════════════════════════════════════════════════════════╝

    # ── BEL Line-1 Pump-001 ─────────────────────────────────────────────
    {
        "tagName": "BEL.L1.PMP001.OutletPressure",
        "site": "BEL", "line": "L1", "equipment": "PMP001",
        "unit": "bar", "datatype": "float",
        "description": "Discharge pressure of process water pump",
        "measurementTokens": "outlet pressure discharge",
        "synonyms": "pump discharge pressure head pressure",
    },
    {
        "tagName": "BEL.L1.PMP001.FlowRate",
        "site": "BEL", "line": "L1", "equipment": "PMP001",
        "unit": "L/min", "datatype": "float",
        "description": "Volumetric flow rate of process water pump",
        "measurementTokens": "flow rate volume throughput",
        "synonyms": "volumetric flow pump output water flow",
    },
    {
        "tagName": "BEL.L1.PMP001.BearingTemp",
        "site": "BEL", "line": "L1", "equipment": "PMP001",
        "unit": "°C", "datatype": "float",
        "description": "Pump bearing temperature on drive-end",
        "measurementTokens": "bearing temperature drive end",
        "synonyms": "bearing temp DE bearing pump bearing thermal",
    },
    {
        "tagName": "BEL.L1.PMP001.Running",
        "site": "BEL", "line": "L1", "equipment": "PMP001",
        "unit": "-", "datatype": "bool",
        "description": "Pump running status (true = running)",
        "measurementTokens": "running status active",
        "synonyms": "run status on off operating pump status",
    },

    # ── BEL Line-1 Conveyor-001 ─────────────────────────────────────────
    {
        "tagName": "BEL.L1.CNV001.BeltSpeed",
        "site": "BEL", "line": "L1", "equipment": "CNV001",
        "unit": "m/s", "datatype": "float",
        "description": "Belt linear speed of intake conveyor",
        "measurementTokens": "belt speed linear velocity",
        "synonyms": "conveyor speed belt velocity line speed",
    },
    {
        "tagName": "BEL.L1.CNV001.LoadWeight",
        "site": "BEL", "line": "L1", "equipment": "CNV001",
        "unit": "kg", "datatype": "float",
        "description": "Instantaneous belt load weight on conveyor",
        "measurementTokens": "load weight mass belt",
        "synonyms": "belt load material weight conveyor weight",
    },
    {
        "tagName": "BEL.L1.CNV001.Running",
        "site": "BEL", "line": "L1", "equipment": "CNV001",
        "unit": "-", "datatype": "bool",
        "description": "Conveyor running status (true = running)",
        "measurementTokens": "running status active",
        "synonyms": "run status on off conveyor operating",
    },
    {
        "tagName": "BEL.L1.CNV001.MotorCurrent",
        "site": "BEL", "line": "L1", "equipment": "CNV001",
        "unit": "A", "datatype": "float",
        "description": "Drive motor current of conveyor 001",
        "measurementTokens": "motor current amperage draw",
        "synonyms": "drive current amp draw electrical current",
    },

    # ── BEL Line-2 Motor-001 ────────────────────────────────────────────
    {
        "tagName": "BEL.L2.MOT001.Speed",
        "site": "BEL", "line": "L2", "equipment": "MOT001",
        "unit": "RPM", "datatype": "float",
        "description": "Rotational speed of VFD motor 001",
        "measurementTokens": "speed rpm rotational",
        "synonyms": "motor speed rotation shaft speed VFD speed",
    },
    {
        "tagName": "BEL.L2.MOT001.PowerConsumption",
        "site": "BEL", "line": "L2", "equipment": "MOT001",
        "unit": "kW", "datatype": "float",
        "description": "Active power consumption of motor 001",
        "measurementTokens": "power consumption active energy",
        "synonyms": "energy use power draw wattage electrical power",
    },
    {
        "tagName": "BEL.L2.MOT001.Torque",
        "site": "BEL", "line": "L2", "equipment": "MOT001",
        "unit": "Nm", "datatype": "float",
        "description": "Output shaft torque of motor 001",
        "measurementTokens": "torque shaft output",
        "synonyms": "rotational force moment turning force",
    },

    # ── BEL Line-2 Compressor-001 ───────────────────────────────────────
    {
        "tagName": "BEL.L2.CMP001.DischargeTemp",
        "site": "BEL", "line": "L2", "equipment": "CMP001",
        "unit": "°C", "datatype": "float",
        "description": "Discharge temperature of refrigerant compressor",
        "measurementTokens": "discharge temperature outlet temp",
        "synonyms": "outlet temperature exhaust temp compressor discharge",
    },
    {
        "tagName": "BEL.L2.CMP001.OutletPressure",
        "site": "BEL", "line": "L2", "equipment": "CMP001",
        "unit": "bar", "datatype": "float",
        "description": "Discharge pressure of refrigerant compressor",
        "measurementTokens": "outlet pressure discharge",
        "synonyms": "discharge pressure high-side pressure head pressure",
    },
    {
        "tagName": "BEL.L2.CMP001.OilTemp",
        "site": "BEL", "line": "L2", "equipment": "CMP001",
        "unit": "°C", "datatype": "float",
        "description": "Lubricating oil temperature of compressor 001",
        "measurementTokens": "oil temperature lubrication",
        "synonyms": "lube oil temp lubricant temperature oil thermal",
    },

    # ── BEL Line-3 Valve-001 ────────────────────────────────────────────
    {
        "tagName": "BEL.L3.VLV001.Position",
        "site": "BEL", "line": "L3", "equipment": "VLV001",
        "unit": "%", "datatype": "float",
        "description": "Control valve position — cooling water",
        "measurementTokens": "position opening percentage",
        "synonyms": "valve opening stroke position travel",
    },
    {
        "tagName": "BEL.L3.VLV001.OpenClose",
        "site": "BEL", "line": "L3", "equipment": "VLV001",
        "unit": "-", "datatype": "bool",
        "description": "Discrete open/close status of isolation valve",
        "measurementTokens": "open close status",
        "synonyms": "valve state limit switch on off",
    },

    # ── BEL Line-3 Tank-001 ─────────────────────────────────────────────
    {
        "tagName": "BEL.L3.TNK001.Level",
        "site": "BEL", "line": "L3", "equipment": "TNK001",
        "unit": "m", "datatype": "float",
        "description": "Liquid level in chemical dosing tank",
        "measurementTokens": "level height fill",
        "synonyms": "tank level fill level liquid height",
    },
    {
        "tagName": "BEL.L3.TNK001.pH",
        "site": "BEL", "line": "L3", "equipment": "TNK001",
        "unit": "pH", "datatype": "float",
        "description": "pH value of solution in dosing tank",
        "measurementTokens": "pH acidity alkalinity",
        "synonyms": "acid level alkalinity hydrogen ion concentration",
    },
    {
        "tagName": "BEL.L3.TNK001.Density",
        "site": "BEL", "line": "L3", "equipment": "TNK001",
        "unit": "kg/m³", "datatype": "float",
        "description": "Liquid density in chemical dosing tank",
        "measurementTokens": "density specific gravity",
        "synonyms": "fluid density specific gravity mass per volume",
    },

    # ╔═══════════════════════════════════════════════════════════════════╗
    # ║  FRA — France                                                    ║
    # ╚═══════════════════════════════════════════════════════════════════╝

    # ── FRA Line-1 Pump-001 ─────────────────────────────────────────────
    {
        "tagName": "FRA.L1.PMP001.OutletPressure",
        "site": "FRA", "line": "L1", "equipment": "PMP001",
        "unit": "bar", "datatype": "float",
        "description": "Outlet pressure of boiler feed-water pump",
        "measurementTokens": "outlet pressure discharge",
        "synonyms": "pump discharge pressure head pressure",
    },
    {
        "tagName": "FRA.L1.PMP001.FlowRate",
        "site": "FRA", "line": "L1", "equipment": "PMP001",
        "unit": "L/min", "datatype": "float",
        "description": "Volumetric flow rate of boiler feed-water pump",
        "measurementTokens": "flow rate volume throughput",
        "synonyms": "volumetric flow pump output feed water flow",
    },
    {
        "tagName": "FRA.L1.PMP001.MotorCurrent",
        "site": "FRA", "line": "L1", "equipment": "PMP001",
        "unit": "A", "datatype": "float",
        "description": "Motor current draw of feed-water pump 001",
        "measurementTokens": "motor current amperage draw",
        "synonyms": "winding current amp draw electrical current",
    },
    {
        "tagName": "FRA.L1.PMP001.VibrationLevel",
        "site": "FRA", "line": "L1", "equipment": "PMP001",
        "unit": "mm/s", "datatype": "float",
        "description": "Pump casing vibration level on drive-end",
        "measurementTokens": "vibration casing level",
        "synonyms": "vibration amplitude oscillation pump vibration",
    },

    # ── FRA Line-1 HeatExchanger-001 ────────────────────────────────────
    {
        "tagName": "FRA.L1.HEX001.InletTemp",
        "site": "FRA", "line": "L1", "equipment": "HEX001",
        "unit": "°C", "datatype": "float",
        "description": "Shell-side inlet temperature of heat exchanger",
        "measurementTokens": "inlet temperature shell side",
        "synonyms": "entry temperature incoming temp feed temperature",
    },
    {
        "tagName": "FRA.L1.HEX001.OutletTemp",
        "site": "FRA", "line": "L1", "equipment": "HEX001",
        "unit": "°C", "datatype": "float",
        "description": "Shell-side outlet temperature of heat exchanger",
        "measurementTokens": "outlet temperature shell side exit",
        "synonyms": "exit temperature outgoing temp return temperature",
    },
    {
        "tagName": "FRA.L1.HEX001.FlowRate",
        "site": "FRA", "line": "L1", "equipment": "HEX001",
        "unit": "L/min", "datatype": "float",
        "description": "Tube-side flow rate through heat exchanger",
        "measurementTokens": "flow rate tube side throughput",
        "synonyms": "heat exchanger flow cooling flow process flow",
    },

    # ── FRA Line-2 Motor-001 ────────────────────────────────────────────
    {
        "tagName": "FRA.L2.MOT001.Speed",
        "site": "FRA", "line": "L2", "equipment": "MOT001",
        "unit": "RPM", "datatype": "float",
        "description": "Rotational speed of compressor drive motor",
        "measurementTokens": "speed rpm rotational",
        "synonyms": "motor speed rotation shaft speed revolutions",
    },
    {
        "tagName": "FRA.L2.MOT001.BearingTemp",
        "site": "FRA", "line": "L2", "equipment": "MOT001",
        "unit": "°C", "datatype": "float",
        "description": "Drive-end bearing temperature of motor 001",
        "measurementTokens": "bearing temperature drive end",
        "synonyms": "bearing temp DE bearing motor bearing thermal",
    },
    {
        "tagName": "FRA.L2.MOT001.MotorCurrent",
        "site": "FRA", "line": "L2", "equipment": "MOT001",
        "unit": "A", "datatype": "float",
        "description": "Phase current of motor 001",
        "measurementTokens": "motor current amperage phase",
        "synonyms": "winding current amp draw phase current",
    },

    # ── FRA Line-2 Boiler-001 ───────────────────────────────────────────
    {
        "tagName": "FRA.L2.BLR001.SteamPressure",
        "site": "FRA", "line": "L2", "equipment": "BLR001",
        "unit": "bar", "datatype": "float",
        "description": "Steam drum pressure of boiler 001",
        "measurementTokens": "steam pressure drum",
        "synonyms": "boiler pressure steam header drum pressure",
    },
    {
        "tagName": "FRA.L2.BLR001.ExhaustTemp",
        "site": "FRA", "line": "L2", "equipment": "BLR001",
        "unit": "°C", "datatype": "float",
        "description": "Flue gas exhaust temperature of boiler 001",
        "measurementTokens": "exhaust temperature flue gas",
        "synonyms": "stack temperature flue temp combustion exhaust",
    },
    {
        "tagName": "FRA.L2.BLR001.FeedWaterTemp",
        "site": "FRA", "line": "L2", "equipment": "BLR001",
        "unit": "°C", "datatype": "float",
        "description": "Feed-water inlet temperature of boiler 001",
        "measurementTokens": "feed water temperature inlet",
        "synonyms": "make-up water temp boiler feed temperature",
    },
    {
        "tagName": "FRA.L2.BLR001.FuelFlowRate",
        "site": "FRA", "line": "L2", "equipment": "BLR001",
        "unit": "m³/h", "datatype": "float",
        "description": "Natural gas fuel flow rate to boiler 001",
        "measurementTokens": "fuel flow rate gas consumption",
        "synonyms": "gas flow fuel consumption burner flow rate",
    },

    # ── FRA Line-3 Conveyor-001 ─────────────────────────────────────────
    {
        "tagName": "FRA.L3.CNV001.BeltSpeed",
        "site": "FRA", "line": "L3", "equipment": "CNV001",
        "unit": "m/s", "datatype": "float",
        "description": "Belt speed of raw-material intake conveyor",
        "measurementTokens": "belt speed linear velocity",
        "synonyms": "conveyor speed belt velocity line speed",
    },
    {
        "tagName": "FRA.L3.CNV001.LoadWeight",
        "site": "FRA", "line": "L3", "equipment": "CNV001",
        "unit": "kg", "datatype": "float",
        "description": "Instantaneous belt load weight of conveyor",
        "measurementTokens": "load weight mass belt",
        "synonyms": "belt load material weight conveyor weight",
    },
    {
        "tagName": "FRA.L3.CNV001.MotorCurrent",
        "site": "FRA", "line": "L3", "equipment": "CNV001",
        "unit": "A", "datatype": "float",
        "description": "Drive motor current of conveyor 001",
        "measurementTokens": "motor current amperage draw",
        "synonyms": "drive current amp draw electrical current",
    },

    # ── FRA Line-3 Valve-001 ────────────────────────────────────────────
    {
        "tagName": "FRA.L3.VLV001.Position",
        "site": "FRA", "line": "L3", "equipment": "VLV001",
        "unit": "%", "datatype": "float",
        "description": "Control valve stem position — steam header",
        "measurementTokens": "position opening percentage",
        "synonyms": "valve opening stroke position travel",
    },

    # ── FRA Line-4 Tank-001 ─────────────────────────────────────────────
    {
        "tagName": "FRA.L4.TNK001.Level",
        "site": "FRA", "line": "L4", "equipment": "TNK001",
        "unit": "m", "datatype": "float",
        "description": "Liquid level in raw-water storage tank",
        "measurementTokens": "level height fill",
        "synonyms": "tank level fill level liquid height water level",
    },
    {
        "tagName": "FRA.L4.TNK001.Temperature",
        "site": "FRA", "line": "L4", "equipment": "TNK001",
        "unit": "°C", "datatype": "float",
        "description": "Water temperature in raw-water tank",
        "measurementTokens": "temperature water tank",
        "synonyms": "tank temperature water temp process temperature",
    },
    {
        "tagName": "FRA.L4.TNK001.Pressure",
        "site": "FRA", "line": "L4", "equipment": "TNK001",
        "unit": "bar", "datatype": "float",
        "description": "Headspace pressure of raw-water tank",
        "measurementTokens": "pressure headspace tank",
        "synonyms": "vessel pressure tank pressure internal pressure",
    },
    {
        "tagName": "FRA.L4.TNK001.Humidity",
        "site": "FRA", "line": "L4", "equipment": "TNK001",
        "unit": "%RH", "datatype": "float",
        "description": "Relative humidity in tank enclosure area",
        "measurementTokens": "humidity relative moisture",
        "synonyms": "relative humidity moisture content RH ambient humidity",
    },

    # ── FRA Line-4 Compressor-001 ───────────────────────────────────────
    {
        "tagName": "FRA.L4.CMP001.DischargeTemp",
        "site": "FRA", "line": "L4", "equipment": "CMP001",
        "unit": "°C", "datatype": "float",
        "description": "Discharge temperature of air compressor",
        "measurementTokens": "discharge temperature outlet temp",
        "synonyms": "outlet temperature exhaust temp air compressor discharge",
    },
    {
        "tagName": "FRA.L4.CMP001.InletPressure",
        "site": "FRA", "line": "L4", "equipment": "CMP001",
        "unit": "bar", "datatype": "float",
        "description": "Suction inlet pressure of air compressor",
        "measurementTokens": "inlet pressure suction",
        "synonyms": "suction pressure intake pressure atmospheric pressure",
    },
    {
        "tagName": "FRA.L4.CMP001.VibrationLevel",
        "site": "FRA", "line": "L4", "equipment": "CMP001",
        "unit": "mm/s", "datatype": "float",
        "description": "Bearing vibration of air compressor 001",
        "measurementTokens": "vibration bearing level",
        "synonyms": "vibration amplitude oscillation compressor vibration",
    },
    {
        "tagName": "FRA.L4.CMP001.Running",
        "site": "FRA", "line": "L4", "equipment": "CMP001",
        "unit": "-", "datatype": "bool",
        "description": "Compressor running status (true = running)",
        "measurementTokens": "running status active",
        "synonyms": "run status on off compressor operating",
    },
]
