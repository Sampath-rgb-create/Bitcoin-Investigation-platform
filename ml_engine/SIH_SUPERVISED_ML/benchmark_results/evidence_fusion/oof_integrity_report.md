# Genuine Temporal Walk-Forward OOF Integrity Report

All 4 folds retrained base models using only historical data prior to each prediction window.

### Fold Execution Summary

| Fold | Training Horizon | Hold-Out Prediction Window | Total Predicted Txs | Illicit Cases | Identity Leakage Overlap |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | T1-T10 | T11-T15 | 3,046 | 628 | **0 (0.00%)** |
| **2** | T1-T15 | T16-T20 | 3,375 | 619 | **0 (0.00%)** |
| **3** | T1-T20 | T21-T25 | 5,311 | 566 | **0 (0.00%)** |
| **4** | T1-T25 | T26-T30 | 2,705 | 617 | **0 (0.00%)** |

**Total Genuine OOF Training Instances:** 14,437 (2,430 illicit)

### Leakage Invariant Verification
- **Assertion 1 (Temporal Directionality):** Passed. $T_{\text{train, max}} < T_{\text{pred, min}}$ for all 4 folds.
- **Assertion 2 (Disjoint Transaction Identities):** Passed. Zero identity reuse between folds.
- **Assertion 3 (Unique Partitioning):** Passed. Exactly one OOF prediction per transaction ($0$ duplicates).
- **Assertion 4 (Complete Continuous Estimations):** Passed. Zero NaN values across all 9 probability channels.
- **Assertion 5 (Strict Hold-Out Invariance):** Passed. No base model received access to its prediction window during fitting.
