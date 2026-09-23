import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models import Alert, AnalysisRun, Case, User
from backend.app.schemas.alert import AlertOut, AlertListResponse, ScoreComponents
from backend.app.schemas.evidence import AlertEvidencePack, DeterministicReason, EvidenceItem
from backend.app.api.deps import (
    get_current_user,
    get_case_for_user,
)

router = APIRouter()


@router.get("/cases/{case_id}/alerts", response_model=AlertListResponse)
def list_case_alerts(
    case_id: str,
    run_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    min_priority_score: Optional[float] = Query(None),
    entity_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Query paginated, prioritized alerts for a case."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' was not found",
        )

    query = (
        db.query(Alert)
        .join(AnalysisRun, Alert.run_id == AnalysisRun.id)
        .filter(AnalysisRun.case_id == case_id)
    )

    if run_id:
        query = query.filter(Alert.run_id == run_id)
    if severity:
        query = query.filter(Alert.severity == severity.upper())
    if min_priority_score is not None:
        query = query.filter(Alert.priority_score >= min_priority_score)
    if entity_type:
        query = query.filter(Alert.entity_id.startswith(f"{entity_type}:"))

    total = query.count()
    alerts = (
        query.order_by(Alert.priority_score.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for a in alerts:
        reasons = []
        if a.reasons_json:
            try:
                reasons = json.loads(a.reasons_json)
            except Exception:
                reasons = [a.reasons_json]
        if not reasons and a.explanation_json:
            try:
                exp = json.loads(a.explanation_json)
                reasons = [r.get("text", "") for r in exp.get("top_reasons", []) if isinstance(r, dict) and r.get("text")]
            except Exception:
                pass

        items.append(
            AlertOut(
                alert_id=a.id,
                run_id=a.run_id,
                entity_id=a.entity_id,
                severity=a.severity,
                priority_score=a.priority_score,
                score_components=ScoreComponents(
                    anomaly_score=a.anomaly_score or 0.0,
                    behavior_score=a.behavior_score or 0.0,
                    graph_score=a.graph_score or 0.0,
                    network_score=a.network_score or 0.0,
                ),
                correlation_strength=a.correlation_strength or 0.0,
                evidence_coverage=a.evidence_coverage or 0.0,
                top_reasons=reasons,
                reasons=reasons,
                laya=json.loads(a.laya_json) if a.laya_json else None,
                ollama_summary=a.explanation_json,
                created_at=a.created_at,
            )
        )

    return AlertListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/alerts/{alert_id}", response_model=AlertOut)
def get_alert_detail(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full details for an individual alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' was not found",
        )

    reasons = []
    if alert.reasons_json:
        try:
            reasons = json.loads(alert.reasons_json)
        except Exception:
            reasons = [alert.reasons_json]
    if not reasons and alert.explanation_json:
        try:
            exp = json.loads(alert.explanation_json)
            reasons = [r.get("text", "") for r in exp.get("top_reasons", []) if isinstance(r, dict) and r.get("text")]
        except Exception:
            pass

    return AlertOut(
        alert_id=alert.id,
        run_id=alert.run_id,
        entity_id=alert.entity_id,
        severity=alert.severity,
        priority_score=alert.priority_score,
        score_components=ScoreComponents(
            anomaly_score=alert.anomaly_score or 0.0,
            behavior_score=alert.behavior_score or 0.0,
            graph_score=alert.graph_score or 0.0,
            network_score=alert.network_score or 0.0,
        ),
        correlation_strength=alert.correlation_strength or 0.0,
        evidence_coverage=alert.evidence_coverage or 0.0,
        top_reasons=reasons,
        reasons=reasons,
        laya=json.loads(alert.laya_json) if alert.laya_json else None,
        ollama_summary=alert.explanation_json,
        created_at=alert.created_at,
    )


@router.get("/alerts/{alert_id}/evidence", response_model=AlertEvidencePack)
@router.get("/cases/{case_id}/alerts/{alert_id}/evidence", response_model=AlertEvidencePack)
def get_alert_evidence(
    alert_id: str,
    case_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the complete evidence provenance chain for an alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' was not found",
        )

    # 1. Real score components
    score_components = {
        "anomaly_score": round(float(alert.anomaly_score or 0.0), 4),
        "behavior_score": round(float(alert.behavior_score or 0.0), 4),
        "graph_score": round(float(alert.graph_score or 0.0), 4),
        "network_score": round(float(alert.network_score or 0.0), 4),
    }

    # 2. Extract structured deterministic reasons
    reasons = []
    if alert.explanation_json:
        try:
            exp = json.loads(alert.explanation_json)
            top_r = exp.get("top_reasons", []) or exp.get("reasons", [])
            for i, r in enumerate(top_r):
                if isinstance(r, dict):
                    feat = r.get("feature", "")
                    headline = feat.replace("RULE_", "") if feat.startswith("RULE_") else feat.replace("_", " ").title()
                    reasons.append({
                        "reason_id": r.get("reason_id", f"r-{i}"),
                        "rule_code": feat or "RULE",
                        "headline": headline or "Forensic Finding",
                        "explanation": r.get("text", ""),
                        "observed_value": r.get("value"),
                        "threshold": r.get("threshold_or_baseline"),
                        "unit": r.get("unit", ""),
                        "type": r.get("type", "rule"),
                        "text": r.get("text", ""),
                    })
        except Exception:
            pass

    if not reasons and alert.reasons_json:
        try:
            raw_reasons = json.loads(alert.reasons_json)
            for i, r in enumerate(raw_reasons):
                if isinstance(r, dict):
                    reasons.append(r)
                else:
                    reasons.append({
                        "reason_id": f"r-{i}",
                        "rule_code": "FINDING",
                        "headline": "Forensic Signal",
                        "explanation": str(r),
                        "observed_value": None,
                        "threshold": None,
                        "unit": "",
                        "type": "rule",
                        "text": str(r),
                    })
        except Exception:
            pass

    # 3. Extract source record IDs and evidence items from case report JSON or Parquet
    source_records = []
    evidence_items = []
    from backend.app.core.config import settings
    from pathlib import Path
    import os

    case_key = case_id
    if not case_key:
        if alert.run:
            case_key = alert.run.case_id
        elif alert.run_id:
            run_obj = db.query(AnalysisRun).filter(AnalysisRun.id == alert.run_id).first()
            if run_obj:
                case_key = run_obj.case_id

    if case_key:
        report_file = Path(settings.DATA_DIR) / "cases" / case_key / "reports" / f"run_{alert.run_id}.json"
        if report_file.exists():
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    rep_data = json.load(f)
                for rep_alert in rep_data.get("alerts", []):
                    if rep_alert.get("entity_id") == alert.entity_id:
                        pack = rep_alert.get("evidence_pack", [])
                        for ev in pack:
                            if isinstance(ev, dict):
                                try:
                                    evidence_items.append(EvidenceItem(**ev))
                                except Exception:
                                    pass
                                if ev.get("source_record_ids"):
                                    for s_id in ev["source_record_ids"]:
                                        if s_id not in source_records:
                                            source_records.append(s_id)
                        break
            except Exception:
                pass

        # Fallback to transactions.parquet
        if not source_records:
            from backend.app.storage.parquet_store import parquet_store
            clean_addr = alert.entity_id.replace("wallet:", "")
            tx_file = os.path.join(settings.DATA_DIR, "cases", case_key, "normalized", "transactions.parquet")
            if os.path.exists(tx_file):
                try:
                    df_tx = parquet_store.read_dataframe(tx_file)
                    for _, row in df_tx.iterrows():
                        in_addrs = list(row["input_addresses"]) if hasattr(row.get("input_addresses"), "__iter__") else []
                        out_addrs = list(row["output_addresses"]) if hasattr(row.get("output_addresses"), "__iter__") else []
                        if clean_addr in in_addrs or clean_addr in out_addrs:
                            rec_id = row.get("record_id")
                            if rec_id and rec_id not in source_records:
                                source_records.append(rec_id)
                            if len(source_records) >= 60:
                                break
                except Exception:
                    pass

    return AlertEvidencePack(
        alert_id=alert.id,
        entity_id=alert.entity_id,
        severity=alert.severity,
        priority_score=alert.priority_score,
        score_components=score_components,
        source_records=source_records,
        reasons=reasons,
        evidence_items=evidence_items,
    )
