"""Unit tests for the deterministic tag naming validator."""

import re
from pathlib import Path

import pytest

from src.validators.naming_validator import (
    NamingSchema,
    SegmentRule,
    ValidationResult,
    load_schema,
    validate_tag_name,
)

# ---------------------------------------------------------------------------
# Default schema tests
# ---------------------------------------------------------------------------


class TestLoadSchema:
    def test_loads_default_config(self):
        schema = load_schema()
        assert schema.separator == "."
        assert len(schema.segments) == 5
        assert schema.segments[0].name == "site"
        assert schema.segments[4].name == "detail"
        assert schema.segments[4].required is False

    def test_min_max_segments(self):
        schema = load_schema()
        assert schema.min_segments == 4  # site, line, equipment, measurement
        assert schema.max_segments == 5  # + detail


# ---------------------------------------------------------------------------
# Valid names
# ---------------------------------------------------------------------------


class TestValidNames:
    def test_four_segments(self):
        result = validate_tag_name("MUN.L2.PMP001.OutletPressure")
        assert result.valid is True
        assert result.errors == []

    def test_five_segments(self):
        result = validate_tag_name("Munich.Line2.Pump001.Pressure.Discharge")
        assert result.valid is True
        assert result.errors == []

    def test_minimal_valid(self):
        result = validate_tag_name("A1.B2.C3.D4")
        assert result.valid is True


# ---------------------------------------------------------------------------
# Invalid names — structural
# ---------------------------------------------------------------------------


class TestStructuralErrors:
    def test_empty_name(self):
        result = validate_tag_name("")
        assert result.valid is False
        assert any("empty" in e.message.lower() for e in result.errors)

    def test_leading_separator(self):
        result = validate_tag_name(".MUN.L2.PMP001.Pressure")
        assert result.valid is False
        assert any("start" in e.message.lower() for e in result.errors)

    def test_trailing_separator(self):
        result = validate_tag_name("MUN.L2.PMP001.Pressure.")
        assert result.valid is False
        assert any("end" in e.message.lower() for e in result.errors)

    def test_consecutive_separators(self):
        result = validate_tag_name("MUN..L2.PMP001.Pressure")
        assert result.valid is False
        assert any("consecutive" in e.message.lower() for e in result.errors)


# ---------------------------------------------------------------------------
# Invalid names — segment count
# ---------------------------------------------------------------------------


class TestSegmentCount:
    def test_too_few_segments(self):
        result = validate_tag_name("MUN.L2.PMP001")
        assert result.valid is False
        assert any("too few" in e.message.lower() for e in result.errors)

    def test_single_segment(self):
        result = validate_tag_name("JustOnePart")
        assert result.valid is False

    def test_too_many_segments(self):
        result = validate_tag_name("A.B.C.D.E.F")
        assert result.valid is False
        assert any("too many" in e.message.lower() for e in result.errors)


# ---------------------------------------------------------------------------
# Invalid names — pattern violations
# ---------------------------------------------------------------------------


class TestPatternViolations:
    def test_lowercase_start(self):
        result = validate_tag_name("mun.L2.PMP001.Pressure")
        assert result.valid is False
        assert result.errors[0].segment == "site"

    def test_special_characters(self):
        result = validate_tag_name("MUN.L2.PMP-001.Pressure")
        assert result.valid is False
        assert result.errors[0].segment == "equipment"

    def test_underscore_rejected(self):
        result = validate_tag_name("MUN.L2.PMP_001.Pressure")
        assert result.valid is False

    def test_space_in_segment(self):
        result = validate_tag_name("MUN.L2.PMP 001.Pressure")
        assert result.valid is False


# ---------------------------------------------------------------------------
# Allowed values
# ---------------------------------------------------------------------------


class TestAllowedValues:
    def test_allowed_values_pass(self):
        schema = NamingSchema(
            separator=".",
            segments=[
                SegmentRule(
                    name="site",
                    required=True,
                    allowed_values=["MUN", "BER"],
                ),
                SegmentRule(name="line", required=True),
                SegmentRule(name="equipment", required=True),
                SegmentRule(name="measurement", required=True),
            ],
        )
        result = validate_tag_name("MUN.L2.PMP001.Pressure", schema=schema)
        assert result.valid is True

    def test_allowed_values_rejected(self):
        schema = NamingSchema(
            separator=".",
            segments=[
                SegmentRule(
                    name="site",
                    required=True,
                    allowed_values=["MUN", "BER"],
                ),
                SegmentRule(name="line", required=True),
                SegmentRule(name="equipment", required=True),
                SegmentRule(name="measurement", required=True),
            ],
        )
        result = validate_tag_name("HAM.L2.PMP001.Pressure", schema=schema)
        assert result.valid is False
        assert result.errors[0].segment == "site"
        assert "not an allowed value" in result.errors[0].message


# ---------------------------------------------------------------------------
# Custom schema
# ---------------------------------------------------------------------------


class TestCustomSchema:
    def test_custom_separator(self):
        schema = NamingSchema(
            separator="/",
            segments=[
                SegmentRule(name="area", required=True),
                SegmentRule(name="device", required=True),
            ],
        )
        result = validate_tag_name("Plant/Pump", schema=schema)
        assert result.valid is True

    def test_custom_pattern(self):
        schema = NamingSchema(
            separator=".",
            segments=[
                SegmentRule(
                    name="code",
                    required=True,
                    pattern=re.compile(r"^[0-9]{3}$"),
                ),
                SegmentRule(name="name", required=True),
            ],
        )
        assert validate_tag_name("123.Pump", schema=schema).valid is True
        assert validate_tag_name("12.Pump", schema=schema).valid is False
        assert validate_tag_name("ABC.Pump", schema=schema).valid is False
