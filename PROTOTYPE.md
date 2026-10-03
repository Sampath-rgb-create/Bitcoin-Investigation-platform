# Bitcoin Investigation Platform — New Prototype Implementation Plan

> **Purpose:** Implementation contract for migrating the existing prototype into the new investigation-oriented prototype.
>
> **Audience:** AI coding agent, project team, reviewers, and future maintainers.
>
> **Status:** Implementation planning / migration specification.
>
> **Core principle:** Preserve the exact input contracts of validated trained models. Do not silently change feature order, dimensions, preprocessing, graph semantics, or temporal handling.

---

## 1. Project Overview

The new prototype upgrades the existing Bitcoin investigation prototype from a single Isolation Forest anomaly detector into a multi-domain investigation platform.

The system will ingest investigator-provided Bitcoin transaction, wallet, and network data; validate and normalize it; generate model-compatible representations; construct investigation graphs; execute trained machine-learning models; perform anomaly and graph analysis; combine evidence; and present prioritized investigation leads.

The system is **not intended to prove criminal activity**. Outputs represent model, anomaly, graph, temporal, and rule-based evidence for investigation.

Preferred terminology:

- investigation lead
- anomalous behavior
- elevated model score
- structural evidence
- temporal evidence
- behavior consistent with a pattern
- investigation priority

Avoid automatically declaring an entity criminal or illicit based only on model output.

### Migration objective

```text
OLD PROTOTYPE
    |
    | Single Isolation Forest
    | Limited feature pipeline
    | Limited investigation capability
    v
NEW PROTOTYPE
    |
    +-- Elliptic++-compatible case generation
    +-- Transaction models
    +-- Wallet models
    +-- Network models
    +-- Isolation Forest
    +-- Neo4j graph database
    +-- Neo4j GDS
    +-- Graph/temporal investigation features
    +-- Evidence fusion
    +-- Investigation priority
    +-- Explainable output
```

---

## 2. Scope

### 2.1 In scope

1. Investigator input ingestion
2. Input validation
3. Canonicalization
4. Elliptic++-compatible feature generation
5. Transaction graph generation
6. Wallet/address graph generation
7. Network graph generation
8. Temporal representation
9. Existing trained transaction models
10. Existing trained wallet models
11. Existing trained network models
12. Isolation Forest
13. Neo4j
14. Neo4j GDS
15. Graph-derived investigation features
16. Evidence fusion
17. Investigation priority scoring
18. Explainable investigation results
19. Logging and validation
20. Runtime error handling
21. Regression testing

### 2.2 Out of scope for the first prototype

- Automatic real-world identity attribution
- Recovery/deanonymization of blinded identifiers
- Automatic legal conclusions
- Automatic asset freezing or enforcement actions
- Generating fake ground-truth labels for investigator cases
- Copying the original Elliptic++ graph into a new case
- Retraining the nine frozen models during an investigation
- Feeding all 85 graph features into frozen models without retraining

---

## 3. Old Prototype Summary

### 3.1 Existing architecture

```text
Input
  |
  v
Preprocessing
  |
  v
Feature extraction
  |
  v
Isolation Forest
  |
  v
Anomaly score
```

### 3.2 Existing algorithm

**Isolation Forest**

Purpose:

- unsupervised anomaly detection;
- identify observations that are unusual relative to the training distribution;
- does not require ground-truth labels during fitting.

**Status: KEEP AS BASELINE**

The old implementation should remain runnable until the new pipeline passes regression tests.

### 3.3 Old prototype limitations

- One model only
- No transaction/wallet/network specialization
- No supervised multi-model evidence
- No persistent investigation graph
- No Neo4j/GDS analysis
- Limited graph/temporal investigation features
- Limited explainability
- No formal investigator-case generation contract
- Limited separation between benchmark/training data and investigator-case data
- Limited runtime observability and validation

---

## 4. New Prototype Architecture

### 4.1 High-level architecture

```text
                    INVESTIGATOR
                         |
                         v
                +------------------+
                | Input Files      |
                | CSV / JSON / XML |
                +--------+---------+
                         |
                         v
                +------------------+
                | Input Validation |
                +--------+---------+
                         |
                         v
                +------------------+
                | Canonicalization |
                +--------+---------+
                         |
                         v
             +---------------------------+
             | Elliptic++ Case Generator |
             +------------+--------------+
                          |
          +---------------+---------------+
          |               |               |
          v               v               v
    Transaction        Wallet          Network
      package          package          package
          |               |               |
          +---------------+---------------+
                          |
              +-----------+-----------+
              |                       |
              v                       v
       ML Model Pipeline        Neo4j Graph
              |                       |
              |                       v
              |                  Neo4j GDS
              |                       |
              |                       v
              |                Graph Features
              |                       |
              +-----------+-----------+
                          |
                          v
                 Evidence Fusion
                          |
                          v
             Investigation Priority
                          |
                          v
                Investigator UI
```

---

## 5. New Technologies

