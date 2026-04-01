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

class ApprovalStatus(str, Enum):
    NONE = "none"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class Tag(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    unit: str                  # e.g., "bar", "°C", "RPM"
    datatype: DataType
    samplingFrequency: float   # seconds
    criticality: Criticality
    status: TagStatus = TagStatus.DRAFT
    approvalStatus: ApprovalStatus = ApprovalStatus.NONE
    rejectionReason: str | None = None
    assetId: str               # FK to Asset
    sourceId: str | None = None  # FK to Source, optional
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CreateTag(BaseModel):
    """Request body for POST /api/tags."""
    name: str
    description: str
    unit: str
    datatype: DataType
    samplingFrequency: float
    criticality: Criticality
    assetId: str
    sourceId: str | None = None


class UpdateTag(BaseModel):
    """Request body for PUT /api/tags/{id}. All fields optional for partial updates."""
    name: str | None = None
    description: str | None = None
    unit: str | None = None
    datatype: DataType | None = None
    samplingFrequency: float | None = None
    criticality: Criticality | None = None
    status: TagStatus | None = None
    sourceId: str | None = None
    assetId: str | None = None
