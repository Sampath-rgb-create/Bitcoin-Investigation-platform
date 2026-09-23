"""
CSV Ingestion Adapter.
Streams rows from CSV files, handles headers, aliases, array columns,
validates with parity checks, and normalizes fields.
"""
import csv
from typing import Dict, Any, Generator, Tuple, List, Optional
from backend.app.services.ingestion.adapters import BaseAdapter
from backend.app.services.ingestion.field_mapping import map_raw_keys, parse_list_field
from backend.app.services.ingestion.validate import validate_record
from backend.app.services.ingestion.normalize import normalize_record
from backend.app.schemas.dataset import ValidationReportRow


class CSVAdapter(BaseAdapter):
    """
    Adapter for processing CSV datasets.
    Handles delimiters (comma, semicolon, tab), field aliases, and array strings.
    """

    def parse_file(
        self,
        file_path: str,
        kind: str = "auto"
    ) -> Generator[Dict[str, Any], None, None]:
        with open(file_path, mode="r", encoding="utf-8-sig", errors="replace") as f:
            # Sniff delimiter safely
            sample = f.read(4096)
            f.seek(0)
            delimiter = ","
            try:
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample, delimiters=",\t;|")
                delimiter = dialect.delimiter
            except Exception:
                pass

            reader = csv.DictReader(f, delimiter=delimiter)
            for row_idx, raw_row in enumerate(reader, start=1):
                # Clean row dictionary
                cleaned_raw = {k.strip(): v for k, v in raw_row.items() if k is not None}
                mapped = map_raw_keys(cleaned_raw)

                # Ensure record_id exists
                if "record_id" not in mapped or not mapped["record_id"]:
                    mapped["record_id"] = f"csv-row-{row_idx:06d}"

                # Parse array columns
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
