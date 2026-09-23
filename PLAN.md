# Implementation Plan: AI-Powered Bitcoin Transaction Traffic Monitoring & Analysis (SIH26146)

Backend-first prototype for offline-first investigative intelligence: ingesting synthetic Bitcoin blockchain/transaction metadata and network telemetry, correlating them, constructing entity graphs, extracting features, detecting anomalies using Isolation Forest and deterministic behavioral rules, scoring priority, tracking provenance, and serving investigator APIs.

---

## 1. System Constraints & Disk Safety (D: Drive Only)

> [!IMPORTANT]
> **Disk Space Safety & Strict D: Drive Confinement**:
> C: drive has only **0.07 GB** of available space.
> All Conda environments, package downloads, pip caches, temporary files, databases, and synthetic datasets will be strictly isolated to `D:\` using:
> - Conda environment prefix: `D:\conda\envs\btc-intel`
> - Package cache: `D:\conda\pkgs`
> - Pip cache: `D:\tmp\pip_cache`
> - Temporary directory: `D:\tmp`
> - Total required space: **~2.0 GB - 2.5 GB** (D: currently has 22.88 GB free).

> [!NOTE]
> Per the interview alignment:
> - **Build Scope**: Full End-to-End MVP (Ingestion, Correlation, Graph, Features, Isolation Forest, Rules, Priority Scoring, SQLite + Parquet Storage, FastAPI endpoints, CLI scripts, and automated test suite).
> - **AI / Explainer Strategy**: Deterministic Explainer (100% offline, zero GPU required, evidence-backed provenance). Optional Ollama / Laya adapters will be stubbed for future expansion.
> - **GeoIP Enrichment**: Local MaxMind GeoLite2 reader with graceful fallback (null fields without pipeline failure if MMDB file is absent).

---

## 2. Architecture & Build Sequence

The platform implementation adheres to the 9-phase sequence defined in `PROTOTYPE.md`:

```
Phase 1: Environment Setup & Foundation Configuration
Phase 2: Database Models & Canonical Pydantic Schemas
Phase 3: Ingestion, Validation & Normalization Service (CSV, JSON, XML)
Phase 4: Correlation, GeoIP & Entity Graph Builder
Phase 5: Feature Engineering Engine (Transaction, Wallet, Network, Graph)
Phase 6: Detectors (Isolation Forest, Behavioral Rules, Graph & Network Signals)
Phase 7: Evidence Fusion, Priority Scoring & Deterministic Explainer
Phase 8: Storage Layer (SQLite metadata + Parquet analytical tables) & Pipeline Orchestration
Phase 9: FastAPI Endpoints, Auth/RBAC, CLI, Synthetic Generator & Test Suite
```

---

## 3. Detailed Component Plan

### Phase 1: Environment Setup & Foundation Configuration
- `environment.yml`: Conda environment specification targeting Python 3.11 with:
  - `numpy`, `pandas`, `scikit-learn`, `networkx`
  - `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`
  - `sqlalchemy`, `duckdb`, `pyarrow`
  - `pytest`, `httpx`, `defusedxml`, `geoip2`
  - `argon2-cffi`, `python-jose`, `python-multipart`
- `pyproject.toml`: Project configuration and tool settings.
- `.env.example`: Configuration defaults (`DATABASE_URL=sqlite:///d:/Bitcoin-Investigation-platform/data/app.db`, `DATA_DIR=d:/Bitcoin-Investigation-platform/data`, `OFFLINE_MODE=True`).
- `backend/app/core/config.py`: Centralized settings loaded via Pydantic Settings.
- `backend/app/core/security.py`: JWT token generation, verification, and Argon2 password hashing.
- `backend/app/core/errors.py`: Custom platform exceptions and HTTP error handlers.
- `backend/app/core/logging.py`: Structured forensic logging.

### Phase 2: Database Models & Canonical Pydantic Schemas
- `backend/app/db/session.py`: SQLite engine and scoped sessionmaker.
- `backend/app/db/models.py`: SQLAlchemy ORM models:
  - `User`: System analysts and administrators with role-based access.
  - `Case`: Investigative case folders and status.
  - `Dataset`: Uploaded raw files, format, hash, and row counts.
  - `AnalysisRun`: Execution runs, configuration parameters, and execution state.
  - `Alert`: Flagged entities/transactions, priority scores, and reason summary.
  - `Feedback`: Investigator feedback tags (`relevant`, `benign`, `needs_review`) and notes.
- `backend/app/schemas/`:
  - `auth.py`, `case.py`, `dataset.py`, `run.py`, `alert.py`, `graph.py`, `evidence.py`, `feedback.py`.
  - Canonical data models matching Section 5.4 of `PROTOTYPE.md`:
    - Canonical transaction: `record_id`, `timestamp`, `txid`, `input_addresses`, `output_addresses`, `input_amounts`, `output_amounts`, `fee`, `script_type`.
    - Canonical network observation: `record_id`, `timestamp`, `src_ip`, `dst_ip`, `src_port`, `dst_port`, `txid`, `geo_country`, `asn`.
    - Combined SIH record: merges transaction and network fields into a single record.

### Phase 3: Ingestion, Validation & Normalization Service
- `backend/app/services/ingestion/adapters.py`: Base ingestion adapter interface.
- `backend/app/services/ingestion/csv_adapter.py`: Streaming CSV parser with alias support.
- `backend/app/services/ingestion/json_adapter.py`: JSON and JSON-Lines parser.
- `backend/app/services/ingestion/xml_adapter.py`: Safe XML parser using `defusedxml`.
- `backend/app/services/ingestion/field_mapping.py`: Flexible column aliasing matching diverse SIH schemas.
- `backend/app/services/ingestion/validate.py`:
  - Schema check: data types, IP addresses, ports, timestamps.
  - Array parity check: `len(input_addresses) == len(input_amounts)` and `len(output_addresses) == len(output_amounts)`.
  - Monetary consistency check: `total_input` vs `total_output + fee`.
