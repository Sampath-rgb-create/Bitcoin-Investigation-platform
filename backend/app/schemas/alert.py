from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ScoreComponents(BaseModel):
    anomaly_score: float
    behavior_score: float
    graph_score: float
    network_score: float


class AlertOut(BaseModel):
    alert_id: str
    run_id: str
    entity_id: str
    severity: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    priority_score: float
    score_components: ScoreComponents
    correlation_strength: float
    evidence_coverage: float
    top_reasons: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    laya: Optional[Dict] = None
    ollama_summary: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    items: List[AlertOut]
    total: int
    page: int
    page_size: int
