"""
Unit tests for ingestion adapters, field mapping, validation, and normalization.
"""
import pytest
from datetime import datetime, timezone
from backend.app.services.ingestion.field_mapping import map_raw_keys, parse_list_field, ALIAS_LOOKUP
from backend.app.services.ingestion.validate import validate_record, is_valid_ip, is_valid_port
from backend.app.services.ingestion.normalize import normalize_record, normalize_timestamp, normalize_ip, compute_sha256_string


def test_field_mapping_aliases():
    raw = {
        "transaction_id": "tx123",
        "inputs": "['W1', 'W2']",
        "vout_amounts": "1.0, 2.5",
        "ts": "2026-01-01T10:00:00Z",
        "source_ip": "192.168.1.1",
        "dest_port": "8333"
    }
    mapped = map_raw_keys(raw)
    assert mapped["txid"] == "tx123"
    assert mapped["input_addresses"] == "['W1', 'W2']"
    assert mapped["output_amounts"] == "1.0, 2.5"
    assert mapped["timestamp"] == "2026-01-01T10:00:00Z"
    assert mapped["src_ip"] == "192.168.1.1"
    assert mapped["dst_port"] == "8333"


def test_parse_list_field():
    assert parse_list_field('["W1", "W2"]') == ["W1", "W2"]
    assert parse_list_field('W1, W2, W3') == ["W1", "W2", "W3"]
    assert parse_list_field('W1|W2') == ["W1", "W2"]
    assert parse_list_field([1.5, 2.5]) == [1.5, 2.5]
    assert parse_list_field(None) == []


def test_validation_array_parity():
    # Valid parity
    rec_valid = {
        "record_id": "row1",
        "timestamp": datetime.now(timezone.utc),
        "txid": "tx01",
        "input_addresses": ["W1", "W2"],
        "input_amounts": [1.0, 2.0],
        "output_addresses": ["W3"],
        "output_amounts": [2.99],
        "fee": 0.01
    }
    is_valid, issues = validate_record(rec_valid, row_number=1, kind="transaction")
    assert is_valid is True
    assert not any(i.issue_type == "error" for i in issues)

    # Invalid parity: input mismatch
    rec_invalid_input = dict(rec_valid)
    rec_invalid_input["input_amounts"] = [1.0]  # length 1 vs 2
    is_valid, issues = validate_record(rec_invalid_input, row_number=2, kind="transaction")
    assert is_valid is False
    assert any(i.code == "ARRAY_PARITY_INPUT_MISMATCH" for i in issues)

    # Invalid parity: output mismatch
    rec_invalid_output = dict(rec_valid)
    rec_invalid_output["output_amounts"] = [2.0, 1.0]  # length 2 vs 1
    is_valid, issues = validate_record(rec_invalid_output, row_number=3, kind="transaction")
    assert is_valid is False
    assert any(i.code == "ARRAY_PARITY_OUTPUT_MISMATCH" for i in issues)


def test_validation_monetary_warning():
    rec_mismatch = {
        "record_id": "row1",
        "timestamp": datetime.now(timezone.utc),
        "txid": "tx01",
        "input_addresses": ["W1"],
        "input_amounts": [10.0],
        "output_addresses": ["W2"],
        "output_amounts": [5.0],
        "fee": 0.01  # discrepancy 10.0 != 5.01
    }
    is_valid, issues = validate_record(rec_mismatch, row_number=1, kind="transaction")
    assert is_valid is True  # Warning does not invalidate row
    assert any(i.code == "MONETARY_DISCREPANCY" for i in issues)


def test_validation_network_fields():
    assert is_valid_ip("192.168.1.1") is True
    assert is_valid_ip("2001:0db8:85a3:0000:0000:8a2e:0370:7334") is True
    assert is_valid_ip("999.999.999.999") is False
    assert is_valid_port(8333) is True
    assert is_valid_port(70000) is False
    assert is_valid_port(-1) is False


def test_normalization():
    dt = normalize_timestamp("2026-01-01T10:00:00Z")
    assert dt is not None
    assert dt.tzinfo == timezone.utc

    norm_ip = normalize_ip(" 192.168.1.1 ")
    assert norm_ip == "192.168.1.1"

    rec = {
        "record_id": "r1",
        "timestamp": "2026-01-01T10:00:00Z",
        "src_ip": " 203.0.113.10 ",
        "src_port": "41000",
        "fee": "0.005",
        "geo_country": "in",
    }
    normalized = normalize_record(rec)
    assert normalized["src_ip"] == "203.0.113.10"
    assert normalized["src_port"] == 41000
    assert normalized["fee"] == 0.005
    assert normalized["geo_country"] == "IN"
