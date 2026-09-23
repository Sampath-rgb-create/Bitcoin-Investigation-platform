"""
Unit and Integration Tests for Phase 5, 6, 7 Analytics and Detection Pipeline.
"""

import pytest
import numpy as np
import pandas as pd
import networkx as nx

from backend.app.services.graph_builder import EntityGraphBuilder
from backend.app.services.features import FeatureEngine
from backend.app.services.detectors.isolation_forest import IsolationForestDetector
from backend.app.services.detectors.behavior_rules import BehaviorRulesDetector
from backend.app.services.detectors.graph_signals import GraphSignalsDetector
from backend.app.services.detectors.network_signals import NetworkSignalsDetector
from backend.app.services.scoring import PriorityFusionScorer
from backend.app.services.evidence import EvidenceManager
from backend.app.services.explain import DeterministicExplainer
from backend.app.services.report import ReportGenerator


@pytest.fixture
def sample_data():
    transactions = [
        {
            "record_id": "tx-001",
            "timestamp": "2026-01-01T10:00:00Z",
            "txid": "tx_normal_1",
            "input_addresses": ["W_A"],
            "output_addresses": ["W_B", "W_C"],
            "input_amounts": [1.5],
            "output_amounts": [1.0, 0.49],
            "fee": 0.01,
            "script_type": "P2WPKH",
            "src_ip": "198.51.100.1",
            "geo_country": "US",
            "asn": "AS15169",
        },
        {
            "record_id": "tx-002",
            "timestamp": "2026-01-01T10:00:05Z",
            "txid": "tx_fanout_1",
            "input_addresses": ["W_DISPERSE"],
            "output_addresses": [f"W_OUT_{i}" for i in range(15)],
            "input_amounts": [10.0],
            "output_amounts": [0.65 for _ in range(15)],
            "fee": 0.25,
            "script_type": "P2WPKH",
            "src_ip": "203.0.113.5",
            "geo_country": "RU",
            "asn": "AS12345",
        },
        {
            "record_id": "tx-003",
            "timestamp": "2026-01-01T10:00:10Z",
            "txid": "tx_dust_1",
            "input_addresses": ["W_ATTACKER"],
            "output_addresses": ["W_VICTIM"],
            "input_amounts": [0.001],
            "output_amounts": [0.00005],
            "fee": 0.00095,
            "script_type": "P2PKH",
            "src_ip": "198.51.100.2",
            "geo_country": "CN",
            "asn": "AS4134",
        },
        {
            "record_id": "tx-004",
            "timestamp": "2026-01-01T10:00:15Z",
            "txid": "tx_dust_2",
            "input_addresses": ["W_ATTACKER"],
            "output_addresses": ["W_VICTIM"],
            "input_amounts": [0.001],
            "output_amounts": [0.00005],
            "fee": 0.00095,
            "script_type": "P2PKH",
            "src_ip": "198.51.100.2",
            "geo_country": "CN",
            "asn": "AS4134",
        },
    ]

    network_observations = [
        {
            "record_id": "net-001",
            "timestamp": "2026-01-01T10:00:01Z",
            "txid": "tx_normal_1",
            "src_ip": "198.51.100.1",
            "dst_ip": "192.0.2.1",
            "src_port": 50000,
            "dst_port": 8333,
            "geo_country": "US",
            "asn": "AS15169",
        },
        {
            "record_id": "net-002",
            "timestamp": "2026-01-01T10:00:06Z",
            "txid": "tx_fanout_1",
            "src_ip": "203.0.113.5",
            "dst_ip": "192.0.2.2",
            "src_port": 50001,
            "dst_port": 9999,  # Port anomaly
            "geo_country": "RU",
            "asn": "AS12345",
        },
    ]

    return transactions, network_observations


def test_entity_graph_builder(sample_data):
    transactions, network_observations = sample_data
    builder = EntityGraphBuilder()
    graph = builder.build_from_records(transactions, network_observations)

    assert graph.number_of_nodes() > 0
    assert graph.number_of_edges() > 0

    stats = builder.get_stats()
    assert stats["total_nodes"] > 0
    assert "wallet" in stats["node_types"]
    assert "transaction" in stats["node_types"]
    assert "ip" in stats["node_types"]
    assert "SPENT_FROM" in stats["edge_types"]
    assert "SENT_TO" in stats["edge_types"]

    cyto = builder.to_cytoscape_json()
    assert "elements" in cyto
    assert len(cyto["elements"]["nodes"]) == stats["total_nodes"]


def test_feature_engine(sample_data):
    transactions, network_observations = sample_data
    builder = EntityGraphBuilder()
    graph = builder.build_from_records(transactions, network_observations)

    tx_df = FeatureEngine.compute_transaction_features(transactions)
    assert not tx_df.empty
    assert "fee_ratio" in tx_df.columns
    assert len(tx_df) == len(transactions)

    wallet_df = FeatureEngine.compute_wallet_features(transactions, network_observations)
    assert not wallet_df.empty
    assert "fan_out" in wallet_df.columns
    assert "fan_in" in wallet_df.columns
    assert "entity_id" in wallet_df.columns

    net_df = FeatureEngine.compute_network_features(network_observations)
    assert not net_df.empty

    graph_df = FeatureEngine.compute_graph_features(graph)
    assert not graph_df.empty
    assert "pagerank" in graph_df.columns

    ml_matrix, cols = FeatureEngine.build_ml_feature_matrix(wallet_df, graph_df)
    assert not ml_matrix.empty
    assert len(cols) > 0
    # No NaNs or Infs
    assert not ml_matrix[cols].isna().any().any()


