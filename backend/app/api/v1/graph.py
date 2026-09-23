import json
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.db.models import Case, User
from backend.app.schemas.graph import GraphResponse, GraphNode, GraphEdge
from backend.app.api.deps import get_current_user

router = APIRouter()


@router.get("/cases/{case_id}/graph", response_model=GraphResponse)
def get_case_graph(
    case_id: str,
    run_id: Optional[str] = Query(None),
    min_priority_score: Optional[float] = Query(None),
    node_type: Optional[str] = Query(None),
    include_ips: bool = Query(True),
    limit: int = Query(500, ge=10, le=5000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve entity graph nodes and edges for cytoscape visualization.
    Loads from case-level graph.json if available.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' was not found",
        )

    graph_file = Path(settings.DATA_DIR) / "cases" / case_id / "graph" / "graph.json"
    if graph_file.exists():
        try:
            with open(graph_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "elements" in data and isinstance(data["elements"], dict):
                    raw_nodes = data["elements"].get("nodes", [])
                    raw_edges = data["elements"].get("edges", [])
                    nodes = [n.get("data", n) for n in raw_nodes]
                    edges = [e.get("data", e) for e in raw_edges]
                else:
                    nodes = data.get("nodes", [])
                    edges = data.get("edges", [])

                if not include_ips:
                    nodes = [n for n in nodes if n.get("type") != "ip"]
                    edges = [e for e in edges if e.get("type") not in ("OBSERVED", "RELAYED_BY")]

                if node_type:
                    nodes = [n for n in nodes if n.get("type") == node_type]

                truncated = len(nodes) > limit
                nodes = nodes[:limit]
                node_ids = {n["id"] for n in nodes if "id" in n}
                edges = [e for e in edges if e.get("source") in node_ids and e.get("target") in node_ids]

                def make_attrs(n_dict):
                    if "attributes" in n_dict and n_dict["attributes"]:
                        return n_dict["attributes"]
                    return {k: v for k, v in n_dict.items() if k not in ("id", "type", "label")}

                return GraphResponse(
                    nodes=[GraphNode(id=n["id"], type=n.get("type", "unknown"), label=n.get("label", n["id"]), attributes=make_attrs(n)) for n in nodes if "id" in n],
                    edges=[GraphEdge(id=e.get("id", f"{e['source']}->{e['target']}"), source=e["source"], target=e["target"], type=e.get("type", "unknown"), basis=e.get("basis", ""), source_record_ids=e.get("source_record_ids", []), weight=float(e.get("weight", 1.0) or 1.0), first_seen=e.get("first_seen"), last_seen=e.get("last_seen")) for e in edges if "source" in e and "target" in e],
                    truncated=truncated,
                    total_nodes=len(raw_nodes) if "raw_nodes" in locals() else len(data.get("nodes", [])),
                    total_edges=len(raw_edges) if "raw_edges" in locals() else len(data.get("edges", [])),
                )
        except Exception:
            pass

    # Fallback to empty graph
    return GraphResponse(
        nodes=[],
        edges=[],
        truncated=False,
        total_nodes=0,
        total_edges=0,
    )


@router.get("/cases/{case_id}/graph/neighborhood/{node_id:path}", response_model=GraphResponse)
def get_node_neighborhood(
    case_id: str,
    node_id: str,
    hops: int = Query(1, ge=1, le=3),
    limit: int = Query(200, ge=10, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve multi-hop neighborhood for a specific node."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' was not found",
        )

    graph_file = Path(settings.DATA_DIR) / "cases" / case_id / "graph" / "graph.json"
    if graph_file.exists():
        try:
            with open(graph_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                raw_nodes = data.get("elements", {}).get("nodes", []) if "elements" in data else data.get("nodes", [])
                raw_edges = data.get("elements", {}).get("edges", []) if "elements" in data else data.get("edges", [])
                all_nodes = {n.get("data", n)["id"]: n.get("data", n) for n in raw_nodes if "id" in n.get("data", n)}
                all_edges = [e.get("data", e) for e in raw_edges]

                # Match target node
                target_key = node_id
                if target_key not in all_nodes:
                    for k in all_nodes:
                        if k.endswith(f":{node_id}") or all_nodes[k].get("label") == node_id:
                            target_key = k
                            break

                current_hop_nodes = {target_key} if target_key in all_nodes else set()
                visited_nodes = set(current_hop_nodes)
                collected_edges = []

                for _ in range(hops):
                    next_hop_nodes = set()
                    for edge in all_edges:
                        s = edge.get("source")
                        t = edge.get("target")
                        if s in current_hop_nodes or t in current_hop_nodes:
                            collected_edges.append(edge)
                            if s and s not in visited_nodes:
                                next_hop_nodes.add(s)
                            if t and t not in visited_nodes:
                                next_hop_nodes.add(t)
                    visited_nodes.update(next_hop_nodes)
                    current_hop_nodes = next_hop_nodes

                sub_nodes = [all_nodes[nid] for nid in visited_nodes if nid in all_nodes][:limit]
                sub_node_ids = {n["id"] for n in sub_nodes}
                sub_edges = [e for e in collected_edges if e.get("source") in sub_node_ids and e.get("target") in sub_node_ids][:limit * 2]

                def make_attrs(n_dict):
                    if "attributes" in n_dict and n_dict["attributes"]:
                        return n_dict["attributes"]
                    return {k: v for k, v in n_dict.items() if k not in ("id", "type", "label")}

                return GraphResponse(
                    nodes=[GraphNode(id=n["id"], type=n.get("type", "unknown"), label=n.get("label", n["id"]), attributes=make_attrs(n)) for n in sub_nodes],
                    edges=[GraphEdge(id=e.get("id", f"{e['source']}->{e['target']}"), source=e["source"], target=e["target"], type=e.get("type", "unknown"), basis=e.get("basis", ""), source_record_ids=e.get("source_record_ids", []), weight=float(e.get("weight", 1.0) or 1.0), first_seen=e.get("first_seen"), last_seen=e.get("last_seen")) for e in sub_edges],
                    truncated=len(visited_nodes) > limit,
                    total_nodes=len(visited_nodes),
                    total_edges=len(collected_edges),
                )
        except Exception:
            pass

    return GraphResponse(
        nodes=[GraphNode(id=node_id, type="wallet", label=node_id, attributes={})],
        edges=[],
        truncated=False,
        total_nodes=1,
        total_edges=0,
    )
