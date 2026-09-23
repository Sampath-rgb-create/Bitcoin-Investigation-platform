"""
Priority Fusion Scorer for Bitcoin Investigation Platform.

Combines four distinct signal streams into a single transparent investigation priority score:
1. Anomaly Score (Isolation Forest percentile rank)
2. Behavior Score (Triggered heuristic rules severity)
3. Graph Score (Centrality, community density, loops)
4. Network Score (IP dispersion, country diversity, relay bursts)

Formula (PROTOTYPE.md Section 5.15):
priority_score = 100 * (
    w_a * anomaly_score +
    w_b * behavior_score +
    w_g * graph_score +
    w_n * network_score
)

Default Weights:
w_a = 0.40 (Anomaly)
w_b = 0.30 (Behavior)
w_g = 0.20 (Graph)
w_n = 0.10 (Network)

Severity Tiers:
- CRITICAL: priority_score >= 85
- HIGH:     70 <= priority_score < 85
- MEDIUM:   40 <= priority_score < 70
- LOW:      0  <= priority_score < 40
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from backend.app.core.config import settings


class PriorityFusionScorer:
    """
    Computes priority scores and maps them to severity tiers.
    """

    def __init__(
        self,
        weight_anomaly: Optional[float] = None,
        weight_behavior: Optional[float] = None,
        weight_graph: Optional[float] = None,
        weight_network: Optional[float] = None,
    ):
        self.w_a = weight_anomaly if weight_anomaly is not None else settings.WEIGHT_ANOMALY
        self.w_b = weight_behavior if weight_behavior is not None else settings.WEIGHT_BEHAVIOR
        self.w_g = weight_graph if weight_graph is not None else settings.WEIGHT_GRAPH
        self.w_n = weight_network if weight_network is not None else settings.WEIGHT_NETWORK

        # Ensure weights sum to 1.0
        tot = self.w_a + self.w_b + self.w_g + self.w_n
        if tot > 0:
            self.w_a /= tot
            self.w_b /= tot
            self.w_g /= tot
            self.w_n /= tot

    @staticmethod
    def get_severity_tier(score: float) -> str:
        """
        Map priority score to priority severity tier.
        Supports both normalized [0.0, 1.0] and percentage [0.0, 100.0].
        Thresholds:
        - CRITICAL: >= 0.80 (or >= 80.0)
        - HIGH:     >= 0.60 (or >= 60.0)
        - MEDIUM:   >= 0.40 (or >= 40.0)
        - LOW:      < 0.40 (or < 40.0)
        """
        s = score if score <= 1.0 else (score / 100.0)
        if s >= 0.80:
            return "CRITICAL"
        elif s >= 0.60:
            return "HIGH"
        elif s >= 0.40:
            return "MEDIUM"
        else:
            return "LOW"

    def compute_priority(
        self,
        anomaly_score: float,
        behavior_score: float,
        graph_score: float,
        network_score: float,
    ) -> Tuple[float, str, Dict[str, float]]:
        """
        Compute weighted priority score, severity tier, and components.
        """
        a = max(0.0, min(1.0, float(anomaly_score)))
        b = max(0.0, min(1.0, float(behavior_score)))
        g = max(0.0, min(1.0, float(graph_score)))
        n = max(0.0, min(1.0, float(network_score)))

        raw_sum = (
            self.w_a * a
            + self.w_b * b
            + self.w_g * g
            + self.w_n * n
        )
        priority_score = round(raw_sum * 100.0, 2)
        tier = self.get_severity_tier(priority_score)

        components = {
            "anomaly_score": round(a, 4),
            "behavior_score": round(b, 4),
            "graph_score": round(g, 4),
            "network_score": round(n, 4),
        }

        return priority_score, tier, components

    def score_all(
        self,
        scored_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Calculate composite priority score for all entities in the DataFrame.
        """
        if scored_df.empty:
            df = scored_df.copy()
            df["priority_score"] = 0.0
            df["severity"] = "LOW"
            return df

        res = scored_df.copy()
        a = res.get("anomaly_score", 0.0).fillna(0.0).clip(0.0, 1.0)
        b = res.get("behavior_score", 0.0).fillna(0.0).clip(0.0, 1.0)
        g = res.get("graph_score", 0.0).fillna(0.0).clip(0.0, 1.0)
        n = res.get("network_score", 0.0).fillna(0.0).clip(0.0, 1.0)

        raw_100 = 100.0 * (
            self.w_a * a + self.w_b * b + self.w_g * g + self.w_n * n
        )
        res["priority_score"] = np.round(raw_100.values, 2)
        res["severity"] = res["priority_score"].apply(self.get_severity_tier)

        return res