| Technology | Role |
|---|---|
| Python | Orchestration and feature generation |
| Pandas/Polars | Tabular processing |
| PyArrow/Parquet | Feature and edge storage |
| scikit-learn | Random Forest / Isolation Forest / preprocessing |
| PyTorch | GNN and temporal model inference |
| Neo4j | Persistent investigation graph database |
| Neo4j GDS | Graph algorithms and graph-derived features |
| Cypher | Graph querying |
| graphdatascience | Python-to-GDS integration |
| Pydantic | Validation/configuration where appropriate |
| pytest | Automated tests |
| Python logging | Runtime observability |
| [TODO] Dashboard framework | Investigation UI |
| [TODO] API framework | Backend API if required |

Neo4j GDS documents the workflow of reading graph data from Neo4j, creating an in-memory graph projection, running algorithms, and writing or streaming results back to the graph/application. The Python client supports Python-oriented graph projection and algorithm workflows.

---

## 6. Algorithm Inventory

### 6.1 Old prototype

| Algorithm | Role | Status |
|---|---|---|
| Isolation Forest | Unsupervised anomaly detection | Kept as baseline |

### 6.2 New supervised models

#### Transaction

| Slot | Algorithm | Input |
|---|---|---|
| Analysis | Random Forest | Exact trained transaction feature matrix |
| Graph | GATv2 | Exact trained transaction features + TX→TX graph |
| Temporal | FG-EGCN | Exact trained transaction features + TX→TX graph + temporal representation |

#### Wallet

| Slot | Algorithm | Input |
|---|---|---|
| Analysis | Actor Random Forest | Exact trained wallet feature matrix |
| Graph | GraphSAGE | Exact trained wallet features + wallet graph |
| Temporal | FG-EGCN | Exact trained wallet features + wallet graph + temporal representation |

#### Network

| Slot | Algorithm | Input |
|---|---|---|
| Analysis | Network Random Forest | Exact trained network feature matrix |
| Graph | GraphSAGE | Exact trained network features + network graph |
| Temporal | TGAT | Exact trained network features + temporal graph/events |

### 6.3 New unsupervised models

Use separate Isolation Forest models for:

- Transaction
- Wallet
- Network

Initial IF contract:

```text
Transaction IF → exact transaction model feature matrix
Wallet IF      → exact wallet model feature matrix
Network IF     → exact network model feature matrix
```

Do not use investigator ground-truth labels for fitting.

### 6.4 Graph algorithms

Candidate algorithms:

- Degree
- Weighted Degree
- PageRank
- Betweenness Centrality
- Weakly Connected Components
- Leiden
- Louvain
- K-Core
- Triangle Count
- [TODO: verify against SIH_GRAPH_FEATURE_SPECIFICATION.md]

Use graph algorithms to create structural evidence, not as automatic proof of illicit behavior.

---

## 7. Feature Architecture

### 7.1 Three feature categories

#### A. Frozen model features

These are the exact feature vectors used when the current models were trained.

**Important:** The public Elliptic++ repository reports 183 transaction features and 56 actor/wallet features. Your current project contract mentions 182 and 55 dimensions. This discrepancy MUST be resolved by inspecting the actual training pipeline and saved model interfaces before implementation.

Do not guess the excluded column.

#### B. Graph/temporal investigation features

The planned ~85 features include:

- transaction topology
- wallet topology
- network topology
- cross-domain relationships
- temporal behavior

These are primarily for:

- investigation evidence
- anomaly detection experiments
- dashboard explanations
- graph exploration
- future retrained model versions

#### C. Raw graph structure

Graph edges are not the same thing as hand-crafted graph metrics.

Example:

```text
TX-A → TX-B → TX-C
```

is graph structure.

```text
TX-B degree = 4
TX-B PageRank = 0.02
TX-B community size = 183
```

are derived graph features.

---

## 8. Feature Comparison

| Feature/Capability | Old Prototype | New Prototype | Status |
|---|---|---|---|
| Existing anomaly features | Yes | Yes | Kept |
| Single Isolation Forest | Yes | Yes + domain-specific IF | Expanded |
| Transaction features | Limited/old schema | Model-compatible TX schema | Added/standardized |
| Wallet features | No/limited | Model-compatible wallet schema | Added |
| Network features | No/limited | Model-compatible network schema | Added |
| Transaction graph | No/limited | TX→TX money-flow graph | Added |
| Wallet graph | No/limited | Address graph + address/transaction relations | Added |
| Network graph | No/limited | Network/originator graph | Added |
| Temporal representation | Limited | Explicit case temporal engine | Added |
| Graph algorithms | No/limited | Neo4j GDS | Added |
| ~85 graph features | No | Yes | Added |
| Nine supervised models | No | Yes | Added |
| L2 evidence fusion | No | Yes | Added |
| Persistent graph database | No | Neo4j | Added |
| Investigator case package | Limited | Formal generated package | Added |
| Fake classes for investigator cases | N/A | Never generated | Removed/Prohibited |
| Explainable investigation evidence | Limited | Model + graph + anomaly evidence | Added |
| Runtime validation | Limited | Multi-stage validation | Expanded |
| Structured logging | Limited | Required | Expanded |

[TODO: Compare this table against the actual old prototype feature extraction code and update the Old Prototype column with exact feature names.]

---

## 9. Investigator Input Contract

The new prototype accepts case data rather than requiring the original Elliptic++ benchmark.

