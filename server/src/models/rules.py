from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field, model_validator

class MissingDataPolicy(str, Enum):
    IGNORE = "ignore"
    ALERT = "alert"
    INTERPOLATE = "interpolate"
    LAST_KNOWN = "last-known"

class L1Rule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    tagId: str                 # FK to Tag
    min: float | None = None
    max: float | None = None
    missingDataPolicy: MissingDataPolicy = MissingDataPolicy.ALERT
    spikeThreshold: float | None = None
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OperationalState(str, Enum):
    RUNNING = "Running"
    IDLE = "Idle"
    STOP = "Stop"

class ConditionOperator(str, Enum):
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    EQ = "=="
    NE = "!="
    BETWEEN = "between"

class StateMapping(BaseModel):
    state: OperationalState
    conditionField: str        # which tag/signal determines this state
    conditionOperator: ConditionOperator
    conditionValue: float | list[float]  # single value or [min, max] for "between"
    rangeMin: float | None = None
    rangeMax: float | None = None

class L2Rule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    tagId: str                 # FK to Tag
    stateMapping: list[StateMapping]
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Request / update bodies
# ---------------------------------------------------------------------------


class CreateL1Rule(BaseModel):
    """Request body for POST /api/tags/{tag_id}/rules/l1."""
    min: float | None = None
    max: float | None = None
    missingDataPolicy: MissingDataPolicy = MissingDataPolicy.ALERT
    spikeThreshold: float | None = None

    @model_validator(mode="after")
    def at_least_one_threshold(self) -> "CreateL1Rule":
        if self.min is None and self.max is None and self.spikeThreshold is None:
            raise ValueError(
                "At least one of 'min', 'max', or 'spikeThreshold' must be set"
            )
        return self


class UpdateL1Rule(BaseModel):
    """Request body for PUT /api/tags/{tag_id}/rules/l1. All fields optional."""
    min: float | None = None
    max: float | None = None
    missingDataPolicy: MissingDataPolicy | None = None
    spikeThreshold: float | None = None


class CreateL2Rule(BaseModel):
    """Request body for POST /api/tags/{tag_id}/rules/l2."""
    stateMapping: list[StateMapping] = Field(min_length=1)


class UpdateL2Rule(BaseModel):
    """Request body for PUT /api/tags/{tag_id}/rules/l2. All fields optional."""
    stateMapping: list[StateMapping] | None = None
