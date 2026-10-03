"""
Unit Tests for New Pipeline Services (Input Validation & Canonicalization).
"""

import os
import shutil
import tempfile
import pytest
import numpy as np
import pandas as pd
from backend.app.services.new_pipeline.input_validator import InputValidator, ErrorCode
from backend.app.services.new_pipeline.canonicalizer import Canonicalizer


@pytest.fixture
def sample_case_dir():
    temp_dir = tempfile.mkdtemp()
    
    # Create valid dummy CSV files
    df_tx = pd.DataFrame({
        "txid": ["tx1", "tx2"],
        "timestamp": ["2026-01-01T10:00:00Z", "2026-01-01T11:00:00Z"],
        "fee": [0.0001, 0.0002],
        "size": [225, 300]
    })
    df_tx.to_csv(os.path.join(temp_dir, "transactions.csv"), index=False)

    df_inp = pd.DataFrame({
        "txid": ["tx1", "tx2"],
        "prev_txid": ["tx0", "tx1"],
        "prev_vout": [0, 0],
        "address": ["addr_A", "addr_B"],
        "amount": [1.0, 0.99]
    })
    df_inp.to_csv(os.path.join(temp_dir, "inputs.csv"), index=False)

    df_out = pd.DataFrame({
        "txid": ["tx1", "tx2"],
        "output_index": [0, 0],
        "address": ["addr_B", "addr_C"],
        "amount": [0.9999, 0.9898]
    })
    df_out.to_csv(os.path.join(temp_dir, "outputs.csv"), index=False)

    df_net = pd.DataFrame({
        "txid": ["tx1", "tx2"],
        "timestamp": ["2026-01-01T10:00:01Z", "2026-01-01T11:00:02Z"],
        "src_ip": ["192.168.1.1", "10.0.0.1"],
        "src_port": [8333, 8333],
        "dst_ip": ["1.1.1.1", "8.8.8.8"],
        "dst_port": [8333, 8333]
    })
    df_net.to_csv(os.path.join(temp_dir, "network.csv"), index=False)

    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_input_validator_success(sample_case_dir):
    validator = InputValidator(sample_case_dir)
    report = validator.validate()
    assert report.is_valid is True
    assert len(report.errors) == 0
    assert report.stats["transactions_count"] == 2
    assert report.stats["inputs_count"] == 2


def test_input_validator_missing_file(sample_case_dir):
    os.remove(os.path.join(sample_case_dir, "transactions.csv"))
    validator = InputValidator(sample_case_dir)
    report = validator.validate()
    assert report.is_valid is False
    assert any(e.code == ErrorCode.E001_INPUT_FILE_MISSING for e in report.errors)


def test_input_validator_orphan_reference(sample_case_dir):
    df_inp = pd.DataFrame({
        "txid": ["tx_nonexistent"],
        "prev_txid": ["tx0"],
        "prev_vout": [0],
        "address": ["addr_A"],
        "amount": [1.0]
    })
    df_inp.to_csv(os.path.join(sample_case_dir, "inputs.csv"), index=False)
    validator = InputValidator(sample_case_dir)
    report = validator.validate()
    assert report.is_valid is False
    assert any(e.code == ErrorCode.E004_TRANSACTION_REFERENCE_MISSING for e in report.errors)


def test_canonicalizer(sample_case_dir):
    canonical_dir = os.path.join(sample_case_dir, "canonical")
    canonicalizer = Canonicalizer(raw_dir=sample_case_dir, canonical_dir=canonical_dir)
    paths = canonicalizer.canonicalize()
    
    assert os.path.exists(paths["transactions"])
    assert os.path.exists(paths["inputs"])
    assert os.path.exists(paths["outputs"])
    assert os.path.exists(paths["network"])

    df_c_tx = pd.read_parquet(paths["transactions"])
    assert "timestamp_epoch" in df_c_tx.columns
    assert "timestamp_iso" in df_c_tx.columns
    assert len(df_c_tx) == 2


