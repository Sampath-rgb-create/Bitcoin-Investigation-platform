import os
import json
import numpy as np
import pandas as pd

class WalletPreprocessor:
    """Preprocesses raw wallet/actor attributes for Actor RF, Wallet GraphSAGE, and FG-EGCN."""
    def __init__(self, schema_path: str = None):
        if schema_path is None:
            schema_path = os.path.join(os.path.dirname(__file__), "..", "schemas", "wallet_features.json")
        with open(schema_path, "r") as f:
            data = json.load(f)
        self.feature_cols = data["features"]
        self.num_features = len(self.feature_cols)

    def extract_static_mean_features(self, df_wal_feat: pd.DataFrame, df_wal_classes: pd.DataFrame):
        addr_to_idx = {addr: i for i, addr in enumerate(df_wal_classes['address'].values)}
        num_wallets = len(df_wal_classes)
        
        mean_feat_df = df_wal_feat.groupby('address')[self.feature_cols].mean().reset_index()
        mean_feat_df['idx'] = mean_feat_df['address'].map(addr_to_idx)
        
        X_raw = np.zeros((num_wallets, self.num_features), dtype=np.float32)
        valid_idx = mean_feat_df['idx'].dropna().astype(int).values
        valid_rows = mean_feat_df.loc[mean_feat_df['idx'].notna(), self.feature_cols].values.astype(np.float32)
        X_raw[valid_idx] = valid_rows
        return np.nan_to_num(X_raw, nan=0.0)
