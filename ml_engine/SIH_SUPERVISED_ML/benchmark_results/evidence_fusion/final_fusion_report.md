# Final Evidence Fusion Benchmark Report (Trained Strictly on Walk-Forward OOF)

Evaluated on untouched Elliptic++ test horizon ($T_{35-49}$, $N=16,670$, $1,083$ labeled illicit).

| Configuration | Num Brains | Val Threshold | Illicit F1 | PR-AUC | Precision | Recall | False Positives | P@100 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Model A: Tx Only (3 brains)** | 3 | 0.62 | **77.48%** | 0.7793 | 87.18% | 69.71% | **111** | **1.00** |
| **Model B: Tx + Wallet (6 brains)** | 6 | 0.62 | **78.91%** | 0.7803 | 89.08% | 70.82% | **94** | **1.00** |
| **Model C: Tx + Network (6 brains)** | 6 | 0.68 | **80.24%** | 0.7794 | 96.62% | 68.61% | **26** | **1.00** |
| **Model D: Full 9-Brain Multi-Domain** | 9 | 0.68 | **80.00%** | 0.7797 | 96.48% | 68.33% | **27** | **1.00** |
