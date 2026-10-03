import os
import json
import numpy as np
import pandas as pd

class TransactionPreprocessor:
    """Preprocesses raw transaction tabular attributes for RF, GATv2, and FG-EGCN."""
    def __init__(self, schema_path: str = None):
        if schema_path is None:
            schema_path = os.path.join(os.path.dirname(__file__), "..", "schemas", "transaction_features.json")
        with open(schema_path, "r") as f:
            data = json.load(f)
        self.feature_cols = data["features"]
        self.num_features = len(self.feature_cols)

    def fit_transform(self, df: pd.DataFrame, train_mask: np.ndarray = None):
        X_raw = df[self.feature_cols].values.astype(np.float32)
        if train_mask is None:
            train_mask = np.ones(len(df), dtype=bool)
        self.mean = np.mean(X_raw[train_mask], axis=0)
        self.std = np.std(X_raw[train_mask], axis=0)
        self.std[self.std == 0] = 1.0
        X_norm = (X_raw - self.mean) / self.std
        return np.nan_to_num(X_norm, nan=0.0)

    def transform(self, df: pd.DataFrame):
        X_raw = df[self.feature_cols].values.astype(np.float32)
        X_norm = (X_raw - self.mean) / self.std
        return np.nan_to_num(X_norm, nan=0.0)
