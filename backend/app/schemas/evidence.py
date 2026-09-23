from typing import Any, List, Optional
from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    """
    Evidence item schema conforming to PROTOTYPE.md Section 5.16
    Classes: 'observed', 'derived', 'detector', 'inferred'
    """
    evidence_id: str
    class_: str = Field(..., alias="class")
    source_record_ids: List[str] = Field(default_factory=list)
    entity_id: str
    feature: Optional[str] = None
    value: Optional[Any] = None
    baseline: Optional[Any] = None
    unit: Optional[str] = None
    description: str

    model_config = {"populate_by_name": True}


class DeterministicReason(BaseModel):
    """
    Deterministic reason schema conforming to PROTOTYPE.md Section 5.17
    """
    reason_id: str
    type: str  # 'feature', 'rule', 'graph', 'network'
    feature: Optional[str] = None
    value: Optional[Any] = None
    threshold_or_baseline: Optional[Any] = None
    source_evidence_ids: List[str] = Field(default_factory=list)
    text: str


class AlertEvidencePack(BaseModel):
    alert_id: str
    entity_id: str
    severity: str = "LOW"
    priority_score: float
    score_components: Optional[dict] = None
    source_records: List[str] = Field(default_factory=list)
    reasons: List[Any] = Field(default_factory=list)
    evidence_items: List[EvidenceItem] = Field(default_factory=list)

