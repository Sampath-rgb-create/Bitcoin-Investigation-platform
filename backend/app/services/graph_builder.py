"""
Entity Graph Builder for Bitcoin Investigation Platform.

Constructs a NetworkX entity graph using:
- Nodes:
    - 'wallet' (e.g. 'wallet:W123')
    - 'transaction' (e.g. 'transaction:tx_abc123')
    - 'ip' (e.g. 'ip:203.0.113.10')
    - 'asn' (e.g. 'asn:AS64500')
    - 'country' (e.g. 'country:US')
- Edges:
    - 'SPENT_FROM': wallet -> transaction (or transaction -> wallet depending on convention, PROTOTYPE specifies INPUT_TO/SPENT_FROM wallet -> transaction)
    - 'SENT_TO': transaction -> wallet
    - 'RELAYED_BY' / 'OBSERVED': ip -> transaction
    - 'HOSTED_IN' / 'BELONGS_TO_ASN': ip -> asn
    - 'LOCATED_IN' / 'GEOLOCATED_TO': ip -> country

Serializes graph to Cytoscape/D3 compatible graph.json and summary graph_stats.json.
"""

from typing import Dict, List, Any, Optional, Set
import json
import logging
from pathlib import Path
import networkx as nx

logger = logging.getLogger(__name__)


