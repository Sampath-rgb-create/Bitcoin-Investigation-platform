"""
Unit tests for correlation and GeoIP services.
"""
from datetime import datetime, timezone, timedelta
from backend.app.services.correlation import CorrelationEngine
from backend.app.services.geoip import GeoIPService


def test_correlation_exact_txid():
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    txs = [
        {"record_id": "tx1", "txid": "hash_aaa", "timestamp": now},
        {"record_id": "tx2", "txid": "hash_bbb", "timestamp": now}
    ]
    net = [
        {"record_id": "net1", "txid": "hash_aaa", "timestamp": now + timedelta(seconds=2), "src_ip": "10.0.0.1"},
        {"record_id": "net2", "txid": "hash_ccc", "timestamp": now, "src_ip": "10.0.0.2"}
    ]

    engine = CorrelationEngine(allow_temporal=False)
    links, status_map = engine.correlate(txs, net)

    assert len(links) == 1
    link = links[0]
    assert link["network_record_id"] == "net1"
    assert link["transaction_record_id"] == "tx1"
    assert link["method"] == "exact_txid"
    assert link["basis"] == "shared_txid"
    assert link["time_delta_ms"] == 2000

    assert status_map["hash_aaa"] == "exactly_correlated"
    assert status_map["hash_bbb"] == "uncorrelated"


def test_correlation_temporal_heuristic():
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    txs = [
        {"record_id": "tx1", "txid": "hash_aaa", "timestamp": now}
    ]
    net_without_txid = [
        {"record_id": "net1", "txid": None, "timestamp": now + timedelta(seconds=15), "src_ip": "10.0.0.1"}
    ]

    # Enabled
    engine = CorrelationEngine(allow_temporal=True, window_seconds=30)
    links, status_map = engine.correlate(txs, net_without_txid)

    assert len(links) == 1
    assert links[0]["method"] == "temporal_window"
    assert links[0]["basis"] == "heuristic"
    assert links[0]["time_delta_ms"] == 15000
    assert status_map["hash_aaa"] == "partially_correlated"


def test_correlation_strength():
    strength = CorrelationEngine.calculate_correlation_strength(matched_observations=5, transaction_count=10)
    assert strength == 0.5
    assert CorrelationEngine.calculate_correlation_strength(20, 10) == 1.0


def test_geoip_service_graceful_fallback():
    # Test fallback with non-existent db path
    geo = GeoIPService(db_path="d:/does_not_exist/GeoLite2.mmdb")
    res = geo.lookup("8.8.8.8")
    assert res["country"] is None
    assert res["geo_status"] in ("db_not_found", "unavailable", "library_missing")
    assert "Observed IP was geolocated approximately" in res["disclaimer"]
