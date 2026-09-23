from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Text,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from backend.app.db.base import Base


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'admin', 'analyst', 'viewer'
    active = Column(Integer, nullable=False, default=1)
    created_at = Column(String, nullable=False, default=utc_now_iso)

    __table_args__ = (
        CheckConstraint("role IN ('admin','analyst','viewer')", name="check_user_role"),
    )

    cases = relationship("Case", back_populates="creator")
    feedbacks = relationship("Feedback", back_populates="user")


class Case(Base):
    __tablename__ = "cases"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="open")  # 'open', 'archived'
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(String, nullable=False, default=utc_now_iso)
    updated_at = Column(String, nullable=False, default=utc_now_iso, onupdate=utc_now_iso)

    __table_args__ = (
        CheckConstraint("status IN ('open','archived')", name="check_case_status"),
    )

    creator = relationship("User", back_populates="cases")
    datasets = relationship("Dataset", back_populates="case", cascade="all, delete-orphan")
    runs = relationship("AnalysisRun", back_populates="case", cascade="all, delete-orphan")


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String, primary_key=True, default=generate_uuid)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    kind = Column(String, nullable=False)  # 'transaction', 'network', 'combined', 'unknown'
    format = Column(String, nullable=False)  # 'csv', 'json', 'xml'
    source_path = Column(String, nullable=False)
    sha256 = Column(String, nullable=False)
    row_count = Column(Integer, nullable=False, default=0)
    accepted_rows = Column(Integer, nullable=False, default=0)
    rejected_rows = Column(Integer, nullable=False, default=0)
    warning_count = Column(Integer, nullable=False, default=0)
    validation_report_path = Column(String, nullable=True)
    created_at = Column(String, nullable=False, default=utc_now_iso)

    __table_args__ = (
        CheckConstraint("kind IN ('transaction','network','combined','unknown')", name="check_dataset_kind"),
    )

    case = relationship("Case", back_populates="datasets")


class AnalysisRun(Base):
    __tablename__ = "runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False, index=True)
    status = Column(String, nullable=False, default="queued")  # queued, running, completed, failed, cancelled
    stage = Column(String, nullable=False, default="queued")
    progress = Column(Integer, nullable=False, default=0)
    config_json = Column(Text, nullable=False, default="{}")
    error_code = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(String, nullable=True)
    completed_at = Column(String, nullable=True)
    created_at = Column(String, nullable=False, default=utc_now_iso)

    case = relationship("Case", back_populates="runs")
    alerts = relationship("Alert", back_populates="run", cascade="all, delete-orphan")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=generate_uuid)
    run_id = Column(String, ForeignKey("runs.id"), nullable=False, index=True)
    entity_id = Column(String, nullable=False, index=True)  # e.g., 'wallet:W123'
    severity = Column(String, nullable=False)  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    priority_score = Column(Float, nullable=False)
    anomaly_score = Column(Float, nullable=False)
    behavior_score = Column(Float, nullable=False)
    graph_score = Column(Float, nullable=False)
    network_score = Column(Float, nullable=False)
    correlation_strength = Column(Float, nullable=False, default=0.0)
    evidence_coverage = Column(Float, nullable=False, default=0.0)
    reasons_json = Column(Text, nullable=False, default="[]")
    laya_json = Column(Text, nullable=True)
    explanation_json = Column(Text, nullable=True)
    created_at = Column(String, nullable=False, default=utc_now_iso)

    run = relationship("AnalysisRun", back_populates="alerts")
    feedbacks = relationship("Feedback", back_populates="alert", cascade="all, delete-orphan")


class Feedback(Base):
    __tablename__ = "alert_feedback"

    id = Column(String, primary_key=True, default=generate_uuid)
    alert_id = Column(String, ForeignKey("alerts.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    label = Column(String, nullable=False)  # 'relevant', 'benign', 'needs_review'
    note = Column(Text, nullable=True)
    created_at = Column(String, nullable=False, default=utc_now_iso)

    __table_args__ = (
        CheckConstraint("label IN ('relevant','benign','needs_review')", name="check_feedback_label"),
    )

    alert = relationship("Alert", back_populates="feedbacks")
    user = relationship("User", back_populates="feedbacks")
