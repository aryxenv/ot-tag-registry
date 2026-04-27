Simple app for manual entries on Tag Registry (OT Ownership)

Today, tag definitions/rules are often scattered (Excel, emails, local know-how). That creates:

- inconsistent tag naming and semantics across sites
- unclear ownership (OT vs IT vs integrator)
- slow onboarding for new sensors/tags and rework in analytics

Objective of the demo

Show a lightweight business app where Site OT can:

- create / update / retire tags in a governed way
- define "physical truth" rules as configuration (not code)
- request validation/approval when needed

Key data objects (MDM-style)

- Asset (site, line, equipment, hierarchy)
- Tag (name, description, unit, datatype, sampling frequency, criticality)
- Source (PLC/SCADA/Historians, connector, topic/path)
- L1 Rules (Range): min/max, missing data policy, spike threshold
- L2 Rules (State Profile): mapping to operating modes (Running/Idle/Stop), state-dependent ranges
