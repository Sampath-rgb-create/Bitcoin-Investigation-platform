"""
Unit tests for EntityGraphBuilder.
"""
import pytest
from backend.app.services.graph_builder import EntityGraphBuilder


def test_entity_graph_builder_structure():
    builder = EntityGraphBuilder()
    txs = [
        {
            "record_id": "tx1",
            "timestamp": "2026-01-01T12:00:00Z",
            "txid": "hash001",
            "input_addresses": ["W_SRC_1", "W_SRC_2"],
            "input_amounts": [2.0, 3.0],
            "output_addresses": ["W_DST_1"],
            "output_amounts": [4.99],
            "fee": 0.01,
            "src_ip": "198.51.100.1",
            "asn": "AS64500",
            "geo_country": "US",
        }
    ]

    G = builder.build_from_records(txs)

    # Validate node types
    assert G.has_node("wallet:W_SRC_1")
    assert G.has_node("wallet:W_SRC_2")
    assert G.has_node("wallet:W_DST_1")
    assert G.has_node("transaction:hash001")
    assert G.has_node("ip:198.51.100.1")
    assert G.has_node("asn:AS64500")
    assert G.has_node("country:US")

    # Validate edge types
    assert G.has_edge("wallet:W_SRC_1", "transaction:hash001")
    assert G["wallet:W_SRC_1"]["transaction:hash001"]["type"] == "SPENT_FROM"

    assert G.has_edge("transaction:hash001", "wallet:W_DST_1")
    assert G["transaction:hash001"]["wallet:W_DST_1"]["type"] == "SENT_TO"

    assert G.has_edge("ip:198.51.100.1", "transaction:hash001")
    assert G["ip:198.51.100.1"]["transaction:hash001"]["type"] == "RELAYED_BY"

    assert G.has_edge("ip:198.51.100.1", "asn:AS64500")
    assert G["ip:198.51.100.1"]["asn:AS64500"]["type"] == "HOSTED_IN"

    assert G.has_edge("ip:198.51.100.1", "country:US")
    assert G["ip:198.51.100.1"]["country:US"]["type"] == "LOCATED_IN"

    # Validate Cytoscape & Stats
    cyto = builder.to_cytoscape_json()
    assert "elements" in cyto
    assert len(cyto["elements"]["nodes"]) == 7
    assert len(cyto["elements"]["edges"]) == 6

    stats = builder.get_stats()
    assert stats["total_nodes"] == 7
    assert stats["total_edges"] == 6
    assert stats["node_types"]["wallet"] == 3
    assert stats["node_types"]["transaction"] == 1
    assert stats["node_types"]["ip"] == 1
    assert stats["node_types"]["asn"] == 1
    assert stats["node_types"]["country"] == 1
