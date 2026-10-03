# Elliptic++ & Forensic Feature Catalog: Mathematical Formulations & Definitions

This catalog provides the complete, authoritative reference for all **335 features** across the Tri-Domain Supervised ML models and the Graph Investigation Engine in the **Bitcoin Investigation Platform**, based on the official Elliptic++ methodology and forensic graph analytics.

---

## Table of Contents
1. [Overview & Taxonomy](#1-overview--taxonomy)
2. [Transaction Domain Features (182 Features)](#2-transaction-domain-features-182-features)
   - [Basic Graph & Flow Features (17)](#21-basic-graph--flow-features-17-features)
   - [Local Intrinsic Features (LF_1 - LF_93)](#22-local-intrinsic-features-93-features)
   - [Aggregate Neighborhood Features (AF_1 - AF_72)](#23-aggregate-neighborhood-features-72-features)
3. [Wallet / Address Domain Features (55 Features)](#3-wallet--address-domain-features-55-features)
   - [Interaction & Degree (6)](#31-interaction--degree-6-features)
   - [Block Appearance & Lifetime (6)](#32-block-appearance--lifetime-6-features)
   - [Bitcoin Flow Volumes (15)](#33-bitcoin-flow-volumes-15-features)
   - [Transaction Fees & Fee Shares (10)](#34-transaction-fees--fee-shares-10-features)
   - [Temporal Block Intervals (15)](#35-temporal-block-intervals-15-features)
   - [Counterparty Diversity (3)](#36-counterparty-diversity-3-features)
4. [Network & Bipartite Telemetry Features (13 Features)](#4-network--bipartite-telemetry-features-13-features)
5. [Graph Investigation & Centrality Features (85 Features)](#5-graph-investigation--centrality-features-85-features)
   - [Centrality & Flow Prominence](#51-centrality--flow-prominence)
   - [Component & Subgraph Structure](#52-component--subgraph-structure)
   - [Forensic Typologies & Dispersion](#53-forensic-typologies--dispersion)
   - [Originator & P2P Telemetry Correlates](#54-originator--p2p-telemetry-correlates)

---

## 1. Overview & Taxonomy

| Domain | Count | Mathematical Basis | ML / Analytical Consumer |
|:---|:---:|:---|:---|
| **Transaction** | **182** | UTXO graph topology, in/out degrees, Shannon entropy, neighbor stats | Random Forest, GATv2, FG-EGCN, Isolation Forest |
| **Wallet (Actor)** | **55** | Address activity, lifetime blocks, BTC volumes, fees, gap intervals | Actor Random Forest, GraphSAGE, FG-EGCN, Isolation Forest |
| **Network** | **13** | Bipartite projection, Gini concentration, peeling/fan-out flags | Network Random Forest, GraphSAGE, TGAT, Isolation Forest |
| **Graph Investigation** | **85** | PageRank, Betweenness, WCC, K-core, Triangles, Dispersion | Neo4j GDS, NetworkX, Evidence Fusion, Rule Engine |
| **Total** | **335** | Complete multi-domain forensic feature matrix | 9-Brain Stacker, Dynamic Rules Engine |

---

## 2. Transaction Domain Features (182 Features)

In the official Elliptic and Elliptic++ frameworks, a transaction $t \in V_{tx}$ represents a Bitcoin transaction vertex with directed edges representing money flow from inputs to outputs.

### 2.1 Basic Graph & Flow Features (17 Features)

1. **`in_txs_degree`**:
   $$\text{deg}_{in}(t) = |\{ t_{prev} \mid (t_{prev}, t) \in E_{tx} \}|$$
   The number of immediate predecessor transactions whose outputs are spent by transaction $t$.
2. **`out_txs_degree`**:
   $$\text{deg}_{out}(t) = |\{ t_{succ} \mid (t, t_{succ}) \in E_{tx} \}|$$
   The number of immediate successor transactions spending outputs of $t$.
3. **`total_BTC`**:
   $$\text{Total\_BTC}(t) = \max \left( \sum_{i \in \text{Inputs}(t)} \text{amt}_i, \; \sum_{o \in \text{Outputs}(t)} \text{amt}_o + \text{fee}(t) \right)$$
   Total volume of Bitcoin transacted.
4. **`fees`**:
   $$\text{fee}(t) = \sum_{i \in \text{Inputs}(t)} \text{amt}_i - \sum_{o \in \text{Outputs}(t)} \text{amt}_o$$
   Mining fee paid in satoshis / BTC.
5. **`size`**:
   Byte length / virtual size (vBytes) of the serialized transaction.
6. **`num_input_addresses`**:
   $$|\{ \text{addr}(i) \mid i \in \text{Inputs}(t) \}|$$
   Count of distinct sender addresses participating in the transaction.
7. **`num_output_addresses`**:
   $$|\{ \text{addr}(o) \mid o \in \text{Outputs}(t) \}|$$
   Count of distinct recipient addresses.
8. **`in_BTC_min`**: $\min_{i \in \text{Inputs}(t)} \text{amt}_i$ (Minimum input value).
9. **`in_BTC_max`**: $\max_{i \in \text{Inputs}(t)} \text{amt}_i$ (Maximum input value).
10. **`in_BTC_mean`**: $\frac{1}{|\text{Inputs}(t)|} \sum_{i \in \text{Inputs}(t)} \text{amt}_i$ (Average input value).
11. **`in_BTC_median`**: $\text{Median}(\{ \text{amt}_i \mid i \in \text{Inputs}(t) \})$ (Median input value).
12. **`in_BTC_total`**: $\sum_{i \in \text{Inputs}(t)} \text{amt}_i$ (Sum of input values).
13. **`out_BTC_min`**: $\min_{o \in \text{Outputs}(t)} \text{amt}_o$ (Minimum output value).
14. **`out_BTC_max`**: $\max_{o \in \text{Outputs}(t)} \text{amt}_o$ (Maximum output value).
15. **`out_BTC_mean`**: $\frac{1}{|\text{Outputs}(t)|} \sum_{o \in \text{Outputs}(t)} \text{amt}_o$ (Average output value).
16. **`out_BTC_median`**: $\text{Median}(\{ \text{amt}_o \mid o \in \text{Outputs}(t) \})$ (Median output value).
17. **`out_BTC_total`**: $\sum_{o \in \text{Outputs}(t)} \text{amt}_o$ (Sum of output values).

---

### 2.2 Local Intrinsic Features (93 Features: `Local_feature_1` to `Local_feature_93`)

These represent intrinsic transaction properties computed without 1-hop aggregate graph traversal:
- **`Local_feature_1` (Fee-per-Byte / Feerate)**:
  $$\text{Feerate}(t) = \frac{\text{fee}(t)}{\text{size}(t)}$$
- **`Local_feature_2` (Output Shannon Entropy)**:
  $$H_{out}(t) = -\sum_{o \in \text{Outputs}(t)} p_o \log_2(p_o), \quad \text{where } p_o = \frac{\text{amt}_o}{\sum \text{amt}}$$
  Measures the dispersal distribution of output values (peeling chains have low entropy; mixing pools have high entropy).
- **`Local_feature_3` (Input Shannon Entropy)**:
  $$H_{in}(t) = -\sum_{i \in \text{Inputs}(t)} p_i \log_2(p_i), \quad \text{where } p_i = \frac{\text{amt}_i}{\sum \text{amt}}$$
- **`Local_feature_4` (Input-to-Output Count Ratio)**:
  $$\text{Ratio}_{in/out}(t) = \frac{|\text{Inputs}(t)|}{\max(1, |\text{Outputs}(t)|)}$$
- **`Local_feature_5` to `Local_feature_93`**:
  Standardized Elliptic++ local dimensions representing script type encodings (P2PKH, P2SH, SegWit, Multi-Sig), locktime parameters, sequence numbers, and statistical moment ratios (skewness, kurtosis, variance of amounts).

---

### 2.3 Aggregate Neighborhood Features (72 Features: `Aggregate_feature_1` to `Aggregate_feature_72`)

These features capture contextual 1-hop backward (predecessors) and forward (successors) topological properties:
- **Predecessor Statistics (Inputs)**:
  $$\mu_{pred}(t) = \frac{1}{|Pred(t)|} \sum_{p \in Pred(t)} \text{metric}(p)$$
  Computed for min, max, mean, standard deviation, and median across predecessor degrees, fees, and BTC amounts.
- **Successor Statistics (Outputs)**:
  $$\mu_{succ}(t) = \frac{1}{|Succ(t)|} \sum_{s \in Succ(t)} \text{metric}(s)$$
  Computed for min, max, mean, standard deviation, and median across successor degrees, fees, and BTC amounts.

---

## 3. Wallet / Address Domain Features (55 Features)

In Bitcoin forensics, addresses represent actor nodes $a \in V_{wal}$.

### 3.1 Interaction & Degree (6 Features)
1. **`num_txs_as_sender`**: Total number of transactions where $a$ appeared as an input address.
2. **`num_txs_as receiver`**: Total number of transactions where $a$ appeared as an output address.
3. **`total_txs`**: $\text{num\_txs\_as\_sender} + \text{num\_txs\_as\_receiver}$.
4. **`num_timesteps_appeared_in`**: Count of distinct temporal snapshots in which $a$ executed transfers.
5. **`num_addr_transacted_multiple`**: Number of counterparties with whom $a$ transacted $\ge 2$ times.
6. **`transacted_w_address_total`**: Total number of unique counterparty addresses directly linked to $a$.

### 3.2 Block Appearance & Lifetime (6 Features)
7. **`first_block_appeared_in`**: Lowest block height containing a transaction involving $a$.
8. **`last_block_appeared_in`**: Highest block height containing a transaction involving $a$.
9. **`lifetime_in_blocks`**: $\text{last\_block\_appeared\_in} - \text{first\_block\_appeared\_in} + 1$.
10. **`first_sent_block`**: Block height of the first outgoing transfer sent by $a$.
11. **`first_received_block`**: Block height of the first incoming transfer received by $a$.
12. **`blocks_btwn_txs_total`**: Cumulative sum of block gaps between all consecutive transactions of $a$.

### 3.3 Bitcoin Flow Volumes (15 Features)
- **Transacted Volume**: `btc_transacted_total`, `btc_transacted_min`, `btc_transacted_max`, `btc_transacted_mean`, `btc_transacted_median`.
- **Sent Volume**: `btc_sent_total`, `btc_sent_min`, `btc_sent_max`, `btc_sent_mean`, `btc_sent_median`.
- **Received Volume**: `btc_received_total`, `btc_received_min`, `btc_received_max`, `btc_received_mean`, `btc_received_median`.

### 3.4 Transaction Fees & Fee Shares (10 Features)
- **Absolute Fees Paid**: `fees_total`, `fees_min`, `fees_max`, `fees_mean`, `fees_median`.
- **Fee Share Relative to Transfer Volume**:
  $$\text{Fee\_Share}(t) = \frac{\text{fee}(t)}{\text{total\_volume}(t)}$$
  Summary metrics: `fees_as_share_total`, `fees_as_share_min`, `fees_as_share_max`, `fees_as_share_mean`, `fees_as_share_median`.

### 3.5 Temporal Block Intervals (15 Features)
- **Gaps Between Any Transactions**: `blocks_btwn_txs_min`, `blocks_btwn_txs_max`, `blocks_btwn_txs_mean`, `blocks_btwn_txs_median`.
- **Gaps Between Input (Sending) Transactions**: `blocks_btwn_input_txs_total`, `blocks_btwn_input_txs_min`, `blocks_btwn_input_txs_max`, `blocks_btwn_input_txs_mean`, `blocks_btwn_input_txs_median`.
- **Gaps Between Output (Receiving) Transactions**: `blocks_btwn_output_txs_total`, `blocks_btwn_output_txs_min`, `blocks_btwn_output_txs_max`, `blocks_btwn_output_txs_mean`, `blocks_btwn_output_txs_median`.

### 3.6 Counterparty Diversity (3 Features)
- `transacted_w_address_min`, `transacted_w_address_max`, `transacted_w_address_mean`, `transacted_w_address_median`.

---

## 4. Network & Bipartite Telemetry Features (13 Features)

Derived from correlated P2P network telemetry and bipartite bipartite transaction projections:
1. **`num_inputs`**: Total inputs in the transaction ($N_{in}$).
2. **`unique_inputs`**: Count of distinct input addresses ($U_{in}$).
3. **`num_outputs`**: Total outputs in the transaction ($N_{out}$).
4. **`unique_outputs`**: Count of distinct output addresses ($U_{out}$).
5. **`total_degree`**: $N_{in} + N_{out}$.
6. **`in_out_ratio`**: $\frac{N_{in}}{\max(1, N_{out})}$.
7. **`net_flow_direction`**: $\frac{N_{out} - N_{in}}{N_{out} + N_{in}} \in [-1, 1]$ (Negative = Aggregation; Positive = Dispersal).
8. **`is_aggregation_pattern`**: Binary flag indicating consolidation ($N_{in} \ge 5$ and $N_{out} \le 2$).
9. **`is_peeling_chain_pattern`**: Binary flag indicating peeling structure ($N_{in} = 1$ and $N_{out} = 2$).
10. **`is_fan_out_dispersion`**: Binary flag indicating extreme dispersal ($N_{in} = 1$ and $N_{out} \ge 10$).
11. **`input_concentration`**: Gini concentration of input values: $\frac{\max(in\_amounts)}{\sum in\_amounts}$.
12. **`output_concentration`**: Gini concentration of output values: $\frac{\max(out\_amounts)}{\sum out\_amounts}$.
13. **`bipartite_entropy`**: Total bipartite Shannon entropy of combined funds.

---

## 5. Graph Investigation & Centrality Features (85 Features)

Extracted via Neo4j GDS / NetworkX for forensic audit and scoring:

### 5.1 Centrality & Flow Prominence
- **`pagerank`**:
  $$PR(u) = \frac{1 - d}{N} + d \sum_{v \in Pred(u)} \frac{PR(v)}{OutDegree(v)}, \quad d = 0.85$$
  Ranks systemic fund concentration and transit hubs.
- **`betweenness`**:
  $$C_B(u) = \sum_{s \neq u \neq t} \frac{\sigma_{st}(u)}{\sigma_{st}}$$
  Quantifies bridge and laundering conduit nodes between clusters.
- **`articlerank`**: PageRank variant normalized by average network degree.
- **`closeness_centrality`**: Reciprocal of average shortest-path distance to all reachable nodes.
- **`eigenvector_centrality`**: Influence score measuring connections to other influential entities.

### 5.2 Component & Subgraph Structure
- **`wcc_component_id` & `wcc_component_size`**: Identifier and node count of the Weakly Connected Component.
- **`k_core_number`**: Maximal subgraph where every node has degree $\ge k$.
- **`triangle_count`**: Number of closed directed/undirected triangles involving the node (indicates circular fund recycling).
- **`clustering_coefficient`**:
  $$C(u) = \frac{2 \cdot \text{Triangles}(u)}{\text{deg}(u)(\text{deg}(u) - 1)}$$

### 5.3 Forensic Typologies & Dispersion
- **`dispersion_ratio`**: Ratio of unique downstream counterparties to total outward transfers.
- **`peeling_chain_depth`**: Length of consecutive 1-in-2-out transactions originating from this entity.
- **`burst_event_count`**: Number of transactions executed within a 30-second window.
- **`inter_arrival_time_min`, `_max`, `_mean`, `_median`, `_std`**: Time-gap statistical moments between successive transfers.
- **`short_cycle_3_count` & `short_cycle_4_count`**: Number of circular fund paths returning to the source in 3 or 4 hops.

### 5.4 Originator & P2P Telemetry Correlates
- **`originator_peer_count`**: Number of distinct P2P relay nodes broadcasting this transaction.
- **`originator_country_diversity`**: Count of distinct countries where broadcasts were captured.
- **`originator_asn_diversity`**: Count of distinct Autonomous System Numbers (ASNs) relaying the transaction.
- **`originator_tor_or_vpn_flag`**: Boolean flag indicating broadcast originated from known exit nodes or proxy IP ranges.
- **`originator_relay_burst_score`**: Concentration of relays occurring within $< 500\text{ms}$ of first sight.

---

## 6. Verification and Cryptographic Order Integrity

All 335 features conform to the frozen schemas in `features/schemas/` verified by SHA-256 order hashes:
- `transaction_features.json` (182 features): `d25f2f8e7eb7faee...`
- `wallet_features.json` (55 features): `e135dce14b253ce9...`
- `network_features.json` (13 features): `824e58b592ca73f0...`
- `graph_features.json` (85 features): `3f81e8093498bc19...`
