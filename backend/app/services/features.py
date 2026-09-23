"""
Feature Extraction Engine for Bitcoin Investigation Platform.

Computes features at:
- Transaction level:
    - input_count, output_count, total_input, total_output, fee, fee_ratio,
      input_output_ratio, transaction_value
- Wallet level:
    - transaction_count, incoming_count, outgoing_count, total_incoming, total_outgoing,
      average_tx_value, median_tx_value, unique_counterparties, fan_in, fan_out,
      transaction_rate, median_time_gap, wallet_lifetime_seconds,
      connected_ip_count, unique_country_count, unique_asn_count
- Network level:
    - network_observation_count, unique_src_ip_count, unique_dst_ip_count,
      unique_src_port_count, unique_dst_port_count, unique_country_count,
      unique_asn_count, observation_rate, median_network_time_gap
- Graph level (from NetworkX entity graph):
    - degree, in_degree, out_degree, weighted_degree, neighbor_count, pagerank,
      community_id, community_size, community_density, short_cycle_count

Handles missing values and provides tabular feature matrices for ML/detection.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timezone
import math
import numpy as np
import pandas as pd
import networkx as nx


def parse_iso_ts(ts_str: Optional[str]) -> Optional[float]:
    """Parse ISO8601 timestamp string to POSIX epoch seconds."""
    if not ts_str:
        return None
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.timestamp()
    except Exception:
        return None


class FeatureEngine:
    """
    Computes multi-dimensional feature representations for transactions, wallets,
    network activity, and entity graph topologies.
    """

    def __init__(self):
        pass

    @staticmethod
    def compute_transaction_features(transactions: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Compute transaction-level tabular features.
        """
        rows = []
        for tx in transactions:
            txid = tx.get("txid", "")
            rec_id = tx.get("record_id", "")
            ts = parse_iso_ts(tx.get("timestamp"))

            in_addrs = tx.get("input_addresses") or []
            out_addrs = tx.get("output_addresses") or []
            in_amts = [float(x) for x in (tx.get("input_amounts") or []) if x is not None]
            out_amts = [float(x) for x in (tx.get("output_amounts") or []) if x is not None]

            in_count = len(in_addrs)
            out_count = len(out_addrs)
            tot_in = sum(in_amts) if in_amts else 0.0
            tot_out = sum(out_amts) if out_amts else 0.0
            fee = float(tx.get("fee", 0.0) or 0.0)

            tx_val = tot_out
            fee_ratio = (fee / tot_in) if tot_in > 0 else 0.0
            in_out_ratio = (out_count / in_count) if in_count > 0 else float(out_count)

            # Shannon entropy of output distribution
            output_entropy = 0.0
            if tot_out > 0 and len(out_amts) > 1:
                for a in out_amts:
                    p = a / tot_out
                    if p > 0:
                        output_entropy -= p * math.log2(p)

            rows.append(
                {
                    "txid": txid,
                    "record_id": rec_id,
                    "timestamp": ts,
                    "input_count": in_count,
                    "output_count": out_count,
                    "in_degree": in_count,
                    "out_degree": out_count,
                    "total_input": tot_in,
                    "total_output": tot_out,
                    "transaction_value": tx_val,
                    "fee": fee,
                    "fee_ratio": fee_ratio,
                    "input_output_ratio": in_out_ratio,
                    "output_entropy": round(output_entropy, 4),
                    "dust_outputs_count": sum(1 for val in out_amts if val < 0.0001),
                }
            )

        if not rows:
            return pd.DataFrame(
                columns=[
                    "txid",
                    "record_id",
                    "timestamp",
                    "input_count",
                    "output_count",
                    "in_degree",
                    "out_degree",
                    "total_input",
                    "total_output",
                    "transaction_value",
                    "fee",
                    "fee_ratio",
                    "input_output_ratio",
                    "output_entropy",
                    "dust_outputs_count",
                ]
            )
        return pd.DataFrame(rows)

    @staticmethod
    def compute_wallet_features(
        transactions: List[Dict[str, Any]],
        network_observations: Optional[List[Dict[str, Any]]] = None,
    ) -> pd.DataFrame:
        """
        Compute wallet-level behavioral and temporal features.
        """
        # Aggregate wallet history
        wallets: Dict[str, Dict[str, Any]] = {}

        def get_wallet(addr: str) -> Dict[str, Any]:
            if addr not in wallets:
                wallets[addr] = {
                    "address": addr,
                    "entity_id": f"wallet:{addr}",
                    "tx_timestamps": [],
                    "incoming_txids": set(),
                    "outgoing_txids": set(),
                    "incoming_amts": [],
                    "outgoing_amts": [],
                    "counterparties": set(),
                    "incoming_counterparties": set(),
                    "outgoing_counterparties": set(),
                    "source_record_ids": set(),
                    "connected_ips": set(),
                    "unique_countries": set(),
                    "unique_asns": set(),
                }
            return wallets[addr]

        # Map txid to associated network observations
        tx_net_map: Dict[str, List[Dict[str, Any]]] = {}
        if network_observations:
            for obs in network_observations:
                t = obs.get("txid")
                if t:
                    tx_net_map.setdefault(t, []).append(obs)

        for tx in transactions:
            txid = tx.get("txid", "")
            rec_id = tx.get("record_id")
            ts = parse_iso_ts(tx.get("timestamp"))

            in_addrs = tx.get("input_addresses") or []
            out_addrs = tx.get("output_addresses") or []
            in_amts = [float(x) for x in (tx.get("input_amounts") or []) if x is not None]
            out_amts = [float(x) for x in (tx.get("output_amounts") or []) if x is not None]

            # Net info for this tx
            net_items = tx_net_map.get(txid, [])
            # Also check direct fields on tx (combined row)
            if tx.get("src_ip"):
                net_items.append(
                    {
                        "src_ip": tx.get("src_ip"),
                        "geo_country": tx.get("geo_country"),
                        "asn": tx.get("asn"),
                    }
                )

            # Inbound / Outbound records
            for idx, src_addr in enumerate(in_addrs):
                w = get_wallet(src_addr)
                w["outgoing_txids"].add(txid)
                if rec_id:
                    w["source_record_ids"].add(rec_id)
                if ts is not None:
                    w["tx_timestamps"].append(ts)
                amt = in_amts[idx] if idx < len(in_amts) else 0.0
                w["outgoing_amts"].append(amt)
                for dst_addr in out_addrs:
                    if dst_addr != src_addr:
                        w["counterparties"].add(dst_addr)
                        w["outgoing_counterparties"].add(dst_addr)

                # Attach network telemetry to sender wallet
                for n in net_items:
                    if n.get("src_ip"):
                        w["connected_ips"].add(n["src_ip"])
                    if n.get("geo_country"):
                        w["unique_countries"].add(n["geo_country"])
                    if n.get("asn"):
                        w["unique_asns"].add(n["asn"])

            for idx, dst_addr in enumerate(out_addrs):
                w = get_wallet(dst_addr)
                w["incoming_txids"].add(txid)
                if rec_id:
                    w["source_record_ids"].add(rec_id)
                if ts is not None:
                    w["tx_timestamps"].append(ts)
                amt = out_amts[idx] if idx < len(out_amts) else 0.0
                w["incoming_amts"].append(amt)
                for src_addr in in_addrs:
                    if src_addr != dst_addr:
                        w["counterparties"].add(src_addr)
                        w["incoming_counterparties"].add(src_addr)

                # Output wallets also get associated network context
                for n in net_items:
                    if n.get("src_ip"):
                        w["connected_ips"].add(n["src_ip"])
                    if n.get("geo_country"):
                        w["unique_countries"].add(n["geo_country"])
                    if n.get("asn"):
                        w["unique_asns"].add(n["asn"])

        # Compute summary metrics per wallet
        wallet_rows = []
        for addr, data in wallets.items():
            in_tx_cnt = len(data["incoming_txids"])
            out_tx_cnt = len(data["outgoing_txids"])
            all_tx_cnt = len(data["incoming_txids"].union(data["outgoing_txids"]))
            tot_in = sum(data["incoming_amts"])
            tot_out = sum(data["outgoing_amts"])
            all_amts = data["incoming_amts"] + data["outgoing_amts"]
            avg_val = float(np.mean(all_amts)) if all_amts else 0.0
            med_val = float(np.median(all_amts)) if all_amts else 0.0

            # Repeated value count (common AML structuring signal)
            val_counts: Dict[float, int] = {}
            for a in data["outgoing_amts"]:
                rounded = round(a, 4)
                val_counts[rounded] = val_counts.get(rounded, 0) + 1
            max_repeated_value_count = max(val_counts.values()) if val_counts else 0

            # Temporal features
            timestamps = sorted(data["tx_timestamps"])
            if len(timestamps) > 1:
                gaps = [timestamps[i] - timestamps[i - 1] for i in range(1, len(timestamps))]
                med_gap = float(np.median(gaps))
                lifetime = float(timestamps[-1] - timestamps[0])
                tx_rate = float(len(timestamps) / lifetime) if lifetime > 0 else float(len(timestamps))
            elif len(timestamps) == 1:
                med_gap = 0.0
                lifetime = 0.0
                tx_rate = 1.0
            else:
                med_gap = 0.0
                lifetime = 0.0
                tx_rate = 0.0

            fan_in = max(len(data["incoming_counterparties"]), in_tx_cnt)
            fan_out = max(len(data["outgoing_counterparties"]), out_tx_cnt)
            in_degree = in_tx_cnt
            out_degree = out_tx_cnt
            fan_out_ratio = (out_degree / in_degree) if in_degree > 0 else float(out_degree)
            total_volume = tot_in + tot_out
            address_reuse = all_tx_cnt > 1
            counterparties_cnt = len(data["counterparties"])

            # Dust count
            dust_cnt = sum(1 for a in data["incoming_amts"] if a < 0.0001)

            wallet_rows.append(
                {
                    "wallet_address": addr,
                    "entity_id": data["entity_id"],
                    "transaction_count": all_tx_cnt,
                    "incoming_transaction_count": in_tx_cnt,
                    "outgoing_transaction_count": out_tx_cnt,
                    "in_degree": in_degree,
                    "out_degree": out_degree,
                    "fan_in": fan_in,
                    "fan_out": fan_out,
                    "fan_out_ratio": fan_out_ratio,
                    "total_incoming": tot_in,
                    "total_outgoing": tot_out,
                    "total_volume": total_volume,
                    "net_balance_change": tot_in - tot_out,
                    "address_reuse": 1 if address_reuse else 0,
                    "average_transaction_value": avg_val,
                    "median_transaction_value": med_val,
                    "unique_counterparties": counterparties_cnt,
                    "max_repeated_value_count": max_repeated_value_count,
                    "dust_incoming_count": dust_cnt,
                    "transaction_rate": tx_rate,
                    "median_time_gap": med_gap,
                    "wallet_lifetime_seconds": lifetime,
                    "connected_ip_count": len(data["connected_ips"]),
                    "unique_country_count": len(data["unique_countries"]),
                    "unique_asn_count": len(data["unique_asns"]),
                    "source_record_ids": sorted(list(data["source_record_ids"])),
                }
            )

        if not wallet_rows:
            return pd.DataFrame(
                columns=[
                    "wallet_address",
                    "entity_id",
                    "transaction_count",
                    "incoming_transaction_count",
                    "outgoing_transaction_count",
                    "in_degree",
                    "out_degree",
                    "fan_in",
                    "fan_out",
                    "fan_out_ratio",
                    "total_incoming",
                    "total_outgoing",
                    "total_volume",
                    "net_balance_change",
                    "address_reuse",
                    "average_transaction_value",
                    "median_transaction_value",
                    "unique_counterparties",
                    "max_repeated_value_count",
                    "dust_incoming_count",
                    "transaction_rate",
                    "median_time_gap",
                    "wallet_lifetime_seconds",
                    "connected_ip_count",
                    "unique_country_count",
                    "unique_asn_count",
                    "source_record_ids",
                ]
            )

        return pd.DataFrame(wallet_rows)

    @staticmethod
    def compute_network_features(network_observations: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Compute network-level telemetry features grouped by source IP.
        """
        ip_groups: Dict[str, Dict[str, Any]] = {}

        for obs in network_observations:
            ip = obs.get("src_ip")
            if not ip:
                continue
            rec_id = obs.get("record_id")
            ts = parse_iso_ts(obs.get("timestamp"))
            dst_ip = obs.get("dst_ip")
            src_port = obs.get("src_port")
            dst_port = obs.get("dst_port")
            asn = obs.get("asn")
            country = obs.get("geo_country")
            txid = obs.get("txid")

            if ip not in ip_groups:
                ip_groups[ip] = {
                    "ip": ip,
                    "entity_id": f"ip:{ip}",
                    "record_ids": set(),
                    "timestamps": [],
                    "dst_ips": set(),
                    "src_ports": set(),
                    "dst_ports": set(),
                    "countries": set(),
                    "asns": set(),
                    "txids": set(),
                }

            group = ip_groups[ip]
            if rec_id:
                group["record_ids"].add(rec_id)
            if ts is not None:
                group["timestamps"].append(ts)
            if dst_ip:
                group["dst_ips"].add(dst_ip)
            if src_port is not None:
                group["src_ports"].add(src_port)
            if dst_port is not None:
                group["dst_ports"].add(dst_port)
            if country:
                group["countries"].add(country)
            if asn:
                group["asns"].add(asn)
            if txid:
                group["txids"].add(txid)

        rows = []
        for ip, g in ip_groups.items():
            obs_cnt = len(g["timestamps"])
            timestamps = sorted(g["timestamps"])
            if len(timestamps) > 1:
                gaps = [timestamps[i] - timestamps[i - 1] for i in range(1, len(timestamps))]
                med_gap = float(np.median(gaps))
                lifetime = float(timestamps[-1] - timestamps[0])
                rate = float(obs_cnt / lifetime) if lifetime > 0 else float(obs_cnt)
            elif len(timestamps) == 1:
                med_gap = 0.0
                lifetime = 0.0
                rate = 1.0
            else:
                med_gap = 0.0
                lifetime = 0.0
                rate = 0.0

            rows.append(
                {
                    "ip": ip,
                    "entity_id": g["entity_id"],
                    "network_observation_count": obs_cnt,
                    "unique_dst_ip_count": len(g["dst_ips"]),
                    "unique_src_port_count": len(g["src_ports"]),
                    "unique_dst_port_count": len(g["dst_ports"]),
                    "unique_country_count": len(g["countries"]),
                    "unique_asn_count": len(g["asns"]),
                    "associated_tx_count": len(g["txids"]),
                    "observation_rate": rate,
                    "median_network_time_gap": med_gap,
                    "source_record_ids": sorted(list(g["record_ids"])),
                }
            )

        if not rows:
            return pd.DataFrame(
                columns=[
                    "ip",
                    "entity_id",
                    "network_observation_count",
                    "unique_dst_ip_count",
                    "unique_src_port_count",
                    "unique_dst_port_count",
                    "unique_country_count",
                    "unique_asn_count",
                    "associated_tx_count",
                    "observation_rate",
                    "median_network_time_gap",
                    "source_record_ids",
                ]
            )

        return pd.DataFrame(rows)

    @staticmethod
    def compute_graph_features(graph: nx.DiGraph) -> pd.DataFrame:
        """
        Compute topological metrics for all nodes in the entity graph:
        - degree, in_degree, out_degree
        - PageRank
        - community ID (via Louvain / connected components)
        - community size & density
        - short cycle participation
        """
        if graph.number_of_nodes() == 0:
            return pd.DataFrame(
                columns=[
                    "node_id",
                    "entity_id",
                    "node_type",
                    "degree",
                    "in_degree",
                    "out_degree",
                    "pagerank",
                    "community_id",
                    "community_size",
                    "community_density",
                    "short_cycle_count",
                ]
            )

        # 1. PageRank and Centralities
        try:
            pageranks = nx.pagerank(graph, alpha=0.85, max_iter=200)
        except Exception:
            # Fallback uniform
            uniform = 1.0 / max(graph.number_of_nodes(), 1)
            pageranks = {n: uniform for n in graph.nodes()}

        try:
            degree_centralities = nx.degree_centrality(graph)
        except Exception:
            degree_centralities = {n: 0.0 for n in graph.nodes()}

        # Betweenness centrality (approximate if graph > 500 nodes for high performance)
        try:
            num_nodes = graph.number_of_nodes()
            if num_nodes > 500:
                k_samples = min(100, num_nodes)
                betweenness_centralities = nx.betweenness_centrality(graph, k=k_samples, seed=42)
            else:
                betweenness_centralities = nx.betweenness_centrality(graph)
        except Exception:
            betweenness_centralities = {n: 0.0 for n in graph.nodes()}

        # 2. Communities via undirected connected components or modularity
        undirected = graph.to_undirected()
        community_map: Dict[str, int] = {}
        community_sizes: Dict[int, int] = {}
        community_densities: Dict[int, float] = {}

        try:
            # Use greedy modularity communities if possible
            communities = list(nx.community.greedy_modularity_communities(undirected))
            if not communities:
                communities = list(nx.connected_components(undirected))
        except Exception:
            communities = list(nx.connected_components(undirected))

        for comm_idx, comp in enumerate(communities):
            c_nodes = set(comp)
            c_size = len(c_nodes)
            community_sizes[comm_idx] = c_size
            subg = graph.subgraph(c_nodes)
            c_dens = nx.density(subg) if c_size > 1 else 0.0
            community_densities[comm_idx] = c_dens
            for node in c_nodes:
                community_map[node] = comm_idx

        # 3. Short cycles (length 2-4) with strict iteration cap
        cycle_counts: Dict[str, int] = {n: 0 for n in graph.nodes()}
        try:
            # Strictly bounded cycle exploration to prevent combinatoric explosion
            cycle_iter = 0
            for cycle in nx.simple_cycles(graph):
                cycle_iter += 1
                if 2 <= len(cycle) <= 4:
                    for n in cycle:
                        cycle_counts[n] = cycle_counts.get(n, 0) + 1
                if cycle_iter >= 200 or any(v >= 20 for v in cycle_counts.values()):
                    break
        except Exception:
            pass

        rows = []
        for node_id, data in graph.nodes(data=True):
            ntype = data.get("type", "unknown")
            deg = graph.degree(node_id)
            in_deg = graph.in_degree(node_id) if hasattr(graph, "in_degree") else 0
            out_deg = graph.out_degree(node_id) if hasattr(graph, "out_degree") else 0
            pr = pageranks.get(node_id, 0.0)
            deg_cent = degree_centralities.get(node_id, 0.0)
            btw_cent = betweenness_centralities.get(node_id, 0.0)
            comm_id = community_map.get(node_id, 0)
            comm_size = community_sizes.get(comm_id, 1)
            comm_dens = community_densities.get(comm_id, 0.0)
            cycle_cnt = cycle_counts.get(node_id, 0)

            rows.append(
                {
                    "node_id": node_id,
                    "entity_id": node_id,
                    "node_type": ntype,
                    "degree": deg,
                    "in_degree": in_deg,
                    "out_degree": out_deg,
                    "degree_centrality": deg_cent,
                    "betweenness_centrality": btw_cent,
                    "pagerank": pr,
                    "community_id": comm_id,
                    "community_size": comm_size,
                    "community_density": comm_dens,
                    "short_cycle_count": cycle_cnt,
                }
            )

        return pd.DataFrame(rows)

    @staticmethod
    def build_ml_feature_matrix(
        wallet_features: pd.DataFrame,
        graph_features: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Merge wallet features with graph topological metrics to form the final
        numerical matrix for Isolation Forest and anomaly detection.
        Replaces NaNs with column medians, ensuring reproducibility.
        """
        if wallet_features.empty:
            return pd.DataFrame(), []

        # Filter graph features to wallet nodes
        wallet_graph_feats = graph_features[
            graph_features["node_type"] == "wallet"
        ].copy() if not graph_features.empty else pd.DataFrame()

        if not wallet_graph_feats.empty:
            merged = pd.merge(
                wallet_features,
                wallet_graph_feats[
                    [
                        "entity_id",
                        "degree",
                        "degree_centrality",
                        "betweenness_centrality",
                        "pagerank",
                        "community_size",
                        "community_density",
                        "short_cycle_count",
                    ]
                ],
                on="entity_id",
                how="left",
            )
        else:
            merged = wallet_features.copy()
            merged["degree"] = 0
            merged["degree_centrality"] = 0.0
            merged["betweenness_centrality"] = 0.0
            merged["pagerank"] = 0.0
            merged["community_size"] = 1
            merged["community_density"] = 0.0
            merged["short_cycle_count"] = 0

        feature_cols = [
            "transaction_count",
            "incoming_transaction_count",
            "outgoing_transaction_count",
            "in_degree",
            "out_degree",
            "fan_in",
            "fan_out",
            "fan_out_ratio",
            "total_incoming",
            "total_outgoing",
            "total_volume",
            "address_reuse",
            "average_transaction_value",
            "median_transaction_value",
            "unique_counterparties",
            "max_repeated_value_count",
            "dust_incoming_count",
            "transaction_rate",
            "median_time_gap",
            "wallet_lifetime_seconds",
            "connected_ip_count",
            "unique_country_count",
            "unique_asn_count",
            "degree",
            "degree_centrality",
            "betweenness_centrality",
            "pagerank",
            "community_size",
            "community_density",
            "short_cycle_count",
        ]

        # Fill NaNs/Infs deterministically
        for col in feature_cols:
            if col in merged.columns:
                merged[col] = pd.to_numeric(merged[col], errors="coerce")
                med = merged[col].median()
                if pd.isna(med):
                    med = 0.0
                merged[col] = merged[col].fillna(med).replace([np.inf, -np.inf], med)
            else:
                merged[col] = 0.0

        return merged, feature_cols
