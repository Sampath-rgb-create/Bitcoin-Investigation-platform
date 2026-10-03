# Elliptic++ Case Generator Contract & Forensic Feature Specification
**Project:** AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic (SIH26146)  
**System Target:** `Bitcoin-Investigation-platform`  
**Status:** Canonical Interface Specification & Generator Contract  
**Document Purpose:** Defines the exact contract mapping raw investigator uploads (`transactions.csv`, `inputs.csv`, `outputs.csv`, `network.csv`) to model-ready Elliptic++-compatible case artifacts without artificial temporal leakage and without generating fake class labels.

---

## 1. Core Architectural Principle: Evidence, Not Fake Ground Truth

```text
BENCHMARK EVALUATION MODE (Elliptic++ Ground Truth)
├── txs_features.csv     (182 features + txId + Time step)
├── txs_classes.csv      (GROUND TRUTH LABELS: class 1=illicit, 2=licit, 3=unknown)
└── txs_edgelist.csv     (Money-flow graph topology)

OPERATIONAL INVESTIGATION MODE (Real Investigator Case)
├── transaction/
│   ├── features.parquet      (182 features matching trained model contract)
│   ├── edgelist.parquet      (Reconstructed money-flow graph)
│   └── temporal.parquet      (Case-dependent dynamic snapshot mapping T1..TK)
├── wallet/
│   ├── features.parquet      (55 features matching trained model contract)
│   ├── addr_addr_edgelist.parquet (Derived actor interaction graph)
│   ├── addr_tx_edgelist.parquet   (Input mappings)
│   ├── tx_addr_edgelist.parquet   (Output mappings)
│   └── temporal.parquet      (Wallet activity timeline T1..TK)
├── network/
│   ├── features.parquet      (13 propagation features)
│   ├── edgelist.parquet      (Bipartite peer mesh)
│   └── temporal.parquet      (Continuous timestamps & time deltas)
├── metadata.json             (labels_available: false, entity counts, K snapshots)
└── [NO txs_classes.csv]      (NEVER GUESS LABELS -> Models produce investigation evidence)
```

> [!IMPORTANT]
> **No Fake Classes:**
> In real forensic investigations, transactions are unlabelled ($y = \text{unknown}$). The pipeline must **never** generate a synthetic `txs_classes.csv` or `wallets_classes.csv` with guessed labels.
> Instead, the frozen 9-brain models and Isolation Forest evaluate the generated feature and graph tensors to produce **Investigation Priority Scores (0–100)**, **Severity Tiers**, and **Evidence Packs**.

---

## 2. Generator Goal: Semantic & Structural Compatibility

The generator's goal is **not** to force the investigator's data into the original 203,769-node / 234,355-edge / 49-step dimensions of the Elliptic++ benchmark.

Instead, the goal is:
> **Generate the exact same graph semantics, node/edge types, feature schema, temporal organization, and tensor shapes that the frozen models were trained on — using the investigator's own case data.**

