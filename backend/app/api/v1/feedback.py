from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models import Alert, Feedback, User
from backend.app.schemas.feedback import FeedbackCreate, FeedbackOut
from backend.app.api.deps import (
    get_current_user,
    get_current_analyst_or_admin,
)

router = APIRouter()


@router.post("/alerts/{alert_id}/feedback", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    alert_id: str,
    feedback_in: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_analyst_or_admin),
):
    """Submit investigator feedback annotation on an alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' was not found",
        )

    feedback = Feedback(
        alert_id=alert_id,
        user_id=current_user.id,
        label=feedback_in.label,
        note=feedback_in.note,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return feedback


@router.get("/alerts/{alert_id}/feedback", response_model=List[FeedbackOut])
def get_alert_feedback(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all investigator feedback annotations for an alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' was not found",
        )
    return db.query(Feedback).filter(Feedback.alert_id == alert_id).all()