### 9.1 `transactions.csv`

Expected fields:

```text
txid
timestamp
fee
size
version
locktime
```

[TODO: Confirm timestamp unit: seconds, milliseconds, or ISO-8601.]

[TODO: Confirm whether additional transaction-level fields are required.]

### 9.2 `inputs.csv`

Expected fields:

```text
txid
prev_txid
prev_vout
address
amount
script_type
```

This file is essential for reconstructing transaction provenance.

If:

```text
TX_B input spends an output of TX_A
```

create:

```text
TX_A → TX_B
```

### 9.3 `outputs.csv`

Expected fields:

```text
txid
output_index
address
amount
script_type
```

Required to connect transaction outputs to later transaction inputs.

### 9.4 `network.csv`

Expected fields:

```text
txid
timestamp
src_ip
src_port
dst_ip
dst_port
asn
country
```

[TODO: Confirm whether source/destination fields are always available.]

[TODO: Confirm whether production input uses raw IPs or blinded originator identifiers.]

---

## 10. Elliptic++ Case Generator

### 10.1 Purpose

The generator transforms investigator-provided raw data into a model-ready case package.

It must reproduce the **feature definitions, ordering, graph semantics, and temporal representation expected by the frozen models**.

It must NOT copy the original Elliptic++ graph.

### 10.2 Transaction generator

Input:

```text
transactions.csv
inputs.csv
outputs.csv
```

Output:

```text
txs_features.parquet
txs_edgelist.parquet
txs_temporal.parquet
```

Transaction graph rule:

For every input of transaction `TB`, if it spends an output of `TA`:

```text
TA → TB
```

### 10.3 Wallet generator

Use input/output addresses and transaction relationships to construct:

```text
wallet_features.parquet
AddrAddr_edgelist.parquet
AddrTx_edgelist.parquet
TxAddr_edgelist.parquet
wallet_temporal.parquet
```

### 10.4 Network generator

Use `network.csv` to produce:

```text
network_features.parquet
network_edgelist.parquet
network_temporal.parquet
```

[TODO: Freeze the exact network feature list and graph definition from the current trained network models.]

---

## 11. Classes / Labels

### 11.1 Training/benchmark data

The public Elliptic++ repository reports:

- Transaction nodes: 203,769
- Transaction edges: 234,355
- Transaction time steps: 49
- Transaction features: 183
- Transaction class-1: 4,545
- Transaction class-2: 42,019
- Transaction class-3/unknown: 157,205
- Wallet addresses: 822,942
- Temporal interaction nodes: 1,268,260
- Address-address edges: 2,868,964
- Address-transaction-address edges: 1,314,241
- Wallet time steps: 49
- Wallet features: 56

These are benchmark-dataset facts and must not be imposed as fixed sizes on investigator cases.

### 11.2 Investigator cases

Do NOT create:

```text
txs_classes.csv
wallets_classes.csv
```

with guessed labels.

Investigator labels are unknown until independently established.

The inference pipeline outputs scores/evidence, not fabricated ground truth.

---

## 12. Temporal Engine

Temporal information must be generated from actual timestamps/event ordering.

### 12.1 Required outputs

```text
txs_temporal.parquet
wallet_temporal.parquet
network_temporal.parquet
```

Example:

```text
entity_id
timestamp
time_index
snapshot_id
```

### 12.2 Transaction temporal representation

Conceptually:

```text
T1:
    TX1
    TX2

T2:
    TX3
    TX4

T3:
    TX5
```

The temporal model receives the exact representation expected by the trained FG-EGCN implementation.

### 12.3 Wallet temporal representation

Wallet activity is reconstructed from the actual sequence of transactions/interactions.

### 12.4 Network temporal representation

TGAT receives event ordering/timestamps and the exact time encoding expected by the trained implementation.

[TODO: Inspect the current TGAT training/inference code and document timestamp normalization, Δt calculation, and harmonic/time encoding.]

### 12.5 No synthetic temporal leakage

Never generate future information from the prediction target's future.

```text
available information at prediction time
        ↓
features / graph / temporal state
        ↓
prediction
```

---

## 13. Neo4j Database Architecture

Neo4j acts as the **persistent investigation graph**, not as a replacement for Parquet/PyTorch/scikit-learn.

### 13.1 Recommended node types

```text
(:Transaction)
(:Wallet)
(:Originator)
(:NetworkEvent)
```

[TODO: Confirm whether NetworkEvent should be a node or a relationship/property representation.]

### 13.2 Recommended relationships

```text
(:Wallet)-[:INPUT_TO]->(:Transaction)

(:Transaction)-[:OUTPUT_TO]->(:Wallet)

(:Transaction)-[:FLOWS_TO]->(:Transaction)

(:Wallet)-[:INTERACTS_WITH]->(:Wallet)

(:Originator)-[:OBSERVED]->(:Transaction)
```

### 13.3 Neo4j responsibility

- persistent relationships
- investigation queries
- multi-hop exploration
- graph visualization
- case graph storage
- GDS input

### 13.4 What Neo4j should NOT own

Do not make Neo4j the primary store for:

