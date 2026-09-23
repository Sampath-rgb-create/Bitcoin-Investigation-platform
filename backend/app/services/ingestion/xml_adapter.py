"""
XML Ingestion Adapter.
Safely parses XML datasets using defusedxml.
Expected structure (Section 5.6):
<records>
  <record>
    <timestamp>...</timestamp>
    <txid>...</txid>
    ...
  </record>
</records>
"""
from typing import Dict, Any, Generator, Tuple, List, Optional
try:
    import defusedxml.ElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from backend.app.services.ingestion.adapters import BaseAdapter
from backend.app.services.ingestion.field_mapping import map_raw_keys, parse_list_field
from backend.app.services.ingestion.validate import validate_record
from backend.app.services.ingestion.normalize import normalize_record
from backend.app.schemas.dataset import ValidationReportRow


class XMLAdapter(BaseAdapter):
    """
    Adapter for processing XML datasets using safe defusedxml parsing.
    """

    def parse_file(
        self,
        file_path: str,
        kind: str = "auto"
    ) -> Generator[Dict[str, Any], None, None]:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Find record elements (e.g., <record>, <transaction>, <observation>, or children of root)
        record_elements = []
        if root.tag.lower() in ("records", "transactions", "observations", "dataset", "root"):
            record_elements = list(root)
        else:
            record_elements = [root]

        for row_idx, elem in enumerate(record_elements, start=1):
            raw_dict: Dict[str, Any] = {}
            for child in elem:
                tag = child.tag.strip()
                # Check for child elements (e.g. <input_addresses><item>W1</item></input_addresses>)
                children = list(child)
                if children:
                    raw_dict[tag] = [c.text.strip() if c.text else "" for c in children]
                else:
                    raw_dict[tag] = child.text.strip() if child.text else ""

            mapped = map_raw_keys(raw_dict)
            if "record_id" not in mapped or not mapped["record_id"]:
                mapped["record_id"] = f"xml-row-{row_idx:06d}"

            # Parse array fields
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
