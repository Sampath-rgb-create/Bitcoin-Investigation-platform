from typing import Optional
from pydantic import BaseModel, Field, field_validator


class FeedbackCreate(BaseModel):
    label: str = Field(..., description="Allowed: relevant, benign, needs_review")
    note: Optional[str] = None

    @field_validator("label")
    @classmethod
    def validate_label(cls, v: str) -> str:
        allowed = {"relevant", "benign", "needs_review"}
        if v not in allowed:
            raise ValueError(f"Label must be one of {allowed}")
        return v


class FeedbackOut(BaseModel):
    id: str
    alert_id: str
    user_id: str
    label: str
    note: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}