- **$N$ = Case Transaction Count** (Any number of transactions, from 10 to 500,000+).
- **$M$ = Case Wallet Count** (Any number of wallet addresses).
- **$E$ = Case Edge Count** (Reconstructed dynamically from the case's input/output relationships).
- **$K$ = Case Temporal Length** (Calculated dynamically from the case's actual duration, rather than clamped to 49).

---

## 3. The 3 Output Layers of a Generated Case

For every case (e.g. `CASE_001`), the generator produces three distinct layers:

### Layer 1: Features ($X$)
Normalized tabular matrices whose column names, ordering, and data types match the schemas on which the frozen models were trained:
- **Transaction Features ($X_{\text{tx}} \in \mathbb{R}^{N \times 182}$)**:
  Verified directly from `rf.joblib`, `gatv2.pt`, and `fgecgn.pt`. (The raw `txs_features.csv` has 184 columns; `txId` and `Time step` were excluded during training, leaving exactly **182 features**).
- **Wallet Features ($X_{\text{wal}} \in \mathbb{R}^{M \times 55}$)**:
  Verified directly from `actor_rf.joblib`, `graphsage.pt`, and `fgecgn.pt`. (The raw `wallets_features.csv` has 57 columns; `address` and `Time step` were excluded during training, leaving exactly **55 features**).
- **Network Features ($X_{\text{net}} \in \mathbb{R}^{N \times 13}$)**:
  Verified directly from `rf.joblib`, `graphsage.pt`, and `tgat.pt`. (Exactly **13 propagation/topology features**).

### Layer 2: Graphs ($E$)
Directed graph topologies reconstructed from the investigator's actual transaction flows:
- **Transaction Graph ($E_{\text{tx}}$)**: Directed money-flow graph. An edge $T_A \to T_B$ is generated whenever an input of $T_B$ spends an output of $T_A$.
- **Wallet Graphs ($E_{\text{wal}}$)**:
  - `addr_addr_edgelist`: An edge $W_{\text{in}} \to W_{\text{out}}$ is generated whenever an input address sends funds to an output address in the same transaction.
  - `addr_tx_edgelist` & `tx_addr_edgelist`: Bipartite mappings connecting addresses to the transactions they fund or receive from.
- **Network Graph ($E_{\text{net}}$)**: Bipartite peer co-observation mesh connecting originators and transactions.

### Layer 3: Temporal Organization ($T$)
Dynamic temporal representations matching the sequence/time expectations of dynamic models:
- **Discrete Snapshot Mapping ($T_1 \dots T_K$)**:
  - Events are sorted chronologically by timestamp and partitioned into $K$ discrete intervals using a deterministic windowing policy (e.g. 1-hour, 6-hour, or 24-hour windows depending on case span).
  - Used by **FG-EGCN (Transaction & Wallet)** to stream sequential graph slices $(G_1, G_2, \dots, G_K)$ into its recurrent EvolveGCN-H GRU cell.
  - **Recurrent Variable-$K$ Compatibility**: Because EvolveGCN-H updates its internal GRU weights sequentially via `w_t = mat_gru(pooling(x_t), w_prev)`, it naturally processes any arbitrary sequence length $K \ge 1$ without structural mismatch.
- **Continuous Relative Time Encodings ($\Phi(\Delta t)$)**:
  - Used by **Network TGAT** to encode time differences between peer observations via continuous sinusoidal projection functions:
    $$\Phi_d(\Delta t) = \left[ \cos(\omega_1 \Delta t), \sin(\omega_1 \Delta t), \dots, \cos(\omega_d \Delta t), \sin(\omega_d \Delta t) \right]$$

---

## 4. Generator Input Contract: What the Investigator Uploads

The generator expects standard forensic files:

### 4.1 `transactions.csv`
- `txid` (String / Hash): Unique transaction hash.
- `timestamp` (ISO8601 string or Unix epoch): Transaction broadcast/block timestamp.
- `fee` (Float): Transaction fee in BTC.
- `size` (Integer): Transaction byte size.
- `version` (Integer, Optional): Default 1.
- `locktime` (Integer, Optional): Default 0.

### 4.2 `inputs.csv` (or `vin`)
- `txid` (String): Transaction consuming the input.
- `input_index` (Integer): Index of input (0, 1, 2...).
- `prev_txid` (String): Previous transaction hash whose output is spent.
- `prev_vout` (Integer): Output index in previous transaction.
- `address` (String): Funding wallet address.
- `amount` (Float): Value in BTC.

### 4.3 `outputs.csv` (or `vout`)
- `txid` (String): Transaction creating the output.
- `output_index` (Integer): Index of output (0, 1, 2...).
- `address` (String): Recipient wallet address.
- `amount` (Float): Value in BTC.

### 4.4 `network.csv`
- `txid` (String): Associated transaction hash.
- `timestamp` (ISO8601 string or Unix epoch): Observation time.
- `src_ip` (String): Relaying IP address.
- `src_port` (Integer): Port number.
- `dst_ip` (String): Destination/listening IP.
- `dst_port` (Integer): Port number.
- `asn` (String, Optional): Enriched via GeoIP if omitted.
- `country` (String, Optional): Enriched via GeoIP if omitted.

---

## 5. Output Case Package Structure

When an investigator runs a case in `Bitcoin-Investigation-platform`, the generator outputs the package in `data/cases/<case_id>/generated_case/`:

```text
generated_case/
├── transaction/
│   ├── features.parquet      # [N x 182] float32 feature matrix + txid
│   ├── edgelist.parquet      # source_txid -> target_txid
│   └── temporal.parquet      # txid -> timestamp, time_step (T1..TK)
├── wallet/
│   ├── features.parquet      # [M x 55] float32 feature matrix + address
│   ├── addr_addr_edgelist.parquet # input_address -> output_address + weight
│   ├── addr_tx_edgelist.parquet   # address -> txid
│   ├── tx_addr_edgelist.parquet   # txid -> address
│   └── temporal.parquet      # address -> first_seen, last_seen, active_steps
├── network/
│   ├── features.parquet      # [N x 13] float32 feature matrix + txid
│   ├── edgelist.parquet      # originator_id -> txid (bipartite adjacency)
│   └── temporal.parquet      # txid -> continuous timestamps & delta_t
└── metadata.json             # Case metadata
```

### Example `metadata.json`
```json
{
  "case_id": "CASE_2026_001",
  "created_at": "2026-10-03T01:25:00Z",
  "transaction_nodes": 12431,
  "wallet_nodes": 8721,
  "network_nodes": 1294,
  "transaction_edges": 15890,
  "wallet_edges": 24110,
  "temporal_snapshots": 14,
  "time_window_unit": "hours",
  "time_window_step": 12,
  "labels_available": false
}
```

---

## 6. How the 9 Frozen Models Consume the Generated Package

```text
CASE PACKAGE (CASE_001)
│
├── transaction/
│   ├── features (182) ──────────────────────────→ Transaction RF
│   ├── features (182) + edgelist ───────────────→ Transaction GATv2
│   └── features (182) + edgelist + temporal (K) ─→ Transaction FG-EGCN
│
├── wallet/
│   ├── features (55) ───────────────────────────→ Wallet Actor RF
│   ├── features (55) + addr_addr_edgelist ──────→ Wallet GraphSAGE
│   └── features (55) + addr_addr + temporal (K) ─→ Wallet FG-EGCN
│
└── network/
    ├── features (13) ───────────────────────────→ Network RF
    ├── features (13) + edgelist ────────────────→ Network GraphSAGE
    └── features (13) + edgelist + Δt ───────────→ Network TGAT
```

### Downstream Fusion Pipeline:
1. Each of the 9 brains produces an illicit probability $p \in [0, 1]$.
2. The 9 continuous probabilities are passed in exact canonical order:
   `[RF_tx, GATv2_tx, FG_EGCN_tx, RF_wallet, GraphSAGE_wallet, FG_EGCN_wallet, RF_network, GraphSAGE_network, TGAT_network]`
   to the frozen **$L_2$ Temporal Walk-Forward OOF Meta-Stacker** ($C=0.01$, threshold = $0.675$).
3. The resulting **Supervised Probability** is fused with:
   - **Tri-Domain Isolation Forest Anomaly Scores** (unsupervised outlier stream).
   - **Heuristic Behavior Rules** (peeling chains, dust bursts, fan-out dispersion).
   - **Graph Centrality & Community Signals**.
4. The composite **Priority Fusion Scorer** outputs a calibrated **Priority Score (0–100)** and deterministic **Evidence Pack** for the investigator dashboard.

---

## 7. Mathematical Derivation of Features

### 7.1 Transaction Features (182 Features)
- **17 Augmented Quantities**:
  - In/out degree: count of ancestor/descendant transactions.
  - Value flows: `total_BTC`, `fees`, `size`.
  - Address counts: `num_input_addresses`, `num_output_addresses`.
  - Statistics: `in_BTC_*` (min, max, mean, median, total) and `out_BTC_*` (min, max, mean, median, total).
- **93 Local Features (`Local_feature_1` to `Local_feature_93`)**:
  - Intrinsic transaction attributes: fee-per-byte, input-to-output ratios, output value dispersion, Shannon entropy $H = -\sum p_j \log_2(p_j)$, and script type encodings.
- **72 Aggregate Features (`Aggregate_feature_1` to `Aggregate_feature_72`)**:
  - 1-hop forward/backward neighborhood statistics: min, max, mean, std, median of transaction values, fees, and degrees across $\mathcal{N}_{\text{in}}(T)$ and $\mathcal{N}_{\text{out}}(T)$.

### 7.2 Wallet Features (55 Features)
- **Interaction & Degree (6)**: `num_txs_as_sender`, `num_txs_as receiver`, `total_txs`, `num_timesteps_appeared_in`, `num_addr_transacted_multiple`, `transacted_w_address_total`.
- **Block Appearance & Lifetime (6)**: `first_block_appeared_in`, `last_block_appeared_in`, `lifetime_in_blocks`, `first_sent_block`, `first_received_block`, `blocks_btwn_txs_total`.
- **BTC Flow Statistics (15)**: `btc_transacted_*`, `btc_sent_*`, `btc_received_*` (total, min, max, mean, median).
- **Fees (10)**: `fees_*` and `fees_as_share_*` (total, min, max, mean, median).
- **Temporal Intervals (15)**: `blocks_btwn_txs_*`, `blocks_btwn_input_txs_*`, `blocks_btwn_output_txs_*`.
- **Counterparty Distributions (3)**: `transacted_w_address_*` (min, max, mean, median).

### 7.3 Network Features (13 Features)
- `num_inputs`, `unique_inputs`, `num_outputs`, `unique_outputs`, `total_degree`, `in_out_ratio`, `net_flow_direction`
- `is_aggregation_pattern`, `is_peeling_chain_pattern`, `is_fan_out_dispersion`
- `input_concentration`, `output_concentration`, `bipartite_entropy`

---

## 8. Role of Neo4j & Graph Data Science (GDS): Decoupled Architecture

Neo4j is an **investigation and relationship-engineering layer**, **not** a mandatory runtime dependency for feeding the 9 frozen ML models:

```text
ML INFERENCE PATH (Fast, High-Availability, Independent)
Parquet Files ───> PyTorch / Scikit-Learn ───> 9 Brains + 3 IF ───> L2 Meta-Stacker

INVESTIGATION & RELATIONSHIP PATH (Visual, Multi-Hop, Contextual)
Parquet Files ───> Neo4j Database ───> Neo4j GDS (85 features) ───> Multi-Hop Cypher UI
```

### Architectural Contract:
1. **ML Independence:**
   - Transaction RF/GATv2/FG-EGCN, Wallet RF/GraphSAGE/FG-EGCN, and Network RF/GraphSAGE/TGAT receive their tensors ($X, E, T$) directly from Parquet files via Python/PyG memory tensors.
   - If Neo4j is offline or restarting, ML inference and threat scoring proceed without interruption.
2. **Neo4j's Dedicated Purpose:**
   - **Multi-Hop Traversal:** Instant interactive Cypher queries for investigators (e.g. 2-to-5 hop money traces, co-spending rings, mixer paths).
   - **85 Investigation Features:** Computed by Neo4j GDS (PageRank, Betweenness, Weakly Connected Components, Leiden community detection, K-core decomposition) to feed **heuristic rules, evidence packs, and forensic dashboard explanations**.
   - **Evidence Fusion:** The Priority Fusion Scorer blends ML probabilities ($P(\text{illicit})$), Isolation Forest outlier percentiles, and Neo4j GDS structural metrics to deliver comprehensive case priority scores.