def test_elliptic_case_generator_and_validator(sample_case_dir):
    from backend.app.services.new_pipeline.elliptic_case_generator import EllipticCaseGenerator
    from backend.app.services.new_pipeline.generator_validator import GeneratorValidator

    canonical_dir = os.path.join(sample_case_dir, "canonical")
    canonicalizer = Canonicalizer(raw_dir=sample_case_dir, canonical_dir=canonical_dir)
    canonicalizer.canonicalize()

    generated_dir = os.path.join(sample_case_dir, "generated_case")
    schema_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
        "ml_engine",
        "SIH_SUPERVISED_ML",
        "schemas",
        "MODEL_INPUT_SCHEMA.json",
    )
    generator = EllipticCaseGenerator(canonical_dir=canonical_dir, output_dir=generated_dir, schema_path=schema_path)
    res = generator.generate_case(time_window_hours=12)

    assert os.path.exists(res["transaction_features"])
    assert os.path.exists(res["wallet_features"])
    assert os.path.exists(res["network_features"])

    df_tx_f = pd.read_parquet(res["transaction_features"])
    assert len(df_tx_f) == 2
    # 182 features + txid + time_step = 184 columns
    assert df_tx_f.shape[1] == 184

    df_wal_f = pd.read_parquet(res["wallet_features"])
    # 55 features + address + time_step = 57 columns
    assert df_wal_f.shape[1] == 57

    df_net_f = pd.read_parquet(res["network_features"])
    # 13 features + txid + time_step = 15 columns
    assert df_net_f.shape[1] == 15

    # Run GeneratorValidator
    validator = GeneratorValidator(generated_dir=generated_dir, schema_path=schema_path)
    is_valid, errors = validator.validate()
    assert is_valid is True
    assert len(errors) == 0


def test_ml_inference_9_brains(sample_case_dir):
    from backend.app.services.ml_inference import ml_engine

    assert ml_engine.is_loaded is True
    assert ml_engine.supervised_available is True
    assert ml_engine.isolation_forests_available is True

    # Dummy inputs matching exact schema shapes
    X_tx = np.zeros(182, dtype=np.float32)
    X_wal = np.zeros(55, dtype=np.float32)
    X_net = np.zeros(13, dtype=np.float32)

    pred = ml_engine.predict_9_brains(
        X_tx=X_tx,
        edge_index_tx=None,
        X_wal=X_wal,
        edge_index_wal=None,
        X_net=X_net,
        edge_index_net=None,
    )

    assert "probabilities" in pred
    assert len(pred["probabilities"]) == 9
    assert 0.0 <= pred["supervised_score"] <= 100.0
    assert pred["is_illicit"] in (0, 1)
    assert "isolation_forest" in pred
    assert len(pred["isolation_forest"]) == 3


def test_neo4j_service_decoupling():
    from backend.app.services.new_pipeline.neo4j_service import Neo4jInvestigationService

    # Test offline resilience & graceful fallback
    service = Neo4jInvestigationService(enabled=False)
    assert service.is_connected is False

    # Ingestion should return bypassed without failing
    res = service.ingest_case(
        case_id="case_offline_01",
        df_tx=pd.DataFrame(),
        df_tx_edges=pd.DataFrame(),
        df_wal=pd.DataFrame(),
        df_addr_addr=pd.DataFrame(),
        df_addr_tx=pd.DataFrame(),
        df_tx_addr=pd.DataFrame(),
    )
    assert res["status"] == "bypassed"
    assert "offline or disabled" in res["reason"]

    # Query should return available=False gracefully
    q = service.query_multihop(case_id="case_offline_01", start_txid="tx_test", hops=2)
    assert q["available"] is False
    assert len(q["nodes"]) == 0


def test_graph_feature_extractor():
    from backend.app.services.new_pipeline.gds_feature_extractor import GraphFeatureExtractor

    extractor = GraphFeatureExtractor()

    df_tx = pd.DataFrame({"txid": ["txA", "txB", "txC"], "fee": [0.001, 0.002, 0.0005]})
    df_tx_edges = pd.DataFrame({
        "source_txid": ["txA", "txB"],
        "target_txid": ["txB", "txC"]
    })
    df_wal = pd.DataFrame({"address": ["wal_1", "wal_2"]})
    df_addr_addr = pd.DataFrame({
        "source_address": ["wal_1"],
        "target_address": ["wal_2"]
    })

    feats = extractor.extract_features(
        case_id="case_gds_test",
        df_tx=df_tx,
        df_tx_edges=df_tx_edges,
        df_wal=df_wal,
        df_addr_addr=df_addr_addr,
    )

    assert not feats.empty
    assert len(feats) == 5  # 3 tx + 2 wallets
    assert "pagerank" in feats.columns
    assert "betweenness" in feats.columns
    assert "wcc_component_id" in feats.columns
    assert "dispersion_ratio" in feats.columns
    assert (feats["pagerank"] >= 0.0).all()