class EntityGraphBuilder:
    """
    Constructs and exports heterogeneous entity graphs for Bitcoin and network telemetry.
    """

    def __init__(self):
        # We use a directed multigraph or directed graph
        self.graph = nx.DiGraph()

    def add_wallet_node(self, wallet_address: str, **attributes) -> str:
        """Ensure wallet node exists."""
        node_id = f"wallet:{wallet_address}"
        if not self.graph.has_node(node_id):
            self.graph.add_node(
                node_id,
                type="wallet",
                label=wallet_address,
                attributes={"address": wallet_address, **attributes},
            )
        else:
            self.graph.nodes[node_id]["attributes"].update(attributes)
        return node_id

    def add_transaction_node(
        self,
        txid: str,
        timestamp: Optional[str] = None,
        fee: Optional[float] = None,
        total_input: Optional[float] = None,
        total_output: Optional[float] = None,
        script_type: Optional[str] = None,
        source_record_id: Optional[str] = None,
        **attributes,
    ) -> str:
        """Ensure transaction node exists."""
        node_id = f"transaction:{txid}"
        tx_attrs = {
            "txid": txid,
            "timestamp": timestamp,
            "fee": fee,
            "total_input": total_input,
            "total_output": total_output,
            "script_type": script_type,
            "source_record_id": source_record_id,
            **attributes,
        }
        if not self.graph.has_node(node_id):
            self.graph.add_node(
                node_id,
                type="transaction",
                label=txid[:8] + "..." if len(txid) > 12 else txid,
                attributes=tx_attrs,
            )
        else:
            self.graph.nodes[node_id]["attributes"].update(
                {k: v for k, v in tx_attrs.items() if v is not None}
            )
        return node_id

    def add_ip_node(
        self,
        ip: str,
        asn: Optional[str] = None,
        country: Optional[str] = None,
        **attributes,
    ) -> str:
        """Ensure IP node exists."""
        node_id = f"ip:{ip}"
        ip_attrs = {"ip": ip, "asn": asn, "country": country, **attributes}
        if not self.graph.has_node(node_id):
            self.graph.add_node(
                node_id,
                type="ip",
                label=ip,
                attributes=ip_attrs,
            )
        else:
            self.graph.nodes[node_id]["attributes"].update(
                {k: v for k, v in ip_attrs.items() if v is not None}
            )
        return node_id

    def add_asn_node(self, asn: str, **attributes) -> str:
        """Ensure ASN node exists."""
        node_id = f"asn:{asn}"
        if not self.graph.has_node(node_id):
            self.graph.add_node(
                node_id,
                type="asn",
                label=asn,
                attributes={"asn": asn, **attributes},
            )
        return node_id

    def add_country_node(self, country_code: str, **attributes) -> str:
        """Ensure Country node exists."""
        node_id = f"country:{country_code}"
        if not self.graph.has_node(node_id):
            self.graph.add_node(
                node_id,
                type="country",
                label=country_code,
                attributes={"country": country_code, **attributes},
            )
        return node_id

    def add_edge(
        self,
        source: str,
        target: str,
        edge_type: str,
        basis: str = "exact",
        source_record_ids: Optional[List[str]] = None,
        weight: float = 1.0,
        amount: Optional[float] = None,
        timestamp: Optional[str] = None,
        **attributes,
    ):
        """
        Add typed directed edge. If edge already exists, update/aggregate properties.
        Edge types:
        - SPENT_FROM / INPUT_TO: wallet -> transaction
        - SENT_TO / OUTPUT_TO: transaction -> wallet
        - RELAYED_BY / OBSERVED: ip -> transaction
        - HOSTED_IN / BELONGS_TO_ASN: ip -> asn
        - LOCATED_IN / GEOLOCATED_TO: ip -> country
        """
        src_ids = list(source_record_ids or [])
        edge_id = f"edge:{source}->{target}:{edge_type}"

        if self.graph.has_edge(source, target):
            existing = self.graph[source][target]
            # If same edge type, aggregate
            if existing.get("type") == edge_type:
                existing["weight"] = existing.get("weight", 1.0) + weight
                existing_records = set(existing.get("source_record_ids", []))
                existing_records.update(src_ids)
                existing["source_record_ids"] = sorted(list(existing_records))
                if timestamp:
                    if not existing.get("first_seen") or timestamp < existing["first_seen"]:
                        existing["first_seen"] = timestamp
                    if not existing.get("last_seen") or timestamp > existing["last_seen"]:
                        existing["last_seen"] = timestamp
                if amount is not None:
                    existing["amount"] = (existing.get("amount") or 0.0) + amount
                return

        self.graph.add_edge(
            source,
            target,
            id=edge_id,
            type=edge_type,
            basis=basis,
            source_record_ids=src_ids,
            weight=weight,
            amount=amount,
            first_seen=timestamp,
            last_seen=timestamp,
            **attributes,
        )

    def build_from_records(
        self,
        transactions: List[Dict[str, Any]],
        network_observations: Optional[List[Dict[str, Any]]] = None,
        correlations: Optional[List[Dict[str, Any]]] = None,
    ) -> nx.DiGraph:
        """
        Construct entity graph from canonical transactions, network observations, and correlations.
        """
        # 1. Process transactions
        for tx in transactions:
            txid = tx.get("txid")
            if not txid:
                continue

            record_id = tx.get("record_id")
            ts = tx.get("timestamp")
            fee = float(tx.get("fee", 0.0) or 0.0)
            in_addrs = tx.get("input_addresses") or []
            out_addrs = tx.get("output_addresses") or []
            in_amts = tx.get("input_amounts") or []
            out_amts = tx.get("output_amounts") or []
            script_type = tx.get("script_type")

            total_in = sum(float(a) for a in in_amts) if in_amts else 0.0
            total_out = sum(float(a) for a in out_amts) if out_amts else 0.0

            tx_node = self.add_transaction_node(
                txid=txid,
                timestamp=ts,
                fee=fee,
                total_input=total_in,
                total_output=total_out,
                script_type=script_type,
                source_record_id=record_id,
            )

            # Input addresses -> SPENT_FROM / INPUT_TO -> Transaction
            for idx, addr in enumerate(in_addrs):
                amt = float(in_amts[idx]) if idx < len(in_amts) else 0.0
                wallet_node = self.add_wallet_node(addr)
                self.add_edge(
                    source=wallet_node,
                    target=tx_node,
                    edge_type="SPENT_FROM",
                    basis="tx_input",
                    source_record_ids=[record_id] if record_id else [],
                    weight=1.0,
                    amount=amt,
                    timestamp=ts,
                )

            # Transaction -> SENT_TO / OUTPUT_TO -> Output addresses
            for idx, addr in enumerate(out_addrs):
                amt = float(out_amts[idx]) if idx < len(out_amts) else 0.0
                wallet_node = self.add_wallet_node(addr)
                self.add_edge(
                    source=tx_node,
                    target=wallet_node,
                    edge_type="SENT_TO",
                    basis="tx_output",
                    source_record_ids=[record_id] if record_id else [],
                    weight=1.0,
                    amount=amt,
                    timestamp=ts,
                )

            # If combined record contains IP / Geo / ASN directly:
            src_ip = tx.get("src_ip")
            if src_ip:
                asn = tx.get("asn")
                country = tx.get("geo_country")
                ip_node = self.add_ip_node(src_ip, asn=asn, country=country)
                self.add_edge(
                    source=ip_node,
                    target=tx_node,
                    edge_type="RELAYED_BY",
                    basis="combined_row",
                    source_record_ids=[record_id] if record_id else [],
                    timestamp=ts,
                )
                if asn:
                    asn_node = self.add_asn_node(str(asn))
                    self.add_edge(ip_node, asn_node, "HOSTED_IN", basis="asn_lookup")
                if country:
                    country_node = self.add_country_node(str(country))
                    self.add_edge(ip_node, country_node, "LOCATED_IN", basis="geoip")

        # 2. Process external network observations
        if network_observations:
            for obs in network_observations:
                net_rec_id = obs.get("record_id")
                txid = obs.get("txid")
                src_ip = obs.get("src_ip")
                ts = obs.get("timestamp")
                asn = obs.get("asn")
                country = obs.get("geo_country")

                if src_ip:
                    ip_node = self.add_ip_node(src_ip, asn=asn, country=country)
                    if asn:
                        asn_node = self.add_asn_node(str(asn))
                        self.add_edge(ip_node, asn_node, "HOSTED_IN", basis="asn_lookup")
                    if country:
                        country_node = self.add_country_node(str(country))
                        self.add_edge(ip_node, country_node, "LOCATED_IN", basis="geoip")

                    if txid:
                        tx_node = f"transaction:{txid}"
                        if self.graph.has_node(tx_node):
                            self.add_edge(
                                source=ip_node,
                                target=tx_node,
                                edge_type="RELAYED_BY",
                                basis="exact_txid",
                                source_record_ids=[net_rec_id] if net_rec_id else [],
                                timestamp=ts,
                            )

        # 3. Process explicit correlations if provided
        if correlations:
            for corr in correlations:
                txid = corr.get("txid")
                src_ip = corr.get("src_ip")
                basis = corr.get("basis", "correlated")
                net_rec_id = corr.get("net_record_id")
                ts = corr.get("timestamp")

                if txid and src_ip:
                    ip_node = self.add_ip_node(src_ip)
                    tx_node = f"transaction:{txid}"
                    if self.graph.has_node(tx_node):
                        self.add_edge(
                            source=ip_node,
                            target=tx_node,
                            edge_type="RELAYED_BY",
                            basis=basis,
                            source_record_ids=[net_rec_id] if net_rec_id else [],
                            timestamp=ts,
                        )

        return self.graph

    def get_stats(self) -> Dict[str, Any]:
        """Compute summary statistics for the graph."""
        node_counts: Dict[str, int] = {}
        for _, data in self.graph.nodes(data=True):
            ntype = data.get("type", "unknown")
            node_counts[ntype] = node_counts.get(ntype, 0) + 1

        edge_counts: Dict[str, int] = {}
        for _, _, data in self.graph.edges(data=True):
            etype = data.get("type", "unknown")
            edge_counts[etype] = edge_counts.get(etype, 0) + 1

        num_nodes = self.graph.number_of_nodes()
        num_edges = self.graph.number_of_edges()

        # Connected components (undirected view)
        undirected = self.graph.to_undirected()
        num_components = (
            nx.number_connected_components(undirected) if num_nodes > 0 else 0
        )

        return {
            "total_nodes": num_nodes,
            "total_edges": num_edges,
            "node_types": node_counts,
            "edge_types": edge_counts,
            "connected_components": num_components,
            "density": nx.density(self.graph) if num_nodes > 1 else 0.0,
        }

    def to_cytoscape_json(self) -> Dict[str, Any]:
        """Convert graph to Cytoscape.js / D3 compatible JSON dictionary."""
        from datetime import datetime
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            clean_attrs = {}
            for k, v in data.get("attributes", {}).items():
                if isinstance(v, datetime):
                    clean_attrs[k] = v.isoformat()
                else:
                    clean_attrs[k] = v

            nodes.append(
                {
                    "data": {
                        "id": node_id,
                        "label": data.get("label", node_id),
                        "type": data.get("type", "unknown"),
                        **clean_attrs,
                    }
                }
            )

        edges = []
        for src, dst, data in self.graph.edges(data=True):
            f_seen = data.get("first_seen")
            if isinstance(f_seen, datetime):
                f_seen = f_seen.isoformat()
            l_seen = data.get("last_seen")
            if isinstance(l_seen, datetime):
                l_seen = l_seen.isoformat()

            edges.append(
                {
                    "data": {
                        "id": data.get("id", f"{src}->{dst}"),
                        "source": src,
                        "target": dst,
                        "type": data.get("type", "unknown"),
                        "basis": data.get("basis", ""),
                        "weight": data.get("weight", 1.0),
                        "amount": data.get("amount"),
                        "first_seen": f_seen,
                        "last_seen": l_seen,
                        "source_record_ids": data.get("source_record_ids", []),
                    }
                }
            )

        return {
            "elements": {
                "nodes": nodes,
                "edges": edges,
            },
            "stats": self.get_stats(),
        }

    def export_files(self, output_dir: str or Path) -> Dict[str, str]:
        """
        Serialize graph to graph.json and graph_stats.json in the specified directory.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        graph_file = out_path / "graph.json"
        stats_file = out_path / "graph_stats.json"

        cyto_data = self.to_cytoscape_json()
        stats_data = cyto_data["stats"]

        with open(graph_file, "w", encoding="utf-8") as f:
            json.dump(cyto_data, f, indent=2, default=str)

        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats_data, f, indent=2, default=str)

        return {
            "graph_json": str(graph_file),
            "graph_stats_json": str(stats_file),
        }
