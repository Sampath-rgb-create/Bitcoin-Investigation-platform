# SIH Supervised ML Portable Package

This standalone package contains the complete, frozen supervised multi-brain architecture for Bitcoin illicit entity and transaction detection on Elliptic++.

All 9 base models, the genuine temporal Out-Of-Fold (OOF) $L_2$ meta-stacker, architecture code, preprocessing utilities, schemas, and benchmark records are bundled together for transfer and deployment on any laptop or server without retraining.

---

## 1. Directory Structure

```text
SIH_SUPERVISED_ML/
├── models/
│   ├── transaction/
│   │   ├── rf.joblib
│   │   ├── gatv2.pt
│   │   ├── fgecgn.pt
│   │   └── isolation_forest.joblib
│   ├── wallet/
│   │   ├── actor_rf.joblib
│   │   ├── graphsage.pt
│   │   ├── fgecgn.pt
│   │   └── isolation_forest.joblib
│   ├── network/
│   │   ├── rf.joblib
│   │   ├── graphsage.pt
│   │   ├── tgat.pt
│   │   └── isolation_forest.joblib
│   └── fusion/
│       ├── oof_meta_stacker.joblib
│       ├── threshold.json
│       └── calibration.json
├── architectures/
│   ├── gatv2_model.py
│   ├── fgecgn_model.py
│   ├── graphsage_model.py
│   └── tgat_model.py
├── preprocessing/
│   ├── transaction_preprocessing.py
│   ├── wallet_preprocessing.py
│   └── network_preprocessing.py
├── schemas/
│   ├── transaction_features.json
│   ├── wallet_features.json
│   └── network_features.json
├── config/
│   └── model_config.json
├── benchmark_results/
│   ├── nine_brains/
│   │   └── nine_brain_registry.csv
│   ├── evidence_fusion/
│   │   ├── final_fusion_report.md
│   │   ├── oof_integrity_report.md
│   │   ├── final_fusion_calibration_report.md
│   │   └── oof_meta_train.parquet
│   └── ablation_diagnostics/
│       └── final_domain_ablation_results.csv
├── test_horizons_predictions/
│   ├── calibrated_investigation_scoring_oof.csv
│   ├── oof_predictions_val.parquet
│   └── oof_predictions_test.parquet
├── requirements.txt
├── README.md
└── verify_models.py
```

---

## 2. Quickstart & Verification on a New Laptop

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Verify Models and End-to-End Inference
```bash
python verify_models.py
```
Expected output:
```text
===========================================================================
VERIFYING PORTABLE SIH SUPERVISED ML MODEL PACKAGE
===========================================================================
[PASS] 1. Transaction RF (models/transaction/rf.joblib)
[PASS] 2. Transaction GATv2 (models/transaction/gatv2.pt)
[PASS] 3. Transaction FG-EGCN (models/transaction/fgecgn.pt)
[PASS] 4. Wallet Actor RF (models/wallet/actor_rf.joblib)
[PASS] 5. Wallet GraphSAGE (models/wallet/graphsage.pt)
[PASS] 6. Wallet FG-EGCN (models/wallet/fgecgn.pt)
[PASS] 7. Network RF (models/network/rf.joblib)
[PASS] 8. Network GraphSAGE (models/network/graphsage.pt)
[PASS] 9. Network TGAT (models/network/tgat.pt)
[PASS] 10. OOF Meta-Stacker (models/fusion/oof_meta_stacker.joblib)
[PASS] 11. Operational Threshold Configuration (threshold = 0.675)
[PASS] 12. Feature Schemas (Transaction: 182, Wallet: 55, Network: 13)
[PASS] 13. System Manifest & Priority Calibration Tiers Verified
[PASS] 14. Transaction Isolation Forest (models/transaction/isolation_forest.joblib)
[PASS] 15. Wallet Isolation Forest (models/wallet/isolation_forest.joblib)
[PASS] 16. Network Isolation Forest (models/network/isolation_forest.joblib)
===========================================================================
ALL 16/16 ARTIFACTS AND ARCHITECTURES FULLY VERIFIED
===========================================================================
```

---

## 3. How to Perform Inference

```python
import os, json, joblib, torch
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Load Meta-Stacker and Threshold
stacker = joblib.load(os.path.join(BASE_DIR, "models", "fusion", "oof_meta_stacker.joblib"))
with open(os.path.join(BASE_DIR, "models", "fusion", "threshold.json"), "r") as f:
    th = json.load(f)["threshold"]  # 0.675

# 2. Gather Predictions in the exact trained channel order:
# [RF_tx, GATv2_tx, FG_EGCN_tx, RF_wallet, GraphSAGE_wallet, FG_EGCN_wallet, RF_network, GraphSAGE_network, TGAT_network]
X_meta = np.array([[p_rf_tx, p_gat_tx, p_fg_tx, p_rf_wal, p_sage_wal, p_fg_wal, p_rf_net, p_sage_net, p_tgat_net]])

# 3. Output Calibrated Risk Score [0, 100] and Decision
risk_score = stacker.predict_proba(X_meta)[0, 1] * 100.0
is_illicit = int(risk_score >= (th * 100.0))
```

---

## 4. Benchmark Summary (Untouched Test Horizon $T_{35\text{--}49}$)

- **Full 9-Brain Multi-Domain Stacker:**
  - $F_1$: **$80.00\%$**
  - PR-AUC: **$0.7797$**
  - Precision: **$96.48\%$**
  - Recall: **$68.33\%$**
  - False Positives: **$27$** ($75.68\%$ reduction in false alerts vs. Transaction only)
  - Precision@100: **$1.0000$** ($100\%$ precision on top-100 highest priority alerts)
  - Brier Score: **$0.0555$**
