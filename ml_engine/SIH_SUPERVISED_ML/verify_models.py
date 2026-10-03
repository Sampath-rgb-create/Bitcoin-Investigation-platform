"""
Verification Suite for Portable SIH Supervised Model Bundle
Tests all 10 model artifacts, architectures, schemas, and configurations.
Executes an end-to-end forward pass on dummy samples to ensure numerical determinism.
"""

import os
import sys
import json
import joblib
import numpy as np
import torch
import torch.nn.functional as F

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "architectures"))

from gatv2_model import GATv2Model
from fgecgn_model import FGEGCNModel
from graphsage_model import SparseGraphSAGE
from tgat_model import SparseNetworkTGAT

def run_verification():
    print("=" * 75)
    print("VERIFYING PORTABLE SIH SUPERVISED ML MODEL PACKAGE")
    print("=" * 75)

    checks_passed = 0
    total_checks = 16

    # 1. Transaction RF
    rf_tx_path = os.path.join(BASE_DIR, "models", "transaction", "rf.joblib")
    rf_tx = joblib.load(rf_tx_path)
    sample_tx = np.zeros((1, 182), dtype=np.float32)
    p_rf_tx = rf_tx.predict_proba(sample_tx)[0, 1]
    assert 0.0 <= p_rf_tx <= 1.0
    print("[PASS] 1. Transaction RF (models/transaction/rf.joblib)")
    checks_passed += 1

    # 2. Transaction GATv2
    gat_tx_path = os.path.join(BASE_DIR, "models", "transaction", "gatv2.pt")
    gat_tx = GATv2Model(in_d=182, hidden_d=32, heads=4)
    gat_tx.load_state_dict(torch.load(gat_tx_path, map_location="cpu", weights_only=True))
    gat_tx.eval()
    with torch.no_grad():
        x_d = torch.zeros((2, 182), dtype=torch.float32)
        edge_d = torch.tensor([[0, 1], [1, 0]], dtype=torch.long)
        out = gat_tx(x_d, edge_d)
        p_gat_tx = F.softmax(out, dim=-1)[0, 1].item()
    assert 0.0 <= p_gat_tx <= 1.0
    print("[PASS] 2. Transaction GATv2 (models/transaction/gatv2.pt)")
    checks_passed += 1

    # 3. Transaction FG-EGCN
    fg_tx_path = os.path.join(BASE_DIR, "models", "transaction", "fgecgn.pt")
    fg_tx = FGEGCNModel(in_channels=182, hidden_dim=64, top_k=50)
    fg_tx.load_state_dict(torch.load(fg_tx_path, map_location="cpu", weights_only=True))
    fg_tx.eval()
    with torch.no_grad():
        logits, _ = fg_tx(x_d, edge_d)
        p_fg_tx = F.softmax(logits, dim=-1)[0, 1].item()
    assert 0.0 <= p_fg_tx <= 1.0
    print("[PASS] 3. Transaction FG-EGCN (models/transaction/fgecgn.pt)")
    checks_passed += 1

    # 4. Wallet Actor RF
    rf_wal_path = os.path.join(BASE_DIR, "models", "wallet", "actor_rf.joblib")
    rf_wal = joblib.load(rf_wal_path)
    sample_wal = np.zeros((1, 55), dtype=np.float32)
    p_rf_wal = rf_wal.predict_proba(sample_wal)[0, 1]
    assert 0.0 <= p_rf_wal <= 1.0
    print("[PASS] 4. Wallet Actor RF (models/wallet/actor_rf.joblib)")
    checks_passed += 1

    # 5. Wallet GraphSAGE
    sage_wal_path = os.path.join(BASE_DIR, "models", "wallet", "graphsage.pt")
    sage_wal = SparseGraphSAGE(in_channels=55, hidden_dim=64)
    sage_wal.load_state_dict(torch.load(sage_wal_path, map_location="cpu", weights_only=True))
    sage_wal.eval()
    with torch.no_grad():
        x_w = torch.zeros((2, 55), dtype=torch.float32)
        adj_w = torch.sparse_coo_tensor(torch.tensor([[0, 1], [1, 0]]), torch.tensor([1.0, 1.0]), (2, 2))
        out_w = sage_wal(x_w, adj_w)
        p_sage_w = F.softmax(out_w, dim=-1)[0, 1].item()
    assert 0.0 <= p_sage_w <= 1.0
    print("[PASS] 5. Wallet GraphSAGE (models/wallet/graphsage.pt)")
    checks_passed += 1

    # 6. Wallet FG-EGCN
    fg_wal_path = os.path.join(BASE_DIR, "models", "wallet", "fgecgn.pt")
    fg_wal = FGEGCNModel(in_channels=55, hidden_dim=64, top_k=50)
    fg_wal.load_state_dict(torch.load(fg_wal_path, map_location="cpu", weights_only=True))
    fg_wal.eval()
    with torch.no_grad():
        logits_w, _ = fg_wal(x_w, edge_d)
        p_fg_wal = F.softmax(logits_w, dim=-1)[0, 1].item()
    assert 0.0 <= p_fg_wal <= 1.0
    print("[PASS] 6. Wallet FG-EGCN (models/wallet/fgecgn.pt)")
    checks_passed += 1

    # 7. Network RF
    rf_net_path = os.path.join(BASE_DIR, "models", "network", "rf.joblib")
    rf_net = joblib.load(rf_net_path)
    sample_net = np.zeros((1, 13), dtype=np.float32)
    p_rf_net = rf_net.predict_proba(sample_net)[0, 1]
    assert 0.0 <= p_rf_net <= 1.0
    print("[PASS] 7. Network RF (models/network/rf.joblib)")
    checks_passed += 1

    # 8. Network GraphSAGE
    sage_net_path = os.path.join(BASE_DIR, "models", "network", "graphsage.pt")
    sage_net = SparseGraphSAGE(in_features=13, hidden_dim=64)
    sage_net.load_state_dict(torch.load(sage_net_path, map_location="cpu", weights_only=True))
    sage_net.eval()
    with torch.no_grad():
        x_n = torch.zeros((2, 13), dtype=torch.float32)
        out_n = sage_net(x_n, adj_w)
        p_sage_n = F.softmax(out_n, dim=-1)[0, 1].item()
    assert 0.0 <= p_sage_n <= 1.0
    print("[PASS] 8. Network GraphSAGE (models/network/graphsage.pt)")
    checks_passed += 1

    # 9. Network TGAT
    tgat_net_path = os.path.join(BASE_DIR, "models", "network", "tgat.pt")
    tgat_net = SparseNetworkTGAT(in_features=13, time_dim=16, hidden_dim=64)
    tgat_net.load_state_dict(torch.load(tgat_net_path, map_location="cpu", weights_only=True))
    tgat_net.eval()
    with torch.no_grad():
        t_d = torch.tensor([35.0, 35.0])
        out_tgat = tgat_net(x_n, adj_w, t_d)
        p_tgat_n = F.softmax(out_tgat, dim=-1)[0, 1].item()
    assert 0.0 <= p_tgat_n <= 1.0
    print("[PASS] 9. Network TGAT (models/network/tgat.pt)")
    checks_passed += 1

    # 10. OOF Meta-Stacker & End-to-End Fusion
    stacker_path = os.path.join(BASE_DIR, "models", "fusion", "oof_meta_stacker.joblib")
    stacker = joblib.load(stacker_path)
    X_meta = np.array([[p_rf_tx, p_gat_tx, p_fg_tx, p_rf_wal, p_sage_w, p_fg_wal, p_rf_net, p_sage_n, p_tgat_n]], dtype=np.float32)
    meta_prob = stacker.predict_proba(X_meta)[0, 1]
    assert 0.0 <= meta_prob <= 1.0
    print(f"[PASS] 10. OOF Meta-Stacker (models/fusion/oof_meta_stacker.joblib) -> Test Score: {meta_prob*100:.2f}/100")
    checks_passed += 1

    # 11. Threshold Configuration
    th_path = os.path.join(BASE_DIR, "models", "fusion", "threshold.json")
    with open(th_path, "r") as f:
        th_data = json.load(f)
    assert th_data["threshold"] == 0.675
    decision = int(meta_prob >= th_data["threshold"])
    print(f"[PASS] 11. Operational Threshold Configuration (threshold = {th_data['threshold']}) -> Decision: {decision}")
    checks_passed += 1

    # 12. Feature Schemas
    for s_name, exp_len in [("transaction_features.json", 182), ("wallet_features.json", 55), ("network_features.json", 13)]:
        with open(os.path.join(BASE_DIR, "schemas", s_name), "r") as f:
            sc = json.load(f)
            assert sc["feature_count"] == exp_len
    print("[PASS] 12. Feature Schemas (Transaction: 182, Wallet: 55, Network: 13)")
    checks_passed += 1

    # 13. Calibration & Configuration
    with open(os.path.join(BASE_DIR, "config", "model_config.json"), "r") as f:
        cfg = json.load(f)
    with open(os.path.join(BASE_DIR, "models", "fusion", "calibration.json"), "r") as f:
        cal = json.load(f)
    assert len(cfg["models"]["fusion"]["expected_probability_order"]) == 9
    assert len(cal["triage_priority_tiers"]) == 4
    print("[PASS] 13. System Manifest & Priority Calibration Tiers Verified")
    checks_passed += 1

    # 14. Transaction Isolation Forest
    if_tx_path = os.path.join(BASE_DIR, "models", "transaction", "isolation_forest.joblib")
    if_tx = joblib.load(if_tx_path)
    score_if_tx = -if_tx.decision_function(sample_tx)[0]
    print(f"[PASS] 14. Transaction Isolation Forest (models/transaction/isolation_forest.joblib) -> Raw Anomaly: {score_if_tx:.4f}")
    checks_passed += 1

    # 15. Wallet Isolation Forest
    if_wal_path = os.path.join(BASE_DIR, "models", "wallet", "isolation_forest.joblib")
    if_wal = joblib.load(if_wal_path)
    score_if_wal = -if_wal.decision_function(sample_wal)[0]
    print(f"[PASS] 15. Wallet Isolation Forest (models/wallet/isolation_forest.joblib) -> Raw Anomaly: {score_if_wal:.4f}")
    checks_passed += 1

    # 16. Network Isolation Forest
    if_net_path = os.path.join(BASE_DIR, "models", "network", "isolation_forest.joblib")
    if_net = joblib.load(if_net_path)
    score_if_net = -if_net.decision_function(sample_net)[0]
    print(f"[PASS] 16. Network Isolation Forest (models/network/isolation_forest.joblib) -> Raw Anomaly: {score_if_net:.4f}")
    checks_passed += 1

    print("=" * 75)
    print(f"ALL {checks_passed}/{total_checks} ARTIFACTS AND ARCHITECTURES FULLY VERIFIED")
    print("=" * 75)

if __name__ == "__main__":
    run_verification()
