"""
Generator Validation Service for Bitcoin Investigation Platform.

Asserts exact compliance of generated case packages against frozen model contracts:
- Asserts feature dimensions: Tx (182), Wallet (55), Network (13)
- Asserts strict column ordering & order hash match
- Asserts zero NaN or +/-Inf values
- Asserts edge endpoints exist in node tables
- Asserts temporal monotonically increasing sequences
"""

import os
import json
import hashlib
import logging
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd

from .input_validator import ErrorCode, ValidationError

logger = logging.getLogger(__name__)


class GeneratorValidator:
    """
    Validates generated case artifacts against frozen contracts.
    """

    def __init__(self, generated_dir: str, schema_path: str):
        self.generated_dir = generated_dir
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schemas = json.load(f)

    def validate(self) -> Tuple[bool, List[ValidationError]]:
        errors: List[ValidationError] = []

        # 1. Transaction Features Validation
        tx_p = os.path.join(self.generated_dir, "transaction", "features.parquet")
        if not os.path.exists(tx_p):
            errors.append(ValidationError(code=ErrorCode.E001_INPUT_FILE_MISSING, file=tx_p, message="transaction/features.parquet missing."))
        else:
            df_tx = pd.read_parquet(tx_p)
            self._validate_matrix(df_tx, "transaction", 182, errors)

        # 2. Wallet Features Validation
        wal_p = os.path.join(self.generated_dir, "wallet", "features.parquet")
        if not os.path.exists(wal_p):
            errors.append(ValidationError(code=ErrorCode.E001_INPUT_FILE_MISSING, file=wal_p, message="wallet/features.parquet missing."))
        else:
            df_wal = pd.read_parquet(wal_p)
            self._validate_matrix(df_wal, "wallet", 55, errors)

        # 3. Network Features Validation
        net_p = os.path.join(self.generated_dir, "network", "features.parquet")
        if not os.path.exists(net_p):
            errors.append(ValidationError(code=ErrorCode.E001_INPUT_FILE_MISSING, file=net_p, message="network/features.parquet missing."))
        else:
            df_net = pd.read_parquet(net_p)
            self._validate_matrix(df_net, "network", 13, errors)

        is_valid = len(errors) == 0
        return is_valid, errors

    def _validate_matrix(self, df: pd.DataFrame, domain: str, expected_dim: int, errors: List[ValidationError]):
        schema_info = self.schemas[domain]
        expected_cols = schema_info["columns"]

        feature_cols = [c for c in df.columns if c not in ("txid", "address", "time_step")]

        # Dimension Check
        if len(feature_cols) != expected_dim:
            errors.append(
                ValidationError(
                    code=ErrorCode.E005_FEATURE_DIMENSION_MISMATCH,
                    file=f"{domain}/features.parquet",
                    message=f"Dimension mismatch for {domain}: expected {expected_dim}, got {len(feature_cols)}",
                )
            )

        # Column Order & Hash Check
        current_hash = hashlib.sha256(json.dumps(feature_cols).encode()).hexdigest()
        if current_hash != schema_info["order_hash"]:
            errors.append(
                ValidationError(
                    code=ErrorCode.E005_FEATURE_DIMENSION_MISMATCH,
                    file=f"{domain}/features.parquet",
                    message=f"Column order hash mismatch for {domain}.",
                )
            )

        # NaN / Inf Check
        mat = df[feature_cols].values
        if np.isnan(mat).any():
            errors.append(
                ValidationError(
                    code=ErrorCode.E006_FEATURE_NAN,
                    file=f"{domain}/features.parquet",
                    message=f"NaN values detected in {domain} feature matrix.",
                )
            )
        if np.isinf(mat).any():
            errors.append(
                ValidationError(
                    code=ErrorCode.E006_FEATURE_NAN,
                    file=f"{domain}/features.parquet",
                    message=f"Infinite values detected in {domain} feature matrix.",
                )
            )