def test_evidence_fusion_engine():
    from backend.app.services.new_pipeline.evidence_fusion import EvidenceFusionEngine

    fusion = EvidenceFusionEngine()

    # Critical case
    pack_crit = fusion.fuse_entity(
        entity_id="tx_illicit_01",
        entity_type="transaction",
        supervised_prob=0.92,
        anomaly_score=0.85,
        behavior_score=0.75,
        graph_score=0.60,
        network_score=0.50,
        rules_triggered=["RULE_PEELING_CHAIN", "RULE_HIGH_FAN_OUT"],
        source_records=["rec_1", "rec_2"],
    )

    assert pack_crit["priority_score"] >= 70.0
    assert pack_crit["severity_tier"] in ("CRITICAL", "HIGH")
    assert "supervised_score" in pack_crit["score_components"]
    assert len(pack_crit["rules_triggered"]) == 2
    assert "Immediate forensic triage" in pack_crit["investigation_recommendation"] or "Elevated risk" in pack_crit["investigation_recommendation"]

    # Low priority case
    pack_low = fusion.fuse_entity(
        entity_id="wal_clean_01",
        entity_type="wallet",
        supervised_prob=0.05,
        anomaly_score=0.10,
        behavior_score=0.0,
        graph_score=0.05,
        network_score=0.0,
    )
    assert pack_low["priority_score"] < 40.0
    assert pack_low["severity_tier"] == "LOW"


def test_dynamic_rules_engine():
    from backend.app.services.rules_engine import DynamicRulesEngine

    rules = [
        {
            "id": "r_tx_count",
            "name": "High Volume Wallet",
            "target_entity": "wallet",
            "field": "transaction_count",
            "operator": ">=",
            "threshold": 10.0,
            "severity": "high",
            "weight": 1.0,
            "enabled": 1,
        },
        {
            "id": "r_fan_out",
            "name": "Dispersal Wallet",
            "target_entity": "wallet",
            "field": "fan_out",
            "operator": ">",
            "threshold": 5.0,
            "severity": "critical",
            "weight": 1.5,
            "enabled": 1,
        },
        {
            "id": "r_disabled",
            "name": "Disabled Rule",
            "target_entity": "wallet",
            "field": "fan_in",
            "operator": ">",
            "threshold": 1.0,
            "severity": "low",
            "weight": 1.0,
            "enabled": 0,
        },
    ]

    engine = DynamicRulesEngine(rules)

    # Test wallet hit
    wallet_data = {
        "entity_id": "wallet:1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
        "transaction_count": 15,
        "fan_out": 8,
        "fan_in": 10,
    }

    hits = engine.evaluate_wallet(wallet_data)
    assert len(hits) == 2  # r_tx_count and r_fan_out triggered; disabled is skipped
    assert any(h["rule_id"] == "r_tx_count" for h in hits)
    assert any(h["rule_id"] == "r_fan_out" for h in hits)

    # Compute rule score
    rule_score = engine.compute_rule_score(hits)
    assert rule_score > 0.0
    assert rule_score <= 100.0


def test_separate_scores_in_evidence_fusion():
    from backend.app.services.new_pipeline.evidence_fusion import EvidenceFusionEngine

    fusion = EvidenceFusionEngine()

    pack = fusion.fuse_entity(
        entity_id="wallet:W_TEST_MULTI_STREAM",
        entity_type="wallet",
        supervised_prob=0.88,
        anomaly_score=0.75,
        behavior_score=0.50,
        graph_score=0.65,
        network_score=0.30,
        rule_score=60.0,
        rules_triggered=["RULE_PEELING_CHAIN", "Custom Dispersal"],
    )

    # Assert separate stream scores exist and match expectations
    assert "supervised_score" in pack
    assert pack["supervised_score"] == 88.0
    assert "unsupervised_score" in pack
    assert pack["unsupervised_score"] == 75.0
    assert "graph_score" in pack
    assert pack["graph_score"] == 65.0
    assert "rule_score" in pack
    assert pack["rule_score"] == 60.0

    # Assert components mapping
    comps = pack["score_components"]
    assert comps["supervised_score"] == 88.0
    assert comps["unsupervised_score"] == 75.0
    assert comps["graph_score"] == 65.0
    assert comps["rule_score"] == 60.0






