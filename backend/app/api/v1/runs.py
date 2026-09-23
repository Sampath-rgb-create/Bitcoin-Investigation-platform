import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models import AnalysisRun, Case, User
from backend.app.schemas.run import RunCreateRequest, RunOut
from backend.app.api.deps import (
    get_current_user,
    get_current_analyst_or_admin,
    get_case_for_user,
)

router = APIRouter()


@router.post("/cases/{case_id}/runs", response_model=RunOut, status_code=status.HTTP_201_CREATED)
def start_analysis_run(
    case_id: str,
    run_req: RunCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_analyst_or_admin),
):
    """
    Queue an analysis run for a case.
    The analysis executes detectors, graph builder, and score fusion.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' was not found",
        )

    # Check for active run
    from backend.app.services.job_manager import job_manager

    active_run = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.case_id == case_id, AnalysisRun.status.in_(["queued", "running"]))
        .first()
    )
    if active_run:
        if job_manager.is_running(active_run.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An analysis run is actively executing for this case.",
            )
        else:
            # Stale DB record from server reload/crash: automatically clean it up
            active_run.status = "interrupted"
            active_run.stage = "interrupted"
            db.commit()

    run = AnalysisRun(
        case_id=case_id,
        status="queued",
        stage="queued",
        progress=0,
        config_json=json.dumps(run_req.model_dump()),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    from backend.app.services.job_manager import job_manager
    job_manager.submit_job(case_id=case_id, run_id=run.id, config=run_req.model_dump())

    return {
        "run_id": run.id,
        "case_id": run.case_id,
        "status": run.status,
        "stage": run.stage,
        "progress": run.progress,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "created_at": run.created_at,
        "error_code": run.error_code,
        "error_message": run.error_message,
    }


@router.get("/runs/{run_id}", response_model=RunOut)
@router.get("/cases/{case_id}/runs/{run_id}", response_model=RunOut)
def get_run_status(
    run_id: str,
    case_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve run status, stage, and completion progress."""
    run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' was not found",
        )
    return {
        "run_id": run.id,
        "case_id": run.case_id,
        "status": run.status,
        "stage": run.stage,
        "progress": run.progress,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "created_at": run.created_at,
        "error_code": run.error_code,
        "error_message": run.error_message,
    }


@router.post("/runs/{run_id}/cancel", response_model=RunOut)
def cancel_run(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_analyst_or_admin),
):
    """Cancel an active or queued run."""
    run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' was not found",
        )
    if run.status in ("completed", "failed", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel run in status '{run.status}'",
        )
    run.status = "cancelled"
    run.stage = "cancelled"
    db.commit()
    db.refresh(run)

    return {
        "run_id": run.id,
        "case_id": run.case_id,
        "status": run.status,
        "stage": run.stage,
        "progress": run.progress,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "created_at": run.created_at,
        "error_code": run.error_code,
        "error_message": run.error_message,
    }
