"""
Ingestion Service module exporting adapters, validation, normalization, and factory.
"""
import os
from typing import Dict, Any, List, Tuple
from backend.app.services.ingestion.adapters import BaseAdapter
from backend.app.services.ingestion.csv_adapter import CSVAdapter
from backend.app.services.ingestion.json_adapter import JSONAdapter
from backend.app.services.ingestion.xml_adapter import XMLAdapter
from backend.app.services.ingestion.field_mapping import map_raw_keys, parse_list_field, CANONICAL_FIELD_ALIASES
from backend.app.services.ingestion.validate import validate_record, is_valid_ip, is_valid_port
from backend.app.services.ingestion.normalize import normalize_record, normalize_timestamp, normalize_ip, compute_sha256_bytes
from backend.app.schemas.dataset import ValidationReportRow, ValidationReport


def get_adapter_for_format(file_format: str) -> BaseAdapter:
    """
    Returns the appropriate adapter instance for a given format string or file extension.
    """
    fmt = file_format.lower().lstrip(".")
    if fmt in ("csv", "tsv", "txt"):
        return CSVAdapter()
    elif fmt in ("json", "ndjson", "jsonl"):
        return JSONAdapter()
    elif fmt in ("xml",):
        return XMLAdapter()
    else:
        raise ValueError(f"Unsupported file format: {file_format}")


def ingest_file(
    file_path: str,
    kind: str = "auto"
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[ValidationReportRow]]:
    """
    Convenience function to auto-detect file format, parse, validate and normalize records.
    """
    _, ext = os.path.splitext(file_path)
    adapter = get_adapter_for_format(ext or "csv")
    return adapter.validate_and_parse(file_path, kind=kind)