- model weights
- huge dense training matrices
- PyTorch tensors
- complete experiment artifacts
- large intermediate ML datasets when Parquet is more appropriate

---

## 14. Parquet Data Layer

Recommended layout:

```text
data/
├── raw/
├── processed/
│   ├── transactions.parquet
│   ├── inputs.parquet
│   ├── outputs.parquet
│   └── network.parquet
├── features/
│   ├── tx_features.parquet
│   ├── wallet_features.parquet
│   └── network_features.parquet
├── graphs/
│   ├── tx_edges.parquet
│   ├── addr_addr_edges.parquet
│   ├── addr_tx_edges.parquet
│   └── network_edges.parquet
└── temporal/
    ├── tx_temporal.parquet
    ├── wallet_temporal.parquet
    └── network_temporal.parquet
```

---

## 15. Model Input Contract

### 15.1 Transaction

**RF**

```text
X_tx
```

**GATv2**

```text
X_tx + TX→TX graph
```

**FG-EGCN**

```text
X_tx + TX→TX graph + temporal snapshots
```

### 15.2 Wallet

**Actor RF**

```text
X_wallet
```

**GraphSAGE**

```text
X_wallet + AddrAddr graph
```

**FG-EGCN**

```text
X_wallet + wallet graph + temporal snapshots
```

### 15.3 Network

**Network RF**

```text
X_network
```

**Network GraphSAGE**

```text
X_network + network graph
```

**Network TGAT**

```text
X_network + temporal network graph + exact trained time encoding
```

---

## 16. Critical Feature-Dimension Verification

The current project documentation states:

```text
Transaction: N × 182
Wallet:      M × 55
Network:     N × 13
```

However, the public Elliptic++ repository documents:

```text
Transaction: 183 features
Actors:      56 features
```

Therefore:

> **Do not assume the missing column.**

Before implementing the generator:

1. Inspect training preprocessing.
2. Inspect saved-model input dimensions.
3. Inspect exact feature-column list.
4. Identify excluded column(s).
5. Freeze feature order.
6. Add schema/version.
7. Test generator against training representation.

Required artifact:

```text
MODEL_INPUT_SCHEMA.json
```

Example:

```json
{
  "transaction": {
    "dimension": "[TODO]",
    "columns": [],
    "order_hash": "[TODO]"
  },
  "wallet": {
    "dimension": "[TODO]",
    "columns": [],
    "order_hash": "[TODO]"
  },
  "network": {
    "dimension": 13,
    "columns": [],
    "order_hash": "[TODO]"
  }
}
```

---

## 17. Complete Data Flow

### Step 1 — Investigator upload

```text
transactions.csv
inputs.csv
outputs.csv
network.csv
```

### Step 2 — File validation

Validate:

- required files
- required columns
- data types
- IDs
- timestamps
- amounts
- duplicate records
- references

Never silently discard invalid rows.

### Step 3 — Canonicalization

Normalize:

- IDs
- timestamps
- addresses
- numeric types
- script types
- network identifiers

### Step 4 — Case generation

Generate:

```text
Transaction features
Wallet features
Network features
Transaction edges
Wallet edges
Network edges
Temporal mappings
```

### Step 5 — Generator validation

Check:

```text
feature dimension
feature order
NaN/Inf
duplicate node IDs
missing edge endpoints
temporal ordering
edge direction
```

### Step 6 — Neo4j ingestion

Load:

```text
Transactions
Wallets
Originators
Relationships
```

### Step 7 — GDS graph projections

Create appropriate projections for:

- transaction graph
- wallet graph
- network graph
- cross-domain investigation graph

### Step 8 — Graph feature generation

Calculate the approved graph/temporal investigation features.

Write them to Neo4j and/or export them to Parquet.

### Step 9 — Supervised inference

Run:

```text
Transaction RF
Transaction GATv2
Transaction FG-EGCN

Wallet RF
Wallet GraphSAGE
Wallet FG-EGCN

Network RF
Network GraphSAGE
Network TGAT
```

### Step 10 — Isolation Forest

Run:

```text
Transaction IF
Wallet IF
Network IF
```

### Step 11 — Evidence fusion

Use the existing validated OOF fusion architecture where applicable.

Do not retrain the L2 stacker on investigator cases.

Validate missing model outputs before fusion.

### Step 12 — Graph/rule evidence

Combine:

- graph-derived evidence
- temporal evidence
- anomaly evidence
- deterministic rule evidence
- supervised model evidence

### Step 13 — Investigation priority

Produce a 0–100 investigation-priority score.

This is a prioritization mechanism, not automatically a calibrated probability.

### Step 14 — Explanation

For every prioritized entity, provide:

```text
Entity
Model evidence
Anomaly evidence
Graph evidence
Temporal evidence
Network evidence
Rules triggered
Relationships
Supporting feature values
```

### Step 15 — Investigator output

Example:

```text
Investigation Lead
------------------
TXID: TX123
Priority: 91

Evidence:
- Elevated transaction-model score
- Elevated network-model score
- High graph connectivity
- Significant downstream activity
- Temporal burst detected
- Related wallet cluster identified

Status:
Needs investigation
```

---

## 18. Evidence Fusion

Preserve four evidence categories:

