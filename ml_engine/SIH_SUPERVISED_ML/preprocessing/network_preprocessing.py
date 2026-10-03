import os
import json
import numpy as np
import pandas as pd

class NetworkPreprocessor:
    """Preprocesses raw bipartite originator-recipient aggregates for Network RF, GraphSAGE, and TGAT."""
    def __init__(self, schema_path: str = None):
        if schema_path is None:
            schema_path = os.path.join(os.path.dirname(__file__), "..", "schemas", "network_features.json")
        with open(schema_path, "r") as f:
            data = json.load(f)
        self.feature_cols = data["features"]
        self.num_features = len(self.feature_cols)

    def standardize(self, df_net: pd.DataFrame, train_mask: np.ndarray = None):
        X_raw = df_net[self.feature_cols].values.astype(np.float32)
        if train_mask is None:
            train_mask = np.ones(len(df_net), dtype=bool)
        mean = np.mean(X_raw[train_mask], axis=0)
        std = np.std(X_raw[train_mask], axis=0)
        std[std == 0] = 1.0
        X_norm = (X_raw - mean) / std
        return np.nan_to_num(X_norm, nan=0.0)
