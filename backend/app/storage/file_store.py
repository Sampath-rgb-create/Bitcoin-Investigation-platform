"""
File store for managing raw uploaded artifacts, reports, and JSON artifacts.
Computes and verifies SHA-256 digests.
"""
import os
import shutil
from typing import Optional, Tuple
from backend.app.services.ingestion.normalize import compute_sha256_bytes
from backend.app.storage.case_store import case_store


class FileStore:
    """
    Handles saving, reading, and verifying raw files and artifacts within case folders.
    """

    def __init__(self):
        self.case_store = case_store

    def save_raw_upload(
        self,
        case_id: str,
        filename: str,
        content_bytes: bytes
    ) -> Tuple[str, str, int]:
        """
        Saves uploaded file content into data/cases/<case_id>/raw/<filename>.
        Returns:
            (absolute_file_path, sha256_hex, byte_size)
        """
        raw_dir = self.case_store.get_subdir_path(case_id, "raw")
        target_path = os.path.join(raw_dir, filename)

        with open(target_path, "wb") as f:
            f.write(content_bytes)

        sha256 = compute_sha256_bytes(content_bytes)
        size = len(content_bytes)
        return target_path, sha256, size

    def read_file_bytes(self, file_path: str) -> bytes:
        """Reads binary file contents."""
        with open(file_path, "rb") as f:
            return f.read()

    def read_file_text(self, file_path: str, encoding: str = "utf-8") -> str:
        """Reads text file contents."""
        with open(file_path, "r", encoding=encoding, errors="replace") as f:
            return f.read()

    def write_file_text(self, file_path: str, text: str, encoding: str = "utf-8") -> None:
        """Writes text content ensuring parent directories exist."""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding=encoding) as f:
            f.write(text)

    def verify_file_checksum(self, file_path: str, expected_sha256: str) -> bool:
        """Verifies if the file at file_path matches expected SHA-256."""
        if not os.path.exists(file_path):
            return False
        content = self.read_file_bytes(file_path)
        actual = compute_sha256_bytes(content)
        return actual.lower() == expected_sha256.lower()

    def is_safe_case_path(self, case_id: str, file_path: str) -> bool:
        """Checks if file_path is strictly within the case directory."""
        case_dir = os.path.abspath(self.case_store.get_case_path(case_id))
        target_abs = os.path.abspath(file_path)
        return target_abs.startswith(case_dir)


file_store = FileStore()
