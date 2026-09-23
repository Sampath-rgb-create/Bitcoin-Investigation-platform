"""
Graph Signals Detector for Bitcoin Investigation Platform.

Computes topological anomaly indicators separate from unsupervised ML scores:
- degree_percentile: Hub centrality indicator
- fanout_percentile: Outgoing connectivity spread
- community_size_percentile: Scale of the connected subnetwork
- community_density_percentile: Structural tightness of fund circulation
- cycle_signal: Participation in feedback loops / circular mixing
- bridge_signal / betweenness: Bridge centrality indicator connecting disparate components

Formula from PROTOTYPE.md Section 5.13:
graph_score = weighted mean of available graph signals
"""

from typing import Dict, List, Any, Optional, Set
import numpy as np
import pandas as pd
import networkx as nx


class GraphSignalsDetector:
    """
    Computes graph structural signals, bridge centrality, hub detection,
    and weighted graph anomaly score.
    """

    DEFAULT_WEIGHTS = {
        "degree": 0.20,
        "fanout": 0.20,
        "community_size": 0.20,
        "community_density": 0.20,
        "cycle_signal": 0.10,
        "betweenness": 0.10,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS

    @staticmethod
    def _percentile_rank(series: pd.Series) -> pd.Series:
        """Deterministically rank values to [0.0, 1.0]."""
        if len(series) <= 1:
            return pd.Series(0.5, index=series.index)
        ranks = series.rank(method="average", ascending=True)
        return (ranks - 1.0) / (len(series) - 1.0)

    def evaluate(
        self,
        wallet_features: pd.DataFrame,
        graph_features: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Calculates graph signals and composite graph_score for each wallet.
        """
        if wallet_features.empty:
            result = wallet_features.copy()
            result["graph_score"] = 0.0
            return result

        # Merge graph features on entity_id
        candidate_cols = ["degree", "out_degree", "community_size", "community_density", "short_cycle_count", "betweenness_centrality"]
        cols_to_merge = ["entity_id"]
        if not graph_features.empty and "entity_id" in graph_features.columns:
            for c in candidate_cols:
                if c in graph_features.columns:
                    cols_to_merge.append(c)
            merged = pd.merge(
                wallet_features,
                graph_features[cols_to_merge],
                on="entity_id",
                how="left",
            )
        else:
            merged = wallet_features.copy()
            merged["degree"] = 0
            merged["out_degree"] = 0
            merged["community_size"] = 1
            merged["community_density"] = 0.0
            merged["short_cycle_count"] = 0

        # Fill missing values
        if "degree" not in merged.columns:
            merged["degree"] = 0
        else:
            merged["degree"] = merged["degree"].fillna(0)

        if "out_degree" not in merged.columns:
            merged["out_degree"] = merged.get("fan_out", 0)
        else:
            merged["out_degree"] = merged["out_degree"].fillna(merged.get("fan_out", 0))

        if "community_size" not in merged.columns:
            merged["community_size"] = 1
        else:
            merged["community_size"] = merged["community_size"].fillna(1)

        if "community_density" not in merged.columns:
            merged["community_density"] = 0.0
        else:
            merged["community_density"] = merged["community_density"].fillna(0.0)

        if "short_cycle_count" not in merged.columns:
            merged["short_cycle_count"] = 0
        else:
            merged["short_cycle_count"] = merged["short_cycle_count"].fillna(0)

        if "betweenness_centrality" not in merged.columns:
            merged["betweenness_centrality"] = 0.0
        else:
            merged["betweenness_centrality"] = merged["betweenness_centrality"].fillna(0.0)

        # Percentile rank each signal across case
        deg_p = self._percentile_rank(merged["degree"].astype(float))
        fan_p = self._percentile_rank(merged["out_degree"].astype(float))
        csize_p = self._percentile_rank(merged["community_size"].astype(float))
        cdens_p = self._percentile_rank(merged["community_density"].astype(float))
        btw_p = self._percentile_rank(merged["betweenness_centrality"].astype(float))

        # Cycle signal: 1.0 if cycles > 0, otherwise 0.0
        cycle_sig = merged["short_cycle_count"].apply(lambda c: 1.0 if c > 0 else 0.0)

        # Weighted combination
        w = self.weights
        composite_score = (
            w.get("degree", 0.20) * deg_p
            + w.get("fanout", 0.20) * fan_p
            + w.get("community_size", 0.20) * csize_p
            + w.get("community_density", 0.20) * cdens_p
            + w.get("cycle_signal", 0.10) * cycle_sig
            + w.get("betweenness", 0.10) * btw_p
        )

        res_df = wallet_features.copy()
        res_df["degree_percentile"] = np.round(deg_p.values, 4)
        res_df["fanout_percentile"] = np.round(fan_p.values, 4)
        res_df["community_size_percentile"] = np.round(csize_p.values, 4)
        res_df["community_density_percentile"] = np.round(cdens_p.values, 4)
        res_df["betweenness_percentile"] = np.round(btw_p.values, 4)
        res_df["cycle_signal"] = cycle_sig.values
        res_df["graph_score"] = np.round(composite_score.values, 4)

        return res_df

    def find_bridges_and_hubs(self, graph: nx.DiGraph, top_k: int = 10) -> Dict[str, Any]:
        """
        Identify bridge edges, articulation points, and high-centrality hubs in the graph.
        """
        if graph.number_of_nodes() == 0:
            return {"bridges": [], "articulation_points": [], "hubs": []}

        undirected = graph.to_undirected()
        
        # 1. Bridges
        bridges = []
        try:
            for u, v in nx.bridges(undirected):
                bridges.append({"source": u, "target": v})
        except Exception:
            pass

        # 2. Articulation points (bridge cut-nodes)
        art_points = []
        try:
            art_points = list(nx.articulation_points(undirected))
        except Exception:
            pass

        # 3. High-centrality hubs
        hubs = []
        try:
            degrees = dict(graph.degree())
            sorted_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
            for node, deg in sorted_nodes[:top_k]:
                hubs.append({
                    "entity_id": node,
                    "degree": deg,
                    "node_type": graph.nodes[node].get("type", "unknown"),
                })
        except Exception:
            pass

        return {
            "bridges": bridges[:top_k],
            "articulation_points": art_points[:top_k],
            "hubs": hubs,
        }
