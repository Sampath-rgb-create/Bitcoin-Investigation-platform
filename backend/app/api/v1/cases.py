from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models import Case, User
from backend.app.schemas.case import CaseCreate, CaseUpdate, CaseOut
from backend.app.api.deps import (
    get_current_user,
    get_current_analyst_or_admin,
    get_case_for_user,
)

router = APIRouter()


@router.post("", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
def create_case(
    case_in: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_analyst_or_admin),
):
    """Create a new investigative case."""
    case = Case(
        name=case_in.name,
        description=case_in.description,
        status="open",
        created_by=current_user.id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return {
        "case_id": case.id,
        "name": case.name,
        "description": case.description,
        "status": case.status,
        "created_by": case.created_by,
        "created_at": case.created_at,
        "updated_at": case.updated_at,
    }


@router.get("", response_model=List[CaseOut])
def list_cases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all cases accessible by the authenticated user."""
    cases = db.query(Case).order_by(Case.created_at.desc()).all()
    return [
        {
            "case_id": c.id,
            "name": c.name,
            "description": c.description,
            "status": c.status,
            "created_by": c.created_by,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }
        for c in cases
    ]


@router.get("/{case_id}", response_model=CaseOut)
def get_case(
    case: Case = Depends(get_case_for_user),
):
    """Get metadata for a specific case."""
    return {
        "case_id": case.id,
        "name": case.name,
        "description": case.description,
        "status": case.status,
        "created_by": case.created_by,
        "created_at": case.created_at,
        "updated_at": case.updated_at,
    }


@router.patch("/{case_id}", response_model=CaseOut)
def update_case(
    case_in: CaseUpdate,
    case: Case = Depends(get_case_for_user),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_analyst_or_admin),
):
    """Update case metadata or status."""
    if case_in.name is not None:
        case.name = case_in.name
    if case_in.description is not None:
        case.description = case_in.description
    if case_in.status is not None:
        if case_in.status not in ("open", "archived"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Case status must be 'open' or 'archived'",
            )
        case.status = case_in.status
    db.commit()
    db.refresh(case)
    return {
        "case_id": case.id,
        "name": case.name,
        "description": case.description,
        "status": case.status,
        "created_by": case.created_by,
        "created_at": case.created_at,
        "updated_at": case.updated_at,
    }


@router.post("/{case_id}/archive", response_model=CaseOut)
def archive_case(
    case: Case = Depends(get_case_for_user),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_analyst_or_admin),
):
    """Archive an existing case."""
    case.status = "archived"
    db.commit()
    db.refresh(case)
    return {
        "case_id": case.id,
        "name": case.name,
        "description": case.description,
        "status": case.status,
        "created_by": case.created_by,
        "created_at": case.created_at,
        "updated_at": case.updated_at,
    }
