"""
Bridge Service for SIH Multi-Brain Supervised ML and Tri-Domain Isolation Forest
in Bitcoin Investigation Platform.

Provides unified inference over:
1. Frozen 9-Brain Supervised Multi-Domain Stack:
   - Transaction: RF (182), GATv2 (182), FG-EGCN (182)
   - Wallet: Actor RF (55), GraphSAGE (55), FG-EGCN (55)
   - Network: RF (13), GraphSAGE (13), TGAT (13)
   - L2 Temporal Walk-Forward OOF Meta-Stacker (C=0.01, threshold=0.675)
2. Tri-Domain Isolation Forest Anomaly Layer:
   - Transaction Isolation Forest (182)
   - Wallet Isolation Forest (55)
   - Network Isolation Forest (13)
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
import joblib

try:
    import torch
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    F = None
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ML_DIR = os.path.join(BASE_DIR, "models")
if not os.path.exists(ML_DIR):
    ML_DIR = os.path.join(BASE_DIR, "ml_engine", "SIH_SUPERVISED_ML")

ARCH_DIRS = [
    os.path.join(BASE_DIR, "models"),
    os.path.join(BASE_DIR, "ml_engine", "SIH_SUPERVISED_ML", "architectures"),
]
for p in ARCH_DIRS:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)


class MLInferenceEngine:
    """
    Unified manager for the SIH multi-brain supervised models and isolation forests.
    Supports seamless laptop-to-laptop transfers.
    """

    def __init__(self, ml_dir: Optional[str] = None):
        self.ml_dir = ml_dir or ML_DIR
        self.is_loaded = False
        self.supervised_available = False
        self.isolation_forests_available = False

        # Supervised models
        self.rf_tx = None
        self.gat_tx = None
        self.fg_tx = None
        self.rf_wal = None
        self.sage_wal = None
        self.fg_wal = None
        self.rf_net = None
        self.sage_net = None
        self.tgat_net = None
        self.meta_stacker = None
        self.threshold = 0.675

        # Isolation forests
        self.if_tx = None
        self.if_wal = None
        self.if_net = None

        self._load_models()

    def _resolve_model_path(self, subpath: str) -> Optional[str]:
        """Resolves model file path across top-level models/ or ml_engine/ directory."""
        candidates = [
            os.path.join(self.ml_dir, subpath),
            os.path.join(self.ml_dir, "models", subpath),
            os.path.join(BASE_DIR, "models", subpath),
            os.path.join(BASE_DIR, "ml_engine", "SIH_SUPERVISED_ML", "models", subpath),
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return None

    def _load_models(self):
        """Loads all serialized models safely with fallback."""
        try:
            # 1. Load Threshold
            th_path = self._resolve_model_path(os.path.join("fusion", "threshold.json"))
            if th_path:
                with open(th_path, "r", encoding="utf-8") as f:
                    self.threshold = float(json.load(f).get("threshold", 0.675))

            # 2. Load Meta-Stacker
            stacker_path = self._resolve_model_path(os.path.join("fusion", "oof_meta_stacker.joblib"))
            if stacker_path:
                self.meta_stacker = joblib.load(stacker_path)

            # 3. Load RF Classifiers
            rf_tx_p = self._resolve_model_path(os.path.join("transaction", "rf.joblib"))
            if rf_tx_p:
                self.rf_tx = joblib.load(rf_tx_p)

            rf_wal_p = self._resolve_model_path(os.path.join("wallet", "actor_rf.joblib"))
            if rf_wal_p:
                self.rf_wal = joblib.load(rf_wal_p)

            rf_net_p = self._resolve_model_path(os.path.join("network", "rf.joblib"))
            if rf_net_p:
                self.rf_net = joblib.load(rf_net_p)

            # 4. Load PyTorch GNNs (architectures + weights)
            if TORCH_AVAILABLE:
                try:
                    from gatv2_model import GATv2Model
                    from fgecgn_model import FGEGCNModel
                    from graphsage_model import SparseGraphSAGE
                    from tgat_model import SparseNetworkTGAT

                    gat_tx_p = self._resolve_model_path(os.path.join("transaction", "gatv2.pt"))
                    if gat_tx_p:
                        self.gat_tx = GATv2Model(in_d=182, hidden_d=32, heads=4)
                        self.gat_tx.load_state_dict(torch.load(gat_tx_p, map_location="cpu", weights_only=True))
                        self.gat_tx.eval()

                    fg_tx_p = self._resolve_model_path(os.path.join("transaction", "fgecgn.pt"))
                    if fg_tx_p:
                        self.fg_tx = FGEGCNModel(in_channels=182, hidden_dim=64, top_k=50)
                        self.fg_tx.load_state_dict(torch.load(fg_tx_p, map_location="cpu", weights_only=True))
                        self.fg_tx.eval()

                    sage_wal_p = self._resolve_model_path(os.path.join("wallet", "graphsage.pt"))
                    if sage_wal_p:
                        self.sage_wal = SparseGraphSAGE(in_channels=55, hidden_dim=64)
                        self.sage_wal.load_state_dict(torch.load(sage_wal_p, map_location="cpu", weights_only=True))
                        self.sage_wal.eval()

                    fg_wal_p = self._resolve_model_path(os.path.join("wallet", "fgecgn.pt"))
                    if fg_wal_p:
                        self.fg_wal = FGEGCNModel(in_channels=55, hidden_dim=64, top_k=50)
                        self.fg_wal.load_state_dict(torch.load(fg_wal_p, map_location="cpu", weights_only=True))
                        self.fg_wal.eval()

                    sage_net_p = self._resolve_model_path(os.path.join("network", "graphsage.pt"))
                    if sage_net_p:
                        self.sage_net = SparseGraphSAGE(in_features=13, hidden_dim=64)
                        self.sage_net.load_state_dict(torch.load(sage_net_p, map_location="cpu", weights_only=True))
                        self.sage_net.eval()

                    tgat_net_p = self._resolve_model_path(os.path.join("network", "tgat.pt"))
                    if tgat_net_p:
                        self.tgat_net = SparseNetworkTGAT(in_features=13, time_dim=16, hidden_dim=64)
                        self.tgat_net.load_state_dict(torch.load(tgat_net_p, map_location="cpu", weights_only=True))
                        self.tgat_net.eval()

                    self.supervised_available = True
                except Exception as e:
                    logger.warning(f"Could not load PyTorch GNN brains: {e}. Only RF/IF available.")

            # 5. Load Isolation Forests
            if_tx_p = self._resolve_model_path(os.path.join("transaction", "isolation_forest.joblib"))
            if if_tx_p:
                self.if_tx = joblib.load(if_tx_p)

            if_wal_p = self._resolve_model_path(os.path.join("wallet", "isolation_forest.joblib"))
            if if_wal_p:
                self.if_wal = joblib.load(if_wal_p)

            if_net_p = self._resolve_model_path(os.path.join("network", "isolation_forest.joblib"))
            if if_net_p:
                self.if_net = joblib.load(if_net_p)

            if self.if_tx and self.if_wal and self.if_net:
                self.isolation_forests_available = True

            self.is_loaded = True
            logger.info("SIH Multi-Brain and Isolation Forest models loaded successfully.")

        except Exception as exc:
            logger.error(f"Error loading ML models: {exc}")

    def score_isolation_forest_transaction(self, features_182: np.ndarray) -> float:
        """Scores 182-dim transaction vector using Transaction Isolation Forest."""
        if not self.if_tx:
            return 0.0
        X = np.nan_to_num(features_182.reshape(1, -1), nan=0.0, posinf=0.0, neginf=0.0)
        dec = float(self.if_tx.decision_function(X)[0])
        anom = -dec
        return float(np.clip((anom + 0.15) / 0.30, 0.0, 1.0))

    def score_isolation_forest_wallet(self, features_55: np.ndarray) -> float:
        """Scores 55-dim wallet vector using Wallet Isolation Forest."""
        if not self.if_wal:
            return 0.0
        X = np.nan_to_num(features_55.reshape(1, -1), nan=0.0, posinf=0.0, neginf=0.0)
        dec = float(self.if_wal.decision_function(X)[0])
        anom = -dec
        return float(np.clip((anom + 0.15) / 0.30, 0.0, 1.0))

    @property
    def is_ready(self) -> bool:
        """Returns True if models are loaded and available."""
        return self.is_loaded and (self.supervised_available or self.isolation_forests_available)

    def predict_wallet(self, features_55: np.ndarray) -> float:
        """
        Predicts illicit probability for a wallet entity using the Actor RF model.
        Returns float between 0.0 and 1.0.
        """
        if not self.rf_wal:
            return 0.0
        X = np.nan_to_num(features_55.reshape(1, -1), nan=0.0, posinf=0.0, neginf=0.0)
        try:
            prob = float(self.rf_wal.predict_proba(X)[0, 1])
            return prob
        except Exception:
            return 0.0

    def score_isolation_forest_network(self, features_13: np.ndarray) -> float:
        """Scores 13-dim network vector using Network Isolation Forest."""
        if not self.if_net:
            return 0.0
        X = np.nan_to_num(features_13.reshape(1, -1), nan=0.0, posinf=0.0, neginf=0.0)
        dec = float(self.if_net.decision_function(X)[0])
        anom = -dec
        return float(np.clip((anom + 0.15) / 0.30, 0.0, 1.0))

    def predict_9_brains(
        self,
        X_tx: np.ndarray,
        edge_index_tx: Optional[np.ndarray],
        X_wal: np.ndarray,
        edge_index_wal: Optional[np.ndarray],
        X_net: np.ndarray,
        edge_index_net: Optional[np.ndarray],
    ) -> Dict[str, Any]:
        """
        Executes inference across all 9 brains and the L2 Meta-Stacker.
        Returns individual model probabilities, fused score, decision, and IF anomaly scores.
        """
        # 1. Transaction RF
        p_rf_tx = float(self.rf_tx.predict_proba(X_tx.reshape(1, -1))[0, 1]) if self.rf_tx else 0.0

        # 2. Transaction GATv2
        p_gat_tx = p_rf_tx
        if TORCH_AVAILABLE and self.gat_tx:
            with torch.no_grad():
                x_t = torch.tensor(X_tx.reshape(1, -1), dtype=torch.float32)
                # Expand to at least 2 nodes for message passing if isolated
                if x_t.shape[0] < 2:
                    x_t = torch.cat([x_t, x_t], dim=0)
                e_t = torch.tensor([[0, 1], [1, 0]], dtype=torch.long)
                if edge_index_tx is not None and len(edge_index_tx) > 0:
                    e_t = torch.tensor(edge_index_tx, dtype=torch.long)
                out = self.gat_tx(x_t, e_t)
                p_gat_tx = float(F.softmax(out, dim=-1)[0, 1].item())

        # 3. Transaction FG-EGCN
        p_fg_tx = p_rf_tx
        if TORCH_AVAILABLE and self.fg_tx:
            with torch.no_grad():
                x_t = torch.tensor(X_tx.reshape(1, -1), dtype=torch.float32)
                if x_t.shape[0] < 2:
                    x_t = torch.cat([x_t, x_t], dim=0)
                e_t = torch.tensor([[0, 1], [1, 0]], dtype=torch.long)
                logits, _ = self.fg_tx(x_t, e_t)
                p_fg_tx = float(F.softmax(logits, dim=-1)[0, 1].item())

        # 4. Wallet Actor RF
        p_rf_wal = float(self.rf_wal.predict_proba(X_wal.reshape(1, -1))[0, 1]) if self.rf_wal else 0.0

        # 5. Wallet GraphSAGE
        p_sage_wal = p_rf_wal
        if TORCH_AVAILABLE and self.sage_wal:
            with torch.no_grad():
                x_w = torch.tensor(X_wal.reshape(1, -1), dtype=torch.float32)
                if x_w.shape[0] < 2:
                    x_w = torch.cat([x_w, x_w], dim=0)
                adj_w = torch.sparse_coo_tensor(torch.tensor([[0, 1], [1, 0]]), torch.tensor([1.0, 1.0]), (2, 2))
                out_w = self.sage_wal(x_w, adj_w)
                p_sage_wal = float(F.softmax(out_w, dim=-1)[0, 1].item())

        # 6. Wallet FG-EGCN
        p_fg_wal = p_rf_wal
        if TORCH_AVAILABLE and self.fg_wal:
            with torch.no_grad():
                x_w = torch.tensor(X_wal.reshape(1, -1), dtype=torch.float32)
                if x_w.shape[0] < 2:
                    x_w = torch.cat([x_w, x_w], dim=0)
                e_w = torch.tensor([[0, 1], [1, 0]], dtype=torch.long)
                logits_w, _ = self.fg_wal(x_w, e_w)
                p_fg_wal = float(F.softmax(logits_w, dim=-1)[0, 1].item())

        # 7. Network RF
        p_rf_net = float(self.rf_net.predict_proba(X_net.reshape(1, -1))[0, 1]) if self.rf_net else 0.0

        # 8. Network GraphSAGE
        p_sage_net = p_rf_net
        if TORCH_AVAILABLE and self.sage_net:
            with torch.no_grad():
                x_n = torch.tensor(X_net.reshape(1, -1), dtype=torch.float32)
                if x_n.shape[0] < 2:
                    x_n = torch.cat([x_n, x_n], dim=0)
                adj_n = torch.sparse_coo_tensor(torch.tensor([[0, 1], [1, 0]]), torch.tensor([1.0, 1.0]), (2, 2))
                out_n = self.sage_net(x_n, adj_n)
                p_sage_net = float(F.softmax(out_n, dim=-1)[0, 1].item())

        # 9. Network TGAT
        p_tgat_net = p_rf_net
        if TORCH_AVAILABLE and self.tgat_net:
            with torch.no_grad():
                x_n = torch.tensor(X_net.reshape(1, -1), dtype=torch.float32)
                if x_n.shape[0] < 2:
                    x_n = torch.cat([x_n, x_n], dim=0)
                adj_n = torch.sparse_coo_tensor(torch.tensor([[0, 1], [1, 0]]), torch.tensor([1.0, 1.0]), (2, 2))
                t_d = torch.tensor([35.0, 35.0])
                out_tgat = self.tgat_net(x_n, adj_n, t_d)
                p_tgat_net = float(F.softmax(out_tgat, dim=-1)[0, 1].item())

        # 10. L2 Meta-Stacker
        meta_inputs = np.array(
            [[p_rf_tx, p_gat_tx, p_fg_tx, p_rf_wal, p_sage_wal, p_fg_wal, p_rf_net, p_sage_net, p_tgat_net]],
            dtype=np.float32,
        )
        supervised_score, is_illicit = self.score_9_brain_stack(meta_inputs)

        # Isolation forest scores
        anom_tx = self.score_isolation_forest_transaction(X_tx)
        anom_wal = self.score_isolation_forest_wallet(X_wal)
        anom_net = self.score_isolation_forest_network(X_net)

        return {
            "probabilities": {
                "RF_tx": round(p_rf_tx, 4),
                "GATv2_tx": round(p_gat_tx, 4),
                "FG_EGCN_tx": round(p_fg_tx, 4),
                "RF_wallet": round(p_rf_wal, 4),
                "GraphSAGE_wallet": round(p_sage_wal, 4),
                "FG_EGCN_wallet": round(p_fg_wal, 4),
                "RF_network": round(p_rf_net, 4),
                "GraphSAGE_network": round(p_sage_net, 4),
                "TGAT_network": round(p_tgat_net, 4),
            },
            "supervised_score": supervised_score,
            "is_illicit": is_illicit,
            "threshold": self.threshold,
            "isolation_forest": {
                "transaction_anomaly": round(anom_tx, 4),
                "wallet_anomaly": round(anom_wal, 4),
                "network_anomaly": round(anom_net, 4),
            },
        }

    def score_9_brain_stack(self, meta_prob_inputs: np.ndarray) -> Tuple[float, int]:
        """Computes calibrated risk score [0, 100] and decision using the frozen OOF Meta-Stacker."""
        if not self.meta_stacker:
            return 0.0, 0
        X = np.nan_to_num(meta_prob_inputs.reshape(1, 9), nan=0.0, posinf=0.0, neginf=0.0)
        prob = float(self.meta_stacker.predict_proba(X)[0, 1])
        priority_score = round(prob * 100.0, 2)
        is_illicit = int(prob >= self.threshold)
        return priority_score, is_illicit


# Global singleton instance
ml_engine = MLInferenceEngine()