def test_isolation_forest_detector(sample_data):
    transactions, network_observations = sample_data
    builder = EntityGraphBuilder()
    graph = builder.build_from_records(transactions, network_observations)

    wallet_df = FeatureEngine.compute_wallet_features(transactions, network_observations)
    graph_df = FeatureEngine.compute_graph_features(graph)
    ml_matrix, cols = FeatureEngine.build_ml_feature_matrix(wallet_df, graph_df)

    iso = IsolationForestDetector(n_estimators=50, random_state=42)
    scored = iso.fit_predict(ml_matrix, cols)

    assert "anomaly_score" in scored.columns
    assert (scored["anomaly_score"] >= 0.0).all()
    assert (scored["anomaly_score"] <= 1.0).all()

    deviations = iso.get_feature_importances(scored, cols)
    assert isinstance(deviations, dict)


def test_behavior_rules_detector(sample_data):
    transactions, _ = sample_data
    wallet_df = FeatureEngine.compute_wallet_features(transactions)
    detector = BehaviorRulesDetector(high_fan_out_threshold=10)

    # Disperse wallet has 15 outputs -> should trigger R02 High Fan Out
    disperse_row = wallet_df[wallet_df["wallet_address"] == "W_DISPERSE"].iloc[0]
    rules = detector.evaluate_wallet(disperse_row)

    triggered_ids = [r["rule_id"] for r in rules if r.get("triggered")]
    assert "RULE_HIGH_FAN_OUT" in triggered_ids

    b_score = detector.compute_behavior_score(rules)
    assert 0.0 < b_score <= 1.0


def test_graph_signals_and_network_signals(sample_data):
    transactions, network_observations = sample_data
    builder = EntityGraphBuilder()
    graph = builder.build_from_records(transactions, network_observations)

    wallet_df = FeatureEngine.compute_wallet_features(transactions, network_observations)
    graph_df = FeatureEngine.compute_graph_features(graph)
    net_df = FeatureEngine.compute_network_features(network_observations)

    g_det = GraphSignalsDetector()
    scored_g = g_det.evaluate(wallet_df, graph_df)
    assert "graph_score" in scored_g.columns
    assert (scored_g["graph_score"] >= 0.0).all()

    n_det = NetworkSignalsDetector()
    scored_n = n_det.evaluate(wallet_df, net_df)
    assert "network_score" in scored_n.columns
    assert "correlation_strength" in scored_n.columns

    port_anomalies = n_det.detect_network_port_anomalies(network_observations)
    assert len(port_anomalies) == 1
    assert port_anomalies[0]["dst_port"] == 9999


def test_priority_fusion_scorer():
    scorer = PriorityFusionScorer()

    score, tier, components = scorer.compute_priority(
        anomaly_score=0.9,
        behavior_score=0.8,
        graph_score=0.5,
        network_score=0.4,
    )
    # 0.4*0.9 + 0.3*0.8 + 0.2*0.5 + 0.1*0.4 = 0.36 + 0.24 + 0.10 + 0.04 = 0.74 -> 74.0
    assert score == 74.0
    assert tier == "HIGH"
    assert components["anomaly_score"] == 0.9


def test_explainer_and_evidence():
    ev_mgr = EvidenceManager()
    evidence_pack = ev_mgr.compile_evidence_pack(
        entity_id="wallet:W_TEST",
        wallet_features={"fan_out": 25},
        case_medians={"fan_out": 2},
        triggered_rules=[
            {
                "rule_id": "RULE_HIGH_FAN_OUT",
                "observed_value": 25,
                "threshold": 10,
                "unit": "outputs",
                "description": "Fan out 25 exceeded 10",
                "source_record_ids": ["tx-1"],
            }
        ],
        top_deviations=[{"feature": "fan_out", "value": 25, "baseline": 2, "deviation": 5.0}],
        source_record_ids=["tx-1", "net-1"],
    )
    assert len(evidence_pack) >= 2
    assert all("evidence_id" in ev for ev in evidence_pack)

    explainer = DeterministicExplainer()
    explanation = explainer.explain(
        entity_id="wallet:W_TEST",
        priority_score=75.0,
        severity="HIGH",
        score_components={"anomaly_score": 0.8, "behavior_score": 0.7, "graph_score": 0.5, "network_score": 0.2},
        triggered_rules=[{"rule_id": "RULE_HIGH_FAN_OUT", "observed_value": 25, "threshold": 10, "unit": "outputs", "description": "Fan out 25 exceeded 10"}],
        evidence_pack=evidence_pack,
        top_deviations=[{"feature": "fan_out", "value": 25, "baseline": 2, "deviation": 5.0}],
    )

    assert explanation["severity"] == "HIGH"
    assert len(explanation["top_reasons"]) > 0
    assert "summary_text" in explanation


def test_report_generator():
    alerts = [
        {
            "entity_id": "wallet:W_TEST",
            "severity": "HIGH",
            "priority_score": 75.0,
            "score_components": {"anomaly_score": 0.8, "behavior_score": 0.7, "graph_score": 0.5, "network_score": 0.2},
            "top_reasons": [{"text": "High Fan-out dispersal"}],
            "evidence_pack": [{"feature": "fan_out", "source_record_ids": ["tx-001"]}],
        }
    ]
    graph_stats = {"total_nodes": 10, "total_edges": 15, "connected_components": 1, "density": 0.15}
    config = {"weights": {"anomaly": 0.4, "behavior": 0.3, "graph": 0.2, "network": 0.1}}

    json_rep = ReportGenerator.generate_json_report("case_1", "run_1", alerts, graph_stats, config)
    assert json_rep["case_id"] == "case_1"
    assert json_rep["alert_summary"]["total_alerts"] == 1

    md_rep = ReportGenerator.generate_markdown_report(json_rep)
    assert "# Case Investigation Report: case_1" in md_rep
    assert "HIGH" in md_rep
