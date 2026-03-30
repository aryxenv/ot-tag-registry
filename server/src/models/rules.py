from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field

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
