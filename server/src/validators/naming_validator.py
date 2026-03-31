"""Deterministic tag naming validator.

Enforces a configurable naming schema (e.g. ``SITE.LINE.EQUIPMENT.MEASUREMENT``)
loaded from a JSON config file.  Returns structured validation errors.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Schema dataclasses
# ---------------------------------------------------------------------------

_CONFIG_PATH = Path(__file__).parent / "naming_config.json"


@dataclass
class SegmentRule:
    """Defines constraints for a single segment in the tag name."""

    name: str
    required: bool
    pattern: re.Pattern[str] | None = None
    allowed_values: list[str] | None = None


@dataclass
class NamingSchema:
    """Ordered list of segment rules plus the separator character."""

    separator: str
    segments: list[SegmentRule]

    @property
    def min_segments(self) -> int:
        return sum(1 for s in self.segments if s.required)

    @property
    def max_segments(self) -> int:
        return len(self.segments)


# ---------------------------------------------------------------------------
# Validation result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ValidationError:
    segment: str
    message: str
    received: str
    expected: str | None = None


@dataclass
class ValidationResult:
    valid: bool
    errors: list[ValidationError] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Schema loading
# ---------------------------------------------------------------------------


def load_schema(config_path: Path | str | None = None) -> NamingSchema:
    """Load a ``NamingSchema`` from a JSON config file."""
    path = Path(config_path) if config_path else _CONFIG_PATH
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)

    segments: list[SegmentRule] = []
    for seg in raw["segments"]:
        pattern = re.compile(seg["pattern"]) if seg.get("pattern") else None
        segments.append(
            SegmentRule(
                name=seg["name"],
                required=seg["required"],
                pattern=pattern,
                allowed_values=seg.get("allowed_values"),
            )
        )
    return NamingSchema(separator=raw["separator"], segments=segments)


# Module-level cached schema (lazy-loaded on first validation call)
_cached_schema: NamingSchema | None = None


def _get_schema() -> NamingSchema:
    global _cached_schema
    if _cached_schema is None:
        _cached_schema = load_schema()
    return _cached_schema


def reset_schema_cache() -> None:
    """Clear the cached schema — useful for tests that swap configs."""
    global _cached_schema
    _cached_schema = None


# ---------------------------------------------------------------------------
# Core validation logic
# ---------------------------------------------------------------------------


def validate_tag_name(
    name: str,
    schema: NamingSchema | None = None,
) -> ValidationResult:
    """Validate *name* against the naming *schema*.

    If *schema* is ``None`` the default schema from config is used.
    """
    schema = schema or _get_schema()
    errors: list[ValidationError] = []

    # --- structural checks ------------------------------------------------

    if not name:
        errors.append(
            ValidationError(
                segment="name",
                message="Tag name must not be empty",
                received="",
            )
        )
        return ValidationResult(valid=False, errors=errors)

    sep = schema.separator

    # Leading / trailing separator
    if name.startswith(sep):
        errors.append(
            ValidationError(
                segment="name",
                message="Tag name must not start with the separator",
                received=name,
                expected=f"no leading '{sep}'",
            )
        )
    if name.endswith(sep):
        errors.append(
            ValidationError(
                segment="name",
                message="Tag name must not end with the separator",
                received=name,
                expected=f"no trailing '{sep}'",
            )
        )

    # Consecutive separators
    if sep * 2 in name:
        errors.append(
            ValidationError(
                segment="name",
                message="Tag name must not contain consecutive separators",
                received=name,
                expected=f"no '{sep}{sep}'",
            )
        )

    # If structural problems found, return early
    if errors:
        return ValidationResult(valid=False, errors=errors)

    # --- segment-level checks ---------------------------------------------

    parts = name.split(sep)
    num_parts = len(parts)
    min_seg = schema.min_segments
    max_seg = schema.max_segments

    if num_parts < min_seg:
        errors.append(
            ValidationError(
                segment="name",
                message=f"Too few segments: expected at least {min_seg}, got {num_parts}",
                received=name,
                expected=f"{min_seg}–{max_seg} segments",
            )
        )
        return ValidationResult(valid=False, errors=errors)

    if num_parts > max_seg:
        errors.append(
            ValidationError(
                segment="name",
                message=f"Too many segments: expected at most {max_seg}, got {num_parts}",
                received=name,
                expected=f"{min_seg}–{max_seg} segments",
            )
        )
        return ValidationResult(valid=False, errors=errors)

    # Validate each provided segment
    for idx, value in enumerate(parts):
        rule = schema.segments[idx]

        # Empty segment
        if not value:
            errors.append(
                ValidationError(
                    segment=rule.name,
                    message=f"Segment '{rule.name}' must not be empty",
                    received="",
                )
            )
            continue

        # Pattern check
        if rule.pattern and not rule.pattern.match(value):
            errors.append(
                ValidationError(
                    segment=rule.name,
                    message=f"Segment '{rule.name}' does not match required pattern",
                    received=value,
                    expected=rule.pattern.pattern,
                )
            )

        # Allowed values check
        if rule.allowed_values is not None and value not in rule.allowed_values:
            errors.append(
                ValidationError(
                    segment=rule.name,
                    message=f"Segment '{rule.name}' is not an allowed value",
                    received=value,
                    expected=f"one of {rule.allowed_values}",
                )
            )

    return ValidationResult(valid=len(errors) == 0, errors=errors)
