from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field

class DataType(str, Enum):
    FLOAT = "float"
    INT = "int"
    BOOL = "bool"
    STRING = "string"

class Criticality(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TagStatus(str, Enum):
    ACTIVE = "active"
    RETIRED = "retired"
    DRAFT = "draft"

class Tag(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    unit: str                  # e.g., "bar", "°C", "RPM"
    datatype: DataType
    samplingFrequency: float   # seconds
    criticality: Criticality
    status: TagStatus = TagStatus.DRAFT
    assetId: str               # FK to Asset
    sourceId: str | None = None  # FK to Source, optional
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
