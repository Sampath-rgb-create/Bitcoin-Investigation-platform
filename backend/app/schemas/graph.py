from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str  # e.g., 'wallet:W123', 'transaction:TX1'
    type: str  # 'wallet', 'transaction', 'ip', 'asn', 'country'
    label: str
    attributes: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str  # 'INPUT_TO', 'OUTPUT_TO', 'OBSERVED', 'BELONGS_TO_ASN', 'GEOLOCATED_TO', 'NEXT_TX'
    basis: str
    source_record_ids: List[str] = Field(default_factory=list)
    weight: Optional[float] = 1.0
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None


class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    truncated: bool = False
    total_nodes: int
    total_edges: int
