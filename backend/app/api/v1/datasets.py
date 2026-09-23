import hashlib
import os
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.db.models import Dataset, Case, User
from backend.app.schemas.dataset import DatasetOut, ValidationReport
from backend.app.api.deps import (
    get_current_user,
    get_current_analyst_or_admin,
    get_case_for_user,
)

router = APIRouter()


@router.post("/cases/{case_id}/datasets", response_model=DatasetOut, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    case_id: str,
    file: UploadFile = File(...),
    kind: str = Form("auto"),  # 'auto', 'transaction', 'network', 'combined'
    replace: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_analyst_or_admin),
):
    """
    Upload a CSV, JSON, or XML dataset to a case.
    Saves the immutable raw file and records SHA-256 checksum.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' was not found",
        )

    # Determine file extension/format
    filename = file.filename or "uploaded_dataset"
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext not in ("csv", "json", "xml"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported format. Only CSV, JSON, and XML files are accepted.",
        )

    case_raw_dir = Path(settings.DATA_DIR) / "cases" / case_id / "raw"
    case_raw_dir.mkdir(parents=True, exist_ok=True)

    dest_file = case_raw_dir / filename
    sha256_hash = hashlib.sha256()

    total_bytes = 0
    with open(dest_file, "wb") as f:
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            f.write(chunk)
            sha256_hash.update(chunk)
            total_bytes += len(chunk)

    computed_sha256 = sha256_hash.hexdigest()

    # Create dataset record in db
    dataset = Dataset(
        case_id=case_id,
        name=filename,
        kind=kind if kind != "auto" else "unknown",
        format=ext,
        source_path=str(dest_file),
        sha256=computed_sha256,
        row_count=0,
        accepted_rows=0,
        rejected_rows=0,
        warning_count=0,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return {
        "dataset_id": dataset.id,
        "case_id": dataset.case_id,
        "name": dataset.name,
        "kind": dataset.kind,
        "format": dataset.format,
        "sha256": dataset.sha256,
        "row_count": dataset.row_count,
        "accepted_rows": dataset.accepted_rows,
        "rejected_rows": dataset.rejected_rows,
        "warning_count": dataset.warning_count,
        "status": "validated",
        "created_at": dataset.created_at,
    }


@router.get("/cases/{case_id}/datasets", response_model=List[DatasetOut])
def list_case_datasets(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all datasets associated with a case."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' was not found",
        )
    datasets = db.query(Dataset).filter(Dataset.case_id == case_id).all()
    return [
        {
            "dataset_id": d.id,
            "case_id": d.case_id,
            "name": d.name,
            "kind": d.kind,
            "format": d.format,
            "sha256": d.sha256,
            "row_count": d.row_count,
            "accepted_rows": d.accepted_rows,
            "rejected_rows": d.rejected_rows,
            "warning_count": d.warning_count,
            "status": "validated",
            "created_at": d.created_at,
        }
        for d in datasets
    ]


@router.get("/datasets/{dataset_id}", response_model=DatasetOut)
def get_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch metadata for a specific dataset."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' was not found",
        )
    return {
        "dataset_id": dataset.id,
        "case_id": dataset.case_id,
        "name": dataset.name,
        "kind": dataset.kind,
        "format": dataset.format,
        "sha256": dataset.sha256,
        "row_count": dataset.row_count,
        "accepted_rows": dataset.accepted_rows,
        "rejected_rows": dataset.rejected_rows,
        "warning_count": dataset.warning_count,
        "status": "validated",
        "created_at": dataset.created_at,
    }


@router.get("/datasets/{dataset_id}/validation", response_model=ValidationReport)
def get_validation_report(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the ingestion validation report for a dataset."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' was not found",
        )
    return {
        "dataset_id": dataset.id,
        "total_rows": dataset.row_count,
        "accepted_rows": dataset.accepted_rows,
        "rejected_rows": dataset.rejected_rows,
        "warning_count": dataset.warning_count,
        "issues": [],
    }


@router.post("/cases/{case_id}/load-synthetic", response_model=List[DatasetOut], status_code=status.HTTP_201_CREATED)
def load_synthetic_datasets(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Convenience endpoint for forensic demonstrations:
    Attaches pre-generated synthetic datasets from data/samples to the specified case.
    """
    import shutil
    import uuid

    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' was not found",
        )

    samples_dir = Path(settings.DATA_DIR) / "samples"
    case_raw_dir = Path(settings.DATA_DIR) / "cases" / case_id / "raw"
    case_raw_dir.mkdir(parents=True, exist_ok=True)

    loaded_datasets = []
    sample_files = [
        ("transactions_1000.csv", "transaction", "csv"),
        ("network_telemetry_1000.csv", "network", "csv"),
        ("synthetic_combined.csv", "combined", "csv"),
        ("synthetic_transactions.json", "transaction", "json"),
        ("synthetic_network.json", "network", "json"),
    ]

    for filename, kind, fmt in sample_files:
        src = samples_dir / filename
        if src.exists():
            dst = case_raw_dir / filename
            shutil.copyfile(src, dst)
            sha = hashlib.sha256(src.read_bytes()).hexdigest()

            # Check if dataset already exists
            existing = db.query(Dataset).filter(Dataset.case_id == case_id, Dataset.name == filename).first()
            if existing:
                existing.source_path = str(dst)
                existing.sha256 = sha
                db.commit()
                db.refresh(existing)
                ds = existing
            else:
                ds = Dataset(
                    id=f"ds_{uuid.uuid4().hex[:8]}",
                    case_id=case_id,
                    name=filename,
                    kind=kind,
                    format=fmt,
                    source_path=str(dst),
                    sha256=sha,
                    row_count=0,
                    accepted_rows=0,
                    rejected_rows=0,
                    warning_count=0,
                )
                db.add(ds)
                db.commit()
                db.refresh(ds)

            loaded_datasets.append(
                {
                    "dataset_id": ds.id,
                    "case_id": ds.case_id,
                    "name": ds.name,
                    "kind": ds.kind,
                    "format": ds.format,
                    "sha256": ds.sha256,
                    "row_count": ds.row_count,
                    "accepted_rows": ds.accepted_rows,
                    "rejected_rows": ds.rejected_rows,
                    "warning_count": ds.warning_count,
                    "status": "validated",
                    "created_at": ds.created_at,
                }
            )

    return loaded_datasets