### Supervised evidence

```text
9 model outputs
      ↓
OOF L2 fusion
      ↓
Supervised score
```

### Unsupervised evidence

```text
Isolation Forest
      ↓
Anomaly score
```

### Graph evidence

```text
85 graph/temporal features
      ↓
Graph evidence
```

### Deterministic evidence

```text
Rules
      ↓
Rule evidence
```

Then:

```text
Supervised evidence
        +
Anomaly evidence
        +
Graph evidence
        +
Rule evidence
        ↓
Investigation Priority
```

[TODO: Freeze the exact final priority formula and weights.]

---

## 19. 85 Graph/Temporal Features

The 85-feature layer is an **investigation feature layer**, not automatically input to the frozen nine models.

### 19.1 Transaction examples

- transaction in-degree
- transaction out-degree
- total degree
- weighted in-degree
- weighted out-degree
- neighbor count
- 2-hop neighbor count
- PageRank
- betweenness
- community assignment
- community size
- WCC
- k-core
- triangle count
- upstream count
- downstream count
- temporal activity
- recent activity
- [TODO: final approved list]

### 19.2 Wallet examples

- wallet degree
- weighted degree
- unique counterparties
- 2-hop counterparties
- PageRank
- betweenness
- community
- community size
- WCC
- k-core
- triangle count
- transaction count
- incoming/outgoing transaction count
- active timesteps
- lifetime
- activity rate
- [TODO: final approved list]

### 19.3 Network examples

- originator degree
- transaction count
- wallet count
- fan-in
- fan-out
- 2-hop network neighbors
- PageRank
- betweenness
- community
- community size
- temporal activity rate
- burstiness
- inter-arrival statistics
- active span
- [TODO: final approved list]

### 19.4 Cross-domain examples

- transaction-to-wallet count
- transaction-to-originator count
- wallet-to-originator count
- originator-to-wallet diversity
- originator-to-transaction diversity
- cross-domain neighborhood counts
- [TODO: final approved list]

---

## 20. Error Reduction Plan

### 20.1 Input validation

Before model execution:

```text
[ ] required files exist
[ ] required columns exist
[ ] schema version recognized
[ ] IDs non-null
[ ] timestamps parse
[ ] amounts numeric
[ ] duplicates checked
[ ] referenced transactions exist
[ ] referenced outputs exist
[ ] invalid rows reported
```

Never silently repair important forensic data.

### 20.2 Feature validation

```text
assert expected_dimension == actual_dimension
assert expected_columns == actual_columns
assert no unexpected columns
assert no missing required columns
assert no NaN
assert no +/-Inf
```

Use a schema hash to prevent accidental column reordering.

### 20.3 Graph validation

```text
[ ] every edge source exists
[ ] every edge target exists
[ ] correct edge direction
[ ] duplicate-edge policy applied
[ ] self-loop policy applied
[ ] node count recorded
[ ] edge count recorded
```

### 20.4 Temporal validation

```text
[ ] timestamps sorted
[ ] timestamp units known
[ ] no future events used
[ ] time index monotonic
[ ] snapshot assignment deterministic
[ ] Δt calculation deterministic
[ ] temporal model input matches training contract
```

### 20.5 Model validation

Record:

```text
model_version
feature_schema_version
model_input_dimension
model_checksum
```

Before inference:

```text
expected dimension == generated dimension
```

must pass.

If not:

```text
STOP
```

Do not automatically reshape, truncate, or pad features.

### 20.6 Logging

Use structured events such as:

```text
CASE_CREATED
INPUT_VALIDATED
FEATURE_GENERATION_STARTED
FEATURE_GENERATION_COMPLETED
GRAPH_BUILD_STARTED
GRAPH_BUILD_COMPLETED
NEO4J_LOAD_COMPLETED
GDS_ANALYSIS_COMPLETED
MODEL_INFERENCE_STARTED
MODEL_INFERENCE_COMPLETED
FUSION_COMPLETED
CASE_COMPLETED
```

Include:

```text
case_id
timestamp
component
status
duration
error_code
```

### 20.7 Error codes

```text
E001_INPUT_FILE_MISSING
E002_SCHEMA_INVALID
E003_TIMESTAMP_INVALID
E004_TRANSACTION_REFERENCE_MISSING
E005_FEATURE_DIMENSION_MISMATCH
E006_FEATURE_NAN
E007_GRAPH_ENDPOINT_MISSING
E008_NEO4J_CONNECTION_FAILED
E009_GDS_PROJECTION_FAILED
E010_MODEL_LOAD_FAILED
E011_MODEL_INFERENCE_FAILED
E012_FUSION_INPUT_MISSING
E013_TEMPORAL_ORDER_INVALID
```

---

## 21. Fallback Strategy

Fallbacks must never silently produce misleading results.

### Neo4j unavailable

ML inference may continue only for operations that do not require graph evidence.

Record:

```text
graph_evidence_status = unavailable
```

Do not substitute fake graph scores.

### One model unavailable

1. Record failure.
2. Check whether the saved fusion contract supports missing inputs.
3. Otherwise mark fusion unavailable.

Do not silently insert zero.

### Feature-generation failure

