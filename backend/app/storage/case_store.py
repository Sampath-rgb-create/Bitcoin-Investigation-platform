"""
Case directory store.
Manages case directory hierarchy strictly under D: drive:
data/cases/<case_id>/
├── raw/
├── validated/
├── normalized/
├── correlated/
├── features/
├── graph/
├── models/
└── reports/
"""
import os
import shutil
from typing import Dict, List, Optional, Any
from backend.app.core.config import settings


class CaseStore:
    """
    Manages the directory structure and file paths for individual investigative cases.
    Ensures safe operations exclusively on the configured DATA_DIR (D: drive).
    """

    SUBDIRS = [
        "raw",
        "validated",
        "normalized",
        "correlated",
        "features",
        "graph",
        "models",
        "reports",
    ]

    def __init__(self, base_data_dir: Optional[str] = None):
        self.base_data_dir = os.path.abspath(base_data_dir or settings.DATA_DIR)
        self.cases_dir = os.path.join(self.base_data_dir, "cases")
        os.makedirs(self.cases_dir, exist_ok=True)

    def get_case_path(self, case_id: str) -> str:
        """Returns the absolute root directory path for a specific case."""
        return os.path.join(self.cases_dir, case_id)

    def init_case_directory(self, case_id: str) -> Dict[str, str]:
        """
        Creates the standard directory hierarchy for a case.
        Returns a dictionary mapping sub-directory name to absolute path.
        """
        case_root = self.get_case_path(case_id)
        paths = {"root": case_root}
        os.makedirs(case_root, exist_ok=True)

        for subdir in self.SUBDIRS:
            sub_path = os.path.join(case_root, subdir)
            os.makedirs(sub_path, exist_ok=True)
            paths[subdir] = sub_path

        return paths

    def get_subdir_path(self, case_id: str, subdir: str) -> str:
        """Returns the absolute path to a specific case subfolder, creating it if needed."""
        if subdir not in self.SUBDIRS and subdir != "root":
            raise ValueError(f"Unknown case subdirectory '{subdir}'. Expected one of {self.SUBDIRS}")
        path = os.path.join(self.get_case_path(case_id), "" if subdir == "root" else subdir)
        os.makedirs(path, exist_ok=True)
        return path

    def list_cases(self) -> List[str]:
        """Lists all case IDs currently in storage."""
        if not os.path.exists(self.cases_dir):
            return []
        return [
            d for d in os.listdir(self.cases_dir)
            if os.path.isdir(os.path.join(self.cases_dir, d))
        ]

    def save_artifact(self, case_id: str, subdir: str, filename: str, content: bytes) -> Dict[str, Any]:
        """
        Saves an artifact file in the given case subdirectory and calculates SHA-256 digest.
        Returns artifact metadata dictionary.
        """
        import hashlib
        from datetime import datetime, timezone
        sub_dir = self.get_subdir_path(case_id, subdir)
        target_path = os.path.join(sub_dir, filename)
        with open(target_path, "wb") as f:
            f.write(content)
        sha256_hash = hashlib.sha256(content).hexdigest()
        return {
            "case_id": case_id,
            "subdir": subdir,
            "filename": filename,
            "path": target_path,
            "sha256": sha256_hash,
            "size_bytes": len(content),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def verify_artifact(self, file_path: str, expected_sha256: str) -> bool:
        """
        Verifies that an artifact file matches the expected SHA-256 hash.
        """
        import hashlib
        if not os.path.exists(file_path):
            return False
        with open(file_path, "rb") as f:
            content = f.read()
        return hashlib.sha256(content).hexdigest().lower() == expected_sha256.lower()

    def get_case_manifest(self, case_id: str) -> Dict[str, Any]:
        """
        Scans all files in a case hierarchy and compiles a cryptographic provenance manifest.
        """
        import hashlib
        case_root = self.get_case_path(case_id)
        if not os.path.isdir(case_root):
            return {"case_id": case_id, "exists": False, "artifacts": []}

        artifacts = []
        for root, _, files in os.walk(case_root):
            for file in sorted(files):
                abs_file = os.path.join(root, file)
                rel_path = os.path.relpath(abs_file, case_root)
                try:
                    with open(abs_file, "rb") as f:
                        data = f.read()
                    sha256 = hashlib.sha256(data).hexdigest()
                    size = len(data)
                except Exception:
                    sha256 = None
                    size = 0

                artifacts.append({
                    "relative_path": rel_path.replace("\\", "/"),
                    "sha256": sha256,
                    "size_bytes": size,
                })

        return {
            "case_id": case_id,
            "exists": True,
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
        }

    def case_exists(self, case_id: str) -> bool:
        """Checks if case directory exists."""
        return os.path.isdir(self.get_case_path(case_id))

    def delete_case(self, case_id: str) -> bool:
        """Permanently deletes a case folder and all contained evidence files."""
        case_path = self.get_case_path(case_id)
        if os.path.isdir(case_path):
            shutil.rmtree(case_path)
            return True
        return False


case_store = CaseStore()
