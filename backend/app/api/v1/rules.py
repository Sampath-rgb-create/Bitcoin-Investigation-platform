from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models import CustomRule, Case, User
from backend.app.schemas.rule import CustomRuleCreate, CustomRuleUpdate, CustomRuleOut
from backend.app.api.deps import get_current_user

router = APIRouter()


@router.get("/cases/{case_id}/rules", response_model=List[CustomRuleOut])
def list_case_rules(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all custom rules defined for a case (and global rules where case_id is null).
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' was not found",
        )

    rules = (
        db.query(CustomRule)
        .filter((CustomRule.case_id == case_id) | (CustomRule.case_id.is_(None)))
        .order_by(CustomRule.created_at.desc())
        .all()
    )
    return rules


@router.post("/cases/{case_id}/rules", response_model=CustomRuleOut, status_code=status.HTTP_201_CREATED)
def create_case_rule(
    case_id: str,
    rule_in: CustomRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new dynamic investigator rule for this case.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' was not found",
        )

    rule = CustomRule(
        case_id=case_id,
        name=rule_in.name,
        description=rule_in.description,
        target_entity=rule_in.target_entity,
        field=rule_in.field,
        operator=rule_in.operator,
        threshold=rule_in.threshold,
        severity=rule_in.severity,
        weight=rule_in.weight,
        enabled=rule_in.enabled,
        created_by=current_user.id if current_user else None,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/cases/{case_id}/rules/{rule_id}", response_model=CustomRuleOut)
def update_case_rule(
    case_id: str,
    rule_id: str,
    rule_update: CustomRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing custom rule.
    """
    rule = db.query(CustomRule).filter(CustomRule.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule '{rule_id}' was not found",
        )

    update_data = rule_update.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(rule, field, val)

    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/cases/{case_id}/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case_rule(
    case_id: str,
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a custom rule.
    """
    rule = db.query(CustomRule).filter(CustomRule.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule '{rule_id}' was not found",
        )

    db.delete(rule)
    db.commit()
    return None