Stop the affected domain/model.

Do not feed partial or misaligned features into a model.

---

## 22. Testing Strategy

### 22.1 Unit tests

Test:

- input parsing
- timestamp parsing
- transaction graph generation
- wallet graph generation
- network graph generation
- feature calculations
- temporal indexing
- schema validation
- priority scoring
- explanation generation

### 22.2 Golden-data tests

Create:

```text
tests/data/golden_case/
```

Expected artifacts:

```text
expected_tx_features.parquet
expected_wallet_features.parquet
expected_edges.parquet
expected_temporal.parquet
```

Compare generated output against these.

### 22.3 Elliptic++ compatibility tests

Use a controlled Elliptic++ subset to verify:

```text
feature values
feature ordering
edge generation
time-step mapping
node IDs
```

within documented tolerances.

### 22.4 Model regression tests

For a fixed benchmark subset:

```text
old model output
vs
new inference pipeline output
```

must match within an explicitly documented numerical tolerance.

### 22.5 Integration tests

Test:

```text
upload
→ validation
→ generator
→ Neo4j
→ GDS
→ models
→ fusion
→ output
```

### 22.6 Failure tests

Intentionally test:

- missing file
- missing column
- malformed timestamp
- duplicate transaction
- missing previous transaction
- invalid edge
- NaN
- Inf
- Neo4j unavailable
- model file missing
- wrong feature dimension
- corrupted model
- empty dataset

---

## 23. Implementation Roadmap

### Phase 0 — Freeze contracts

Tasks:

1. Inspect every saved model.
2. Record input dimension.
3. Record exact feature order.
4. Record preprocessing/scalers.
5. Record graph format.
6. Record temporal input format.
7. Record output shape.
8. Generate `MODEL_INPUT_SCHEMA.json`.

**Gate:** No generator implementation until this passes.

### Phase 1 — Preserve old prototype

1. Freeze current code.
2. Add regression test.
3. Record baseline output.
4. Record dependency versions.

**Gate:** Old prototype remains equal to baseline.

### Phase 2 — Input validation

1. Implement input schema.
2. Validate required files.
3. Validate columns.
4. Validate types.
5. Validate references.
6. Implement error codes.
7. Add structured logging.

**Gate:** Invalid cases fail safely.

### Phase 3 — Elliptic++ Case Generator

1. Transaction feature generator.
2. Wallet feature generator.
3. Network feature generator.
4. Transaction edge generator.
5. Wallet edge generator.
6. Network edge generator.
7. Temporal engine.
8. Case package writer.

**Gate:** Generator output matches the frozen model input contracts.

### Phase 4 — Model inference

Integrate:

```text
Transaction: RF, GATv2, FG-EGCN
Wallet:      Actor RF, GraphSAGE, FG-EGCN
Network:     RF, GraphSAGE, TGAT
```

**Gate:** All nine models process a golden case.

### Phase 5 — Isolation Forest

1. Preserve old IF.
2. Add transaction IF.
3. Add wallet IF.
4. Add network IF.
5. Validate score orientation.
6. Validate preprocessing.

**Gate:** IF outputs are deterministic on golden data.

### Phase 6 — Neo4j

1. Install/configure Neo4j.
2. Define node labels.
3. Define relationship types.
4. Build ingestion.
5. Add indexes/constraints.
6. Implement case isolation.
7. Add investigation queries.

**Gate:** Neo4j graph matches the generated graph artifacts.

### Phase 7 — Neo4j GDS

1. Create transaction projection.
2. Create wallet projection.
3. Create network projection.
4. Implement selected algorithms.
5. Write/stream results.
6. Generate approved 85-feature set.

**Gate:** GDS results are deterministic and validated.

### Phase 8 — Evidence fusion

1. Load nine model scores.
2. Load IF scores.
3. Load graph evidence.
4. Load rules.
5. Apply approved fusion formula.
6. Generate explanations.

**Gate:** Missing evidence is handled explicitly.

### Phase 9 — Investigation UI

1. Case summary.
2. Ranked investigation leads.
3. Transaction details.
4. Wallet details.
5. Network details.
6. Interactive graph.
7. Timeline.
8. Model evidence.
9. Graph evidence.
10. Explanation panel.

[TODO: Choose frontend/UI stack.]

### Phase 10 — End-to-end validation

Test:

```text
Raw case
→ validation
→ generator
→ Neo4j
→ GDS
→ 9 models
→ IF
→ fusion
→ priority
→ dashboard
```

Final milestone:

> A new investigator case can be uploaded without requiring the original Elliptic++ dataset.

---

## 24. Repository Structure

