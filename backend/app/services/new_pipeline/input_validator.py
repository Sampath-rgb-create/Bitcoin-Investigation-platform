"""
Forensic Input Validator for Bitcoin Investigation Platform.

Enforces strict forensic checks across uploaded case files:
1. transactions.csv
2. inputs.csv
3. outputs.csv
4. network.csv

Validates presence, schema types, non-null IDs, valid timestamps, monetary signs,
and referential integrity between inputs/outputs and transactions.
Never silently mutates or repairs broken forensic evidence.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
import pandas as pd

logger = logging.getLogger(__name__)


# Standardized Error Codes per NEW_PROTOTYPE_IMPLEMENTATION_PLAN.md §20.7
class ErrorCode:
    E001_INPUT_FILE_MISSING = "E001_INPUT_FILE_MISSING"
    E002_SCHEMA_INVALID = "E002_SCHEMA_INVALID"
    E003_TIMESTAMP_INVALID = "E003_TIMESTAMP_INVALID"
    E004_TRANSACTION_REFERENCE_MISSING = "E004_TRANSACTION_REFERENCE_MISSING"
    E005_FEATURE_DIMENSION_MISMATCH = "E005_FEATURE_DIMENSION_MISMATCH"
    E006_FEATURE_NAN = "E006_FEATURE_NAN"
    E007_GRAPH_ENDPOINT_MISSING = "E007_GRAPH_ENDPOINT_MISSING"
    E008_NEO4J_CONNECTION_FAILED = "E008_NEO4J_CONNECTION_FAILED"
    E009_GDS_PROJECTION_FAILED = "E009_GDS_PROJECTION_FAILED"
    E010_MODEL_LOAD_FAILED = "E010_MODEL_LOAD_FAILED"
    E011_MODEL_INFERENCE_FAILED = "E011_MODEL_INFERENCE_FAILED"
    E012_FUSION_INPUT_MISSING = "E012_FUSION_INPUT_MISSING"
    E013_TEMPORAL_ORDER_INVALID = "E013_TEMPORAL_ORDER_INVALID"


@dataclass
class ValidationError:
    code: str
    file: str
    message: str
    row_index: Optional[int] = None
    column: Optional[str] = None


@dataclass
class ValidationReport:
    is_valid: bool
    case_dir: str
    errors: List[ValidationError] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "is_valid": self.is_valid,
            "case_dir": self.case_dir,
            "error_count": len(self.errors),
            "errors": [
                {
                    "code": e.code,
                    "file": e.file,
                    "message": e.message,
                    "row_index": e.row_index,
                    "column": e.column,
                }
                for e in self.errors
            ],
            "stats": self.stats,
        }


class InputValidator:
    """
    Validates investigator-supplied forensic CSV files against contracts.
    """

    REQUIRED_FILES = {
        "transactions.csv": ["txid", "timestamp", "fee", "size"],
        "inputs.csv": ["txid", "prev_txid", "prev_vout", "address", "amount"],
        "outputs.csv": ["txid", "output_index", "address", "amount"],
        "network.csv": ["txid", "timestamp", "src_ip", "src_port", "dst_ip", "dst_port"],
    }

    def __init__(self, raw_dir: str):
        self.raw_dir = raw_dir

    def validate(self) -> ValidationReport:
        errors: List[ValidationError] = []
        stats: Dict[str, int] = {}

        # 1. Verify existence of required files
        for filename, required_cols in self.REQUIRED_FILES.items():
            filepath = os.path.join(self.raw_dir, filename)
            if not os.path.exists(filepath):
                errors.append(
                    ValidationError(
                        code=ErrorCode.E001_INPUT_FILE_MISSING,
                        file=filename,
                        message=f"Mandatory case file '{filename}' was not found in raw staging directory.",
                    )
                )

        if errors:
            return ValidationReport(is_valid=False, case_dir=self.raw_dir, errors=errors, stats=stats)

        # 2. Read and schema-validate transactions.csv
        tx_path = os.path.join(self.raw_dir, "transactions.csv")
        try:
            df_tx = pd.read_csv(tx_path)
            stats["transactions_count"] = len(df_tx)
            self._validate_columns(df_tx, "transactions.csv", self.REQUIRED_FILES["transactions.csv"], errors)
            txids = set(df_tx["txid"].dropna().astype(str))

            # Non-null IDs & duplicates
            if df_tx["txid"].isnull().any():
                errors.append(
                    ValidationError(
                        code=ErrorCode.E002_SCHEMA_INVALID,
                        file="transactions.csv",
                        column="txid",
                        message="transactions.csv contains null txid values.",
                    )
                )
            if df_tx["txid"].duplicated().any():
                errors.append(
                    ValidationError(
                        code=ErrorCode.E002_SCHEMA_INVALID,
                        file="transactions.csv",
                        column="txid",
                        message="transactions.csv contains duplicate txids.",
                    )
                )

            # Timestamps
            self._validate_timestamps(df_tx, "transactions.csv", "timestamp", errors)

            # Numeric checks
            self._validate_numeric(df_tx, "transactions.csv", ["fee", "size"], errors, non_negative=True)
        except Exception as e:
            errors.append(
                ValidationError(
                    code=ErrorCode.E002_SCHEMA_INVALID,
                    file="transactions.csv",
                    message=f"Failed to parse transactions.csv: {str(e)}",
                )
            )
            txids = set()

        # 3. Read and validate inputs.csv
        inp_path = os.path.join(self.raw_dir, "inputs.csv")
        try:
            df_inp = pd.read_csv(inp_path)
            stats["inputs_count"] = len(df_inp)
            self._validate_columns(df_inp, "inputs.csv", self.REQUIRED_FILES["inputs.csv"], errors)
            self._validate_numeric(df_inp, "inputs.csv", ["amount"], errors, non_negative=True)

            # Referential check: all txid must exist in transactions.csv
            inp_txids = set(df_inp["txid"].dropna().astype(str))
            orphan_txids = inp_txids - txids
            if orphan_txids:
                errors.append(
                    ValidationError(
                        code=ErrorCode.E004_TRANSACTION_REFERENCE_MISSING,
                        file="inputs.csv",
                        column="txid",
                        message=f"inputs.csv references {len(orphan_txids)} txids not present in transactions.csv.",
                    )
                )
        except Exception as e:
            errors.append(
                ValidationError(
                    code=ErrorCode.E002_SCHEMA_INVALID,
                    file="inputs.csv",
                    message=f"Failed to parse inputs.csv: {str(e)}",
                )
            )

        # 4. Read and validate outputs.csv
        out_path = os.path.join(self.raw_dir, "outputs.csv")
        try:
            df_out = pd.read_csv(out_path)
            stats["outputs_count"] = len(df_out)
            self._validate_columns(df_out, "outputs.csv", self.REQUIRED_FILES["outputs.csv"], errors)
            self._validate_numeric(df_out, "outputs.csv", ["amount"], errors, non_negative=True)

            out_txids = set(df_out["txid"].dropna().astype(str))
            orphan_out_txids = out_txids - txids
            if orphan_out_txids:
                errors.append(
                    ValidationError(
                        code=ErrorCode.E004_TRANSACTION_REFERENCE_MISSING,
                        file="outputs.csv",
                        column="txid",
                        message=f"outputs.csv references {len(orphan_out_txids)} txids not present in transactions.csv.",
                    )
                )
        except Exception as e:
            errors.append(
                ValidationError(
                    code=ErrorCode.E002_SCHEMA_INVALID,
                    file="outputs.csv",
                    message=f"Failed to parse outputs.csv: {str(e)}",
                )
            )

        # 5. Read and validate network.csv
        net_path = os.path.join(self.raw_dir, "network.csv")
        try:
            df_net = pd.read_csv(net_path)
            stats["network_observations_count"] = len(df_net)
            self._validate_columns(df_net, "network.csv", self.REQUIRED_FILES["network.csv"], errors)
            self._validate_timestamps(df_net, "network.csv", "timestamp", errors)
            self._validate_numeric(df_net, "network.csv", ["src_port", "dst_port"], errors, non_negative=True)
        except Exception as e:
            errors.append(
                ValidationError(
                    code=ErrorCode.E002_SCHEMA_INVALID,
                    file="network.csv",
                    message=f"Failed to parse network.csv: {str(e)}",
                )
            )

        is_valid = len(errors) == 0
        return ValidationReport(is_valid=is_valid, case_dir=self.raw_dir, errors=errors, stats=stats)

    def _validate_columns(self, df: pd.DataFrame, filename: str, required_cols: List[str], errors: List[ValidationError]):
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            errors.append(
                ValidationError(
                    code=ErrorCode.E002_SCHEMA_INVALID,
                    file=filename,
                    message=f"Missing required columns in {filename}: {missing}",
                )
            )

    def _validate_timestamps(self, df: pd.DataFrame, filename: str, col: str, errors: List[ValidationError]):
        if col not in df.columns:
            return
        try:
            pd.to_datetime(df[col], errors="raise")
        except Exception as e:
            errors.append(
                ValidationError(
                    code=ErrorCode.E003_TIMESTAMP_INVALID,
                    file=filename,
                    column=col,
                    message=f"Invalid timestamp formatting detected in {filename}.{col}: {str(e)}",
                )
            )

    def _validate_numeric(self, df: pd.DataFrame, filename: str, cols: List[str], errors: List[ValidationError], non_negative: bool = False):
        for col in cols:
            if col not in df.columns:
                continue
            numeric_series = pd.to_numeric(df[col], errors="coerce")
            if numeric_series.isnull().any():
                errors.append(
                    ValidationError(
                        code=ErrorCode.E002_SCHEMA_INVALID,
                        file=filename,
                        column=col,
                        message=f"Non-numeric values found in {filename}.{col}.",
                    )
                )
            elif non_negative and (numeric_series < 0).any():
                errors.append(
                    ValidationError(
                        code=ErrorCode.E002_SCHEMA_INVALID,
                        file=filename,
                        column=col,
                        message=f"Negative values found in non-negative column {filename}.{col}.",
                    )
                )
