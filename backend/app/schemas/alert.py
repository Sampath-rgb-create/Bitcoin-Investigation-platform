from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ScoreComponents(BaseModel):
    supervised_score: float = 0.0
    unsupervised_score: float = 0.0
    anomaly_score: float = 0.0
    behavior_score: float = 0.0
    graph_score: float = 0.0
    rule_score: float = 0.0
    network_score: float = 0.0


class AlertOut(BaseModel):
    alert_id: str
    run_id: str
    entity_id: str
    severity: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    priority_score: float
    supervised_score: float = 0.0
    unsupervised_score: float = 0.0
    graph_score: float = 0.0
    rule_score: float = 0.0
    score_components: ScoreComponents
    correlation_strength: float = 0.0
    evidence_coverage: float = 0.0
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