```text
Bitcoin-Investigation-platform/
│
├── app/
│   ├── api/
│   ├── services/
│   └── ui/
│
├── generator/
│   ├── transaction/
│   ├── wallet/
│   ├── network/
│   ├── temporal/
│   ├── validation/
│   └── schemas/
│
├── models/
│   ├── transaction/
│   ├── wallet/
│   ├── network/
│   ├── isolation_forest/
│   └── fusion/
│
├── neo4j/
│   ├── schema/
│   ├── ingestion/
│   ├── projections/
│   ├── queries/
│   └── gds/
│
├── features/
│   ├── transaction/
│   ├── wallet/
│   ├── network/
│   ├── cross_domain/
│   └── temporal/
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── features/
│   ├── graphs/
│   └── temporal/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── regression/
│   ├── golden/
│   └── failure/
│
├── configs/
│   ├── models.yaml
│   ├── features.yaml
│   ├── neo4j.yaml
│   └── runtime.yaml
│
├── docs/
│
├── ELLIPTIC_CASE_GENERATOR_CONTRACT.md
├── SIH_GRAPH_FEATURE_SPECIFICATION.md
├── MODEL_INPUT_SCHEMA.json
└── NEW_PROTOTYPE_IMPLEMENTATION_PLAN.md
```

[TODO: Adapt this to the current repository rather than creating duplicate folders.]

---

## 25. Configuration Management

Do not hard-code model paths, feature dimensions, database credentials, or algorithm parameters.

Example:

```yaml
models:
  transaction_rf:
    path: "[TODO]"
    feature_schema: "transaction_v1"

  transaction_gatv2:
    path: "[TODO]"
    feature_schema: "transaction_v1"

  transaction_fg_egcn:
    path: "[TODO]"
    feature_schema: "transaction_v1"

neo4j:
  uri: "[TODO]"
  database: "[TODO]"

features:
  transaction_schema: "transaction_v1"
  wallet_schema: "wallet_v1"
  network_schema: "network_v1"
```

Never commit passwords or secrets.

---

## 26. Case Isolation

Every investigator case must have a unique:

```text
case_id
```

Example:

```text
CASE-2026-000001
```

All generated artifacts must be associated with that case.

Neo4j must prevent accidental cross-case relationships.

[TODO: Choose final case-isolation strategy after performance testing.]

---

## 27. Reproducibility

Every case should record:

```text
case_id
generator_version
schema_version
model_version
feature_version
neo4j_version
gds_version
python_version
timestamp
input_file_hashes
model_file_hashes
configuration_hash
```

This makes results reproducible and auditable.

---

## 28. Runtime Monitoring

Monitor:

- input validation duration
- feature-generation duration
- graph-ingestion duration
- GDS projection duration
- GDS algorithm duration
- model inference duration
- fusion duration
- memory usage
- node count
- edge count
- feature count
- missing values
- model failures

Example:

```text
CASE CASE-001
-----------------------------
Transactions: 12,431
Wallets:       8,721
Network events: 52,341

Feature generation: 12.4s
Neo4j ingestion:     8.1s
GDS analysis:         4.7s
ML inference:         6.3s
Fusion:               0.2s
Total:               31.7s
```

---

## 29. Open Questions / Assumptions

### Q1 — Exact transaction feature dimension

Public Elliptic++ documentation reports 183 transaction features, while the current project contract says 182.

**TODO:** Inspect training code and identify the excluded column.

### Q2 — Exact wallet feature dimension

Public Elliptic++ documentation reports 56 actor features, while the current project contract says 55.

**TODO:** Inspect training code and identify the excluded column.

### Q3 — Exact feature order

**TODO:** Extract exact ordered feature lists used by each saved model.

### Q4 — Temporal model input

**TODO:** Inspect FG-EGCN implementation and determine:

- fixed or variable number of snapshots;
- exact snapshot construction;
- temporal tensor shape;
- timestep encoding.

### Q5 — TGAT time encoding

**TODO:** Inspect TGAT implementation and document:

- timestamp normalization;
- Δt definition;
- harmonic/time encoding;
- event ordering.

### Q6 — Network graph definition

**TODO:** Freeze node/edge semantics for Network GraphSAGE and TGAT.

### Q7 — 85-feature specification

**TODO:** Freeze final feature list, formulas, data dependencies, time windows, and leakage rules.

### Q8 — Final priority formula

**TODO:** Freeze final weighting between supervised, anomaly, graph, and rule evidence.

### Q9 — Dashboard technology

**TODO:** Select frontend/UI stack.

### Q10 — Case isolation

**TODO:** Decide whether case isolation uses Case nodes/properties, separate databases, separate graph namespaces, or another strategy.

---

## 30. Non-Negotiable Implementation Rules

1. **Never invent investigator labels.**
2. **Never silently reorder model features.**
3. **Never silently truncate or pad model inputs.**
4. **Never replace missing model evidence with zero without an explicit policy.**
5. **Never use future information in temporal features.**
6. **Never copy the original Elliptic++ graph into an investigator case.**
7. **Generate the case graph from actual investigator provenance data.**
8. **Keep benchmark data and investigator data separate.**
9. **Keep model weights outside Neo4j.**
10. **Use Parquet for ML-oriented tabular/edge data.**
11. **Use Neo4j for persistent relationships and investigation queries.**
12. **Use GDS for approved graph algorithms/features.**
13. **Validate every model input before inference.**
14. **Record versions and hashes for reproducibility.**
15. **Fail safely rather than producing silently corrupted results.**
16. **Treat scores as investigation evidence, not automatic proof of criminality.**
17. **Do not add the 85 graph features to frozen models without retraining and a new validation study.**
18. **Do not assume public Elliptic++ feature counts match the project's trained tensor dimensions; verify the actual training pipeline.**

