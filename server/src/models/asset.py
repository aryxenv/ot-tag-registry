from datetime import datetime, timezone
from uuid import uuid4
from pydantic import BaseModel, Field, model_validator

class Asset(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    site: str          # e.g., "Plant-Munich"
    line: str          # e.g., "Line-2"
    equipment: str     # e.g., "Pump-001"
    hierarchy: str = "" # computed: site.line.equipment
    description: str | None = None
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="before")
    @classmethod
    def compute_hierarchy(cls, data):
        if isinstance(data, dict):
            site = data.get("site", "")
            line = data.get("line", "")
            equipment = data.get("equipment", "")
            if site and line and equipment:
                data["hierarchy"] = f"{site}.{line}.{equipment}"
        return data