- `backend/app/services/ingestion/normalize.py`: Normalizes timestamps to UTC, IPs to standard string format, produces SHA-256 dataset hash.

### Phase 4: Correlation, GeoIP & Entity Graph Builder
- `backend/app/services/correlation.py`:
  - Exact TXID correlation (`TXID_EXACT`).
  - Proximity time-window correlation (`TIME_WINDOW`) for observations missing txid.
  - Records provenance basis for every network-to-transaction link.
- `backend/app/services/geoip.py`: Local MaxMind GeoLite2 reader with graceful fallback (returns null if MMDB missing, zero crashes).
- `backend/app/services/graph_builder.py`:
  - NetworkX entity graph construction:
    - Nodes: `wallet`, `transaction`, `ip`, `asn`, `country`.
    - Edges: `SPENT_FROM`, `SENT_TO`, `RELAYED_BY`, `HOSTED_IN`, `LOCATED_IN`.
  - Graph serialization to `graph.json` and `graph_stats.json` for investigator visualization.

### Phase 5: Feature Extraction Engine
- `backend/app/services/features.py`:
  - Transaction features: `total_input`, `total_output`, `fee`, `fee_ratio`, `in_degree`, `out_degree`.
  - Wallet features: total volume, tx count, in-degree, out-degree, fan-out ratio, address reuse.
  - Network features: unique IPs observed, port diversity, ASN diversity.
  - Graph features: PageRank, betweenness centrality, community ID, motif detection.

### Phase 6: Detectors & Behavioral Rules
- `backend/app/services/detectors/isolation_forest.py`: Unsupervised anomaly detection on normalized numerical features.
- `backend/app/services/detectors/behavior_rules.py`: Deterministic rules:
  - `RULE_PEELING_CHAIN`: Successive small transfers from one primary input.
  - `RULE_RAPID_DISPERSAL`: 1 input split into dozens of outputs in brief window.
  - `RULE_DUST_ATTACK`: Flood of sub-dust threshold transactions.
  - `RULE_FEE_ANOMALY`: Exceptionally high or zero fee transactions.
  - `RULE_HIGH_FAN_OUT`: Extreme ratio of outputs to inputs.
- `backend/app/services/detectors/graph_signals.py`: Identifies high-centrality bridges and dense subgraphs.
- `backend/app/services/detectors/network_signals.py`: Detects multi-IP relay bursts and anomalous port usage.

### Phase 7: Score Fusion, Provenance & Deterministic Explainer
- `backend/app/services/scoring.py`:
  - Composite priority formula:
    `priority_score = w_a * anomaly_score + w_b * behavior_score + w_g * graph_score + w_n * network_score`
  - Priority tiers: `CRITICAL` (≥ 0.8), `HIGH` (≥ 0.6), `MEDIUM` (≥ 0.4), `LOW` (< 0.4).
- `backend/app/services/evidence.py` & `backend/app/services/provenance.py`:
  - Evidence packs attaching exact source record IDs, extracted feature values, and triggered rule identifiers.
- `backend/app/services/explain.py`: Deterministic text explanation generator.
- `backend/app/services/report.py`: Exports comprehensive JSON and Markdown case reports.

### Phase 8: Storage Manager & Pipeline Orchestrator
- `backend/app/storage/case_store.py`: Manages case directory hierarchy (`raw/`, `validated/`, `normalized/`, `correlated/`, `features/`, `graph/`, `models/`, `reports/`).
- `backend/app/storage/parquet_store.py`: High-performance columnar read/write via PyArrow/DuckDB.
- `backend/app/storage/file_store.py`: Raw artifact storage with immutable checksums.
- `backend/app/services/pipeline.py`: Orchestrates full pipeline end-to-end.
- `backend/app/services/job_manager.py`: Async task execution and status tracking.

### Phase 9: FastAPI Web Application & Test Suite
- `backend/app/main.py`: FastAPI application entrypoint with CORS, error handlers, and lifecycle hooks.
- `backend/app/api/router.py`: REST routes:
  - `/api/v1/auth`: Login, token refresh, user profile.
  - `/api/v1/cases`: Case CRUD operations.
  - `/api/v1/datasets`: Upload CSV/JSON/XML, validate, list.
  - `/api/v1/runs`: Trigger analysis pipeline, check run status.
  - `/api/v1/alerts`: Query ranked alerts, filter by tier/entity.
  - `/api/v1/wallets`: Wallet/entity detail, neighboring edges, timeline.
  - `/api/v1/graph`: Cytoscape/D3 compatible node/link graph data.
  - `/api/v1/reports`: Download JSON/Markdown case investigation reports.
  - `/api/v1/feedback`: Submit investigator feedback annotations.
- `scripts/generate_synthetic.py`: Synthetic dataset generator injecting realistic Bitcoin topologies and typologies.
- `scripts/seed_admin.py`: Database bootstrap script.
- `backend/tests/`: Comprehensive unit and integration test suite (`pytest`).

---

## 4. Verification & Acceptance Criteria

1. **Zero Impact on C: Drive**:
   - Verification that Conda environment, caches, and database stay strictly on `D:\`.
2. **Schema & Array Parity Validation**:
   - Ingestion tests verify 100% rejection/quarantine of mismatched array rows.
3. **Evidence Provenance**:
   - 100% of generated alerts link to source record IDs.
4. **Deterministic Behavior**:
   - Identical input + seed produces identical scores and explanations.
5. **Offline Mode**:
   - 0 outbound network requests during analysis.
6. **API Readiness**:
   - All REST endpoints pass automated integration tests.

