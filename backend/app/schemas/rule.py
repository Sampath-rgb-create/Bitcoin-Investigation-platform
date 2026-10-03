from typing import Optional
from pydantic import BaseModel, Field


class CustomRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    target_entity: str = Field("wallet", pattern="^(wallet|transaction)$")
    field: str = Field(..., min_length=1, max_length=64)
    operator: str = Field(..., pattern="^(>|>=|<|<=|==|!=|contains)$")
    threshold: float
    severity: str = Field("medium", pattern="^(low|medium|high|critical)$")
    weight: float = Field(1.0, ge=0.0, le=10.0)
    enabled: int = Field(1, ge=0, le=1)


class CustomRuleCreate(CustomRuleBase):
    pass


class CustomRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_entity: Optional[str] = None
    field: Optional[str] = None
    operator: Optional[str] = None
    threshold: Optional[float] = None
    severity: Optional[str] = None
    weight: Optional[float] = None
    enabled: Optional[int] = None


class CustomRuleOut(CustomRuleBase):
    id: str
    case_id: Optional[str] = None
    created_by: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
