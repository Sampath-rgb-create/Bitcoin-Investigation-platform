"""
JSON / JSON-Lines Ingestion Adapter.
Handles:
- Top-level array: [{"txid": "..."}, ...]
- Wrapped records object: {"records": [{"txid": "..."}]}
- JSON-Lines / NDJSON: one JSON object per line.
"""
import json
from typing import Dict, Any, Generator, Tuple, List, Optional
from backend.app.services.ingestion.adapters import BaseAdapter
from backend.app.services.ingestion.field_mapping import map_raw_keys, parse_list_field
from backend.app.services.ingestion.validate import validate_record
from backend.app.services.ingestion.normalize import normalize_record
from backend.app.schemas.dataset import ValidationReportRow


class JSONAdapter(BaseAdapter):
    """
    Adapter for processing JSON and JSON-Lines (NDJSON) datasets.
    """

    def parse_file(
        self,
        file_path: str,
        kind: str = "auto"
    ) -> Generator[Dict[str, Any], None, None]:
        with open(file_path, mode="r", encoding="utf-8", errors="replace") as f:
            content = f.read().strip()

        # 1. Try standard JSON first
        parsed_records: Optional[List[Dict[str, Any]]] = None
        if (content.startswith("[") and content.endswith("]")) or (content.startswith("{") and content.endswith("}")):
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    parsed_records = data
                elif isinstance(data, dict):
                    if "records" in data and isinstance(data["records"], list):
                        parsed_records = data["records"]
                    elif "data" in data and isinstance(data["data"], list):
                        parsed_records = data["data"]
                    else:
                        parsed_records = [data]
            except json.JSONDecodeError:
                parsed_records = None

        # 2. If not standard JSON, try line-delimited JSON (JSON-Lines / NDJSON)
        if parsed_records is None:
            parsed_records = []
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        parsed_records.append(obj)
                except json.JSONDecodeError:
                    continue

        for row_idx, raw_item in enumerate(parsed_records, start=1):
            if not isinstance(raw_item, dict):
                continue
            mapped = map_raw_keys(raw_item)
            if "record_id" not in mapped or not mapped["record_id"]:
                mapped["record_id"] = f"json-row-{row_idx:06d}"

            # Ensure array fields are parsed as lists
            for array_field in ("input_addresses", "output_addresses", "input_amounts", "output_amounts"):
                if array_field in mapped:
                    mapped[array_field] = parse_list_field(mapped[array_field])

            yield mapped

    def validate_and_parse(
        self,
        file_path: str,
        kind: str = "auto"
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[ValidationReportRow]]:
        accepted: List[Dict[str, Any]] = []
        rejected: List[Dict[str, Any]] = []
        all_issues: List[ValidationReportRow] = []

        for row_idx, record in enumerate(self.parse_file(file_path, kind=kind), start=1):
            is_valid, issues = validate_record(record, row_number=row_idx, kind=kind)
            all_issues.extend(issues)

            if is_valid:
                norm_rec = normalize_record(record)
                accepted.append(norm_rec)
            else:
                rejected.append(record)

        return accepted, rejected, all_issues
