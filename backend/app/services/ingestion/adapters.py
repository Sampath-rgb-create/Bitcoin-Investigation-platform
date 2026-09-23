"""
Base ingestion adapter interface.
Defines the contract for dataset file parsers (CSV, JSON, XML).
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Generator, Tuple, List, Optional
from backend.app.schemas.dataset import ValidationReportRow


class BaseAdapter(ABC):
    """
    Abstract base class for all file format ingestion adapters.
    """

    @abstractmethod
    def parse_file(
        self,
        file_path: str,
        kind: str = "auto"
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Parses the given file and yields raw unvalidated dictionary records with
        standardized/mapped field names.
        """
        pass

    @abstractmethod
    def validate_and_parse(
        self,
        file_path: str,
        kind: str = "auto"
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[ValidationReportRow]]:
        """
        Parses, validates, and normalizes records from the file.
        Returns:
            (accepted_records, rejected_records, validation_issues)
        """
        pass
