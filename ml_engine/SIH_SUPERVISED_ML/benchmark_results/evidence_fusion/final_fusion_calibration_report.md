# Final Multi-Brain Calibration & Operational Triage Report

Evaluated on untouched test horizon ($T_{35-49}$, $N=16,670$, $1,083$ labeled illicit).
- **Brier Score:** `0.0555`
- **Expected Calibration Error (ECE):** `0.2085`

### Operational Priority Tiers

| Priority Tier | Priority Score Range | Transactions Count | Percentage | Empirical Test-Set Labeled-Class Rate | Recommended Action |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Tier 1: Immediate Triage** | 85.0 - 100.0 | 632 | 3.79% | **99.68%** | Immediate analyst review; inspect associated network observations and graph neighborhood. |
| **Tier 2: Elevated Priority** | 60.0 - 84.9 | 232 | 1.39% | **61.21%** | Secondary analyst queue; expand 2-hop counterparty transaction cluster. |
| **Tier 3: Routine Review** | 30.0 - 59.9 | 2,853 | 17.11% | **3.15%** | Passive monitoring; log for batch temporal reconciliation. |
| **Tier 4: Low Model Priority** | 0.0 - 29.9 | 12,953 | 77.70% | **1.71%** | Low model priority; no elevated review signal under current model. |
