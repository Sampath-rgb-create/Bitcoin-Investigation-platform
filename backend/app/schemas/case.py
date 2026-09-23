from typing import Optional
from pydantic import BaseModel, Field


class CaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class CaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  # 'open', 'archived'


class CaseOut(BaseModel):
    case_id: str
    name: str
    description: Optional[str] = None
    status: str
    created_by: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
