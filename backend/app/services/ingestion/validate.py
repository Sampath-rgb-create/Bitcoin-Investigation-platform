"""
Validation service for raw, mapped, and parsed records.
Enforces:
- Array parity check: len(input_addresses) == len(input_amounts)
                      len(output_addresses) == len(output_amounts)
- Valid IPv4 and IPv6 format
- Port range 0-65535
- Timestamp validity
- Non-negative amounts
- Monetary consistency: abs(total_input - (total_output + fee)) > MONEY_EPSILON produces a warning
"""
import ipaddress
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from backend.app.schemas.dataset import ValidationReportRow
from backend.app.core.config import settings


def is_valid_ip(ip_str: Optional[str]) -> bool:
    """Checks whether the given string is a valid IPv4 or IPv6 address."""
    if not ip_str or not isinstance(ip_str, str):
        return False
    try:
        ipaddress.ip_address(ip_str.strip())
        return True
    except ValueError:
        return False


def is_valid_port(port: Optional[Any]) -> bool:
    """Checks whether port is an integer in range [0, 65535]."""
    if port is None or port == "" or (isinstance(port, str) and port.lower() in ("null", "none")):
        return True
    try:
        p = int(port)
        return 0 <= p <= 65535
    except (ValueError, TypeError):
        return False


def validate_record(
    record: Dict[str, Any],
    row_number: int,
    kind: str = "auto",
    epsilon: float = settings.MONEY_EPSILON
) -> Tuple[bool, List[ValidationReportRow]]:
    """
    Validates a canonicalized dictionary record against SIH specifications.
    
    Returns:
        (is_valid: bool, issues: List[ValidationReportRow])
        If any issue has issue_type == 'error', is_valid will be False.
    """
    issues: List[ValidationReportRow] = []
    record_id = str(record.get("record_id", f"row-{row_number}"))
    is_valid = True

    def add_error(code: str, msg: str):
        nonlocal is_valid
        is_valid = False
        issues.append(
            ValidationReportRow(
                row_number=row_number,
                record_id=record_id,
                issue_type="error",
                code=code,
                message=msg
            )
        )

    def add_warning(code: str, msg: str):
        issues.append(
            ValidationReportRow(
                row_number=row_number,
                record_id=record_id,
                issue_type="warning",
                code=code,
                message=msg
            )
        )

    # 1. Timestamp validation
    ts = record.get("timestamp")
    if ts is None or ts == "":
        add_error("MISSING_TIMESTAMP", "Timestamp is required.")
    elif not isinstance(ts, datetime):
        # Check string parseability
        try:
            if isinstance(ts, (int, float)):
                # epoch timestamp
                _ = datetime.fromtimestamp(ts)
            else:
                _ = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except Exception:
            add_error("INVALID_TIMESTAMP", f"Unable to parse timestamp: {ts}")

    # Determine role: transaction, network, or combined
    has_tx_fields = any(k in record and record[k] is not None for k in ("input_addresses", "output_addresses", "input_amounts", "output_amounts", "fee"))
    has_net_fields = any(k in record and record[k] is not None for k in ("src_ip", "dst_ip", "src_port", "dst_port"))
    
    # 2. Transaction fields & Parity
    if kind in ("transaction", "combined") or (kind == "auto" and has_tx_fields):
        # txid is required for transaction rows
        txid = record.get("txid")
        if not txid or not str(txid).strip():
            add_error("MISSING_TXID", "Transaction rows must contain a non-empty txid.")

        # Address & amount parity checks
        in_addrs = record.get("input_addresses") or []
        in_amts = record.get("input_amounts") or []
        out_addrs = record.get("output_addresses") or []
        out_amts = record.get("output_amounts") or []

        if in_addrs and in_amts:
            if len(in_addrs) != len(in_amts):
                add_error(
                    "ARRAY_PARITY_INPUT_MISMATCH",
                    f"input_addresses length ({len(in_addrs)}) does not match input_amounts length ({len(in_amts)})"
                )

        if out_addrs and out_amts:
            if len(out_addrs) != len(out_amts):
                add_error(
                    "ARRAY_PARITY_OUTPUT_MISMATCH",
                    f"output_addresses length ({len(out_addrs)}) does not match output_amounts length ({len(out_amts)})"
                )

        # Check negative amounts
        for idx, amt in enumerate(in_amts):
            try:
                if float(amt) < 0:
                    add_error("NEGATIVE_INPUT_AMOUNT", f"Input amount at index {idx} is negative: {amt}")
            except (ValueError, TypeError):
                add_error("INVALID_INPUT_AMOUNT", f"Input amount at index {idx} is not numeric: {amt}")

        for idx, amt in enumerate(out_amts):
            try:
                if float(amt) < 0:
                    add_error("NEGATIVE_OUTPUT_AMOUNT", f"Output amount at index {idx} is negative: {amt}")
            except (ValueError, TypeError):
                add_error("INVALID_OUTPUT_AMOUNT", f"Output amount at index {idx} is not numeric: {amt}")

        fee = record.get("fee")
        if fee is not None:
            try:
                fee_val = float(fee)
                if fee_val < 0:
                    add_error("NEGATIVE_FEE", f"Fee cannot be negative: {fee}")
            except (ValueError, TypeError):
                add_error("INVALID_FEE", f"Fee must be numeric: {fee}")

        # Monetary consistency check (warning only)
        if in_amts and out_amts:
            try:
                total_in = sum(float(a) for a in in_amts)
                total_out = sum(float(a) for a in out_amts)
                fee_val = float(fee) if fee is not None else 0.0
                expected_in = total_out + fee_val
                delta = abs(total_in - expected_in)
                if delta > epsilon:
                    add_warning(
                        "MONETARY_DISCREPANCY",
                        f"Discrepancy detected: total_in ({total_in}) != total_out + fee ({expected_in}), delta = {delta:.8f}"
                    )
            except Exception:
                pass

    # 3. Network fields check
    if kind in ("network", "combined") or (kind == "auto" and has_net_fields):
        src_ip = record.get("src_ip")
        dst_ip = record.get("dst_ip")
        
        # Only validate if provided (in combined rows they might be optional, in network rows required)
        if kind == "network":
            if not src_ip or not is_valid_ip(src_ip):
                add_error("INVALID_SRC_IP", f"Invalid or missing src_ip: {src_ip}")
            if not dst_ip or not is_valid_ip(dst_ip):
                add_error("INVALID_DST_IP", f"Invalid or missing dst_ip: {dst_ip}")
        else:
            if src_ip and not is_valid_ip(src_ip):
                add_error("INVALID_SRC_IP", f"Invalid src_ip format: {src_ip}")
            if dst_ip and not is_valid_ip(dst_ip):
                add_error("INVALID_DST_IP", f"Invalid dst_ip format: {dst_ip}")

        src_port = record.get("src_port")
        if src_port is not None and not is_valid_port(src_port):
            add_error("INVALID_SRC_PORT", f"src_port out of range [0-65535]: {src_port}")

        dst_port = record.get("dst_port")
        if dst_port is not None and not is_valid_port(dst_port):
            add_error("INVALID_DST_PORT", f"dst_port out of range [0-65535]: {dst_port}")

    return is_valid, issues