---

## 31. Definition of Done

```text
[ ] Investigator can upload supported raw files
[ ] Input validation works
[ ] Invalid cases fail safely
[ ] Elliptic++-compatible feature generation works
[ ] Transaction graph generation works
[ ] Wallet graph generation works
[ ] Network graph generation works
[ ] Temporal engine works
[ ] All nine trained models run successfully
[ ] Isolation Forest runs
[ ] Neo4j case graph is created
[ ] GDS projections work
[ ] Approved graph features are generated
[ ] Evidence fusion works
[ ] Investigation priority is produced
[ ] Explanations are produced
[ ] Dashboard displays results
[ ] Golden tests pass
[ ] Regression tests pass
[ ] Failure tests pass
[ ] Model schemas are versioned
[ ] Feature schemas are versioned
[ ] Case artifacts are reproducible
[ ] No fake labels are generated
[ ] No cross-case data contamination occurs
```

---

## 32. Reference Architecture Summary

```text
                         INVESTIGATOR
                              |
                              v
                    Raw Case Input Files
                              |
                              v
                    Input Validation
                              |
                              v
                     Canonical Schema
                              |
                              v
                 Elliptic++ Case Generator
                              |
          +-------------------+-------------------+
          |                   |                   |
          v                   v                   v
     Transaction            Wallet             Network
       package              package             package
          |                   |                   |
          +-------------------+-------------------+
                              |
                 +------------+------------+
                 |                         |
                 v                         v
           ML Data Layer              Neo4j Graph
             Parquet                      |
                 |                        v
                 |                    GDS Graph
                 |                    Algorithms
                 |                        |
                 |                        v
                 |                 85 Investigation
                 |                     Features
                 |                        |
                 +-----------+------------+
                             |
                             v
                     Evidence Collection
                             |
          +------------------+------------------+
          |                  |                  |
          v                  v                  v
    9 Supervised         Isolation          Rules /
       Models              Forest           Graph Evidence
          |                  |                  |
          +------------------+------------------+
                             |
                             v
                       Evidence Fusion
                             |
                             v
                  Investigation Priority
                             |
                             v
                  Investigator Dashboard
                             |
                             v
                     Investigation Lead
```

---

## 33. External Reference Notes

The official Elliptic++ repository documents two major datasets: transactions and actors/wallet addresses. It reports 203,769 transaction nodes, 234,355 money-flow edges, 49 time steps and 183 transaction features; the actor dataset reports 822,942 wallet addresses, 1,268,260 temporal interaction nodes, 2,868,964 address-address edges, 1,314,241 address-transaction-address edges, 49 time steps and 56 features.

Neo4j's official GDS documentation describes the standard workflow as loading graph data from Neo4j, creating an in-memory graph projection, running graph algorithms, and writing or streaming results. GDS includes centrality, community detection, similarity, pathfinding, node-embedding and other algorithm categories.

References:

- Official Elliptic++ repository: https://github.com/git-disl/EllipticPlusPlus
- Neo4j GDS documentation: https://neo4j.com/docs/graph-data-science/current/
- Neo4j GDS graph creation/projection: https://neo4j.com/docs/graph-data-science/current/management-ops/graph-creation/
- Neo4j GDS algorithms: https://neo4j.com/docs/graph-data-science/current/algorithms/
- Neo4j GDS Python client: https://neo4j.com/docs/graph-data-science-client/current/

---

## 34. Immediate Next Actions for the AI Coding Agent

Before writing new production code:

### Step 1

Inspect:

```text
PROTOTYPE.md
ELLIPTIC_CASE_GENERATOR_CONTRACT.md
SIH_GRAPH_FEATURE_SPECIFICATION.md
csv_adapter.py
field_mapping.py
```

### Step 2

Locate all saved model files.

### Step 3

For each model determine:

```text
input dimension
feature order
preprocessing
graph input
temporal input
output shape
```

### Step 4

Generate:

```text
MODEL_INPUT_SCHEMA.json
```

### Step 5

Build golden-data compatibility tests.

### Step 6

Only after schema tests pass, implement the Elliptic++ Case Generator.

### Step 7

Only after generator tests pass, integrate Neo4j.

### Step 8

Only after graph ingestion passes, implement GDS feature generation.

### Step 9

Only after individual components pass, integrate evidence fusion.

### Step 10

Run the complete end-to-end investigator case.

---

## 35. Final Design Principle

The new prototype should be understood as:

```text
                 RAW INVESTIGATOR DATA
                          |
                          v
                  CASE GENERATION
                          |
        +-----------------+-----------------+
        |                 |                 |
        v                 v                 v
   Model Features      Graphs           Temporal
        |                 |                 |
        v                 v                 v
   9 ML Brains         Neo4j/GDS        Temporal Models
        |                 |                 |
        +-----------------+-----------------+
                          |
                          v
                  Evidence Fusion
                          |
                          v
               Investigation Priority
                          |
                          v
                  Explainable Lead
```

The central implementation rule is:

> **The investigator supplies the case data. The system generates the compatible representation. Elliptic++ is the training/benchmark reference, not an input requirement for every investigation.**
