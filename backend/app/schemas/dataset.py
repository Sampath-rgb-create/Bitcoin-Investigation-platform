from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class CanonicalTransactionRecord(BaseModel):
    """
    Canonical Bitcoin transaction record (Section 5.4.1).
    All rows ingested as or extracted as transactions conform to this schema.
    """
    record_id: str
    timestamp: datetime
    txid: str
    input_addresses: List[str] = Field(default_factory=list)
    output_addresses: List[str] = Field(default_factory=list)
    input_amounts: List[float] = Field(default_factory=list)
    output_amounts: List[float] = Field(default_factory=list)
    fee: Optional[float] = 0.0
    script_type: Optional[str] = None

    @field_validator("input_amounts", "output_amounts")
    @classmethod
    def check_non_negative_amounts(cls, amounts: List[float]) -> List[float]:
        for a in amounts:
            if a < 0:
                raise ValueError("Amounts must be non-negative")
        return amounts


class CanonicalNetworkRecord(BaseModel):
    """
    Canonical network observation record (Section 5.4.2).
    """
    record_id: str
    timestamp: datetime
    src_ip: str
    dst_ip: str
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    txid: Optional[str] = None
    geo_country: Optional[str] = None
    asn: Optional[str] = None


class CombinedSIHRecord(BaseModel):
    """
    Combined SIH record (Section 5.4.3), combining transaction and network fields.
    """
    record_id: str
    timestamp: datetime
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    txid: str
    input_addresses: List[str] = Field(default_factory=list)
    output_addresses: List[str] = Field(default_factory=list)
    input_amounts: List[float] = Field(default_factory=list)
    output_amounts: List[float] = Field(default_factory=list)
    fee: Optional[float] = 0.0
    script_type: Optional[str] = None
    geo_country: Optional[str] = None
    asn: Optional[str] = None


class DatasetOut(BaseModel):
    dataset_id: str
    case_id: str
    name: str
    kind: str
    format: str
    sha256: str
    row_count: int
    accepted_rows: int
    rejected_rows: int
    warning_count: int
    status: str = "validated"
    created_at: str

    model_config = {"from_attributes": True}


class ValidationReportRow(BaseModel):
    row_number: int
    record_id: Optional[str] = None
    issue_type: str  # 'error' or 'warning'
    code: str
    message: str


class ValidationReport(BaseModel):
    dataset_id: str
    total_rows: int
    accepted_rows: int
    rejected_rows: int
    warning_count: int
    issues: List[ValidationReportRow] = Field(default_factory=list)
