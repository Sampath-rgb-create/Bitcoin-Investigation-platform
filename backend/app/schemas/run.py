from typing import Dict, Optional
from pydantic import BaseModel, Field


class DetectorConfig(BaseModel):
    isolation_forest: bool = True
    behavior_rules: bool = True
    graph_signals: bool = True
    network_signals: bool = True


class IsolationForestConfig(BaseModel):
    n_estimators: int = 300
    contamination: str = "auto"
    random_state: int = 42


class CorrelationConfig(BaseModel):
    allow_temporal: bool = False
    window_seconds: int = 30


class AIConfig(BaseModel):
    enable_laya: bool = False
    enable_ollama: bool = False


class RunCreateRequest(BaseModel):
    detectors: DetectorConfig = Field(default_factory=DetectorConfig)
    isolation_forest: IsolationForestConfig = Field(default_factory=IsolationForestConfig)
    correlation: CorrelationConfig = Field(default_factory=CorrelationConfig)
    ai: AIConfig = Field(default_factory=AIConfig)


class RunOut(BaseModel):
    run_id: str
    case_id: str
    status: str  # 'queued', 'running', 'completed', 'failed', 'cancelled'
    stage: str
    progress: int
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}
