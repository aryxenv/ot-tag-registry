from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field

class SystemType(str, Enum):
    PLC = "PLC"
    SCADA = "SCADA"
    HISTORIAN = "Historian"
    OTHER = "Other"

class Source(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    systemType: SystemType
    connectorType: str         # e.g., "OPC-UA", "MQTT", "Modbus"
    topicOrPath: str           # the address/topic for this data source
    description: str | None = None
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CreateSource(BaseModel):
    """Request body for POST /api/sources."""
    systemType: SystemType
    connectorType: str
    topicOrPath: str
    description: str | None = None
