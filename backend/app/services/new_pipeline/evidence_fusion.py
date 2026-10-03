"""
Multi-Stream Evidence Fusion Scorer for Bitcoin Investigation Platform.

Combines four distinct forensic evidence streams into an investigator priority lead:
1. Supervised Multi-Brain ML Stream:
   - 9 base neural & tree models aggregated by L2 Walk-Forward OOF Meta-Stacker (threshold = 0.675).
   - High-precision illicit classification confidence.
2. Unsupervised Anomaly Stream:
   - Tri-Domain Isolation Forest percentile outliers (Transaction 182-dim, Wallet 55-dim, Network 13-dim).
3. Graph Topological Stream:
   - Structural flow prominence: PageRank, Betweenness Centrality, WCC Component Reach, Dispersion Ratio.
4. Deterministic AML Behavioral Rules:
   - Peeling chains, dust bursts, fan-out dispersal, high fee anomalies.

Severity Tiers:
- CRITICAL: priority_score >= 80.0
- HIGH:     60.0 <= priority_score < 80.0
- MEDIUM:   40.0 <= priority_score < 60.0
- LOW:      priority_score < 40.0

Generates immutable Evidence Packs with full provenance linking source record IDs.
"""

import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd


class EvidenceFusionEngine:
    """
    Fuses supervised, anomaly, graph, and deterministic AML signals into calibrated lead scores.
    """

    def __init__(
        self,
        weight_supervised: float = 0.35,
        weight_anomaly: float = 0.25,
        weight_behavior: float = 0.20,
        weight_graph: float = 0.12,
        weight_network: float = 0.08,
    ):
        self.w_sup = weight_supervised
        self.w_anom = weight_anomaly
        self.w_beh = weight_behavior
        self.w_graph = weight_graph
        self.w_net = weight_network

        tot = self.w_sup + self.w_anom + self.w_beh + self.w_graph + self.w_net
        self.w_sup /= tot
        self.w_anom /= tot
        self.w_beh /= tot
        self.w_graph /= tot
        self.w_net /= tot

    @staticmethod
    def get_severity_tier(score: float) -> str:
        if score >= 80.0:
            return "CRITICAL"
        if score >= 60.0:
            return "HIGH"
        if score >= 40.0:
            return "MEDIUM"
        return "LOW"

    def fuse_entity(
        self,
        entity_id: str,
        entity_type: str,
        supervised_prob: Optional[float] = None,
        anomaly_score: float = 0.0,
        behavior_score: float = 0.0,
        graph_score: float = 0.0,
        network_score: float = 0.0,
        rule_score: float = 0.0,
        model_details: Optional[Dict[str, Any]] = None,
        rules_triggered: Optional[List[str]] = None,
        source_records: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Computes calibrated composite priority score and evidence pack for an entity.
        Includes separate stream scores: supervised_score, unsupervised_score, graph_score, rule_score.
        """
        sup = max(0.0, min(1.0, float(supervised_prob or 0.0)))
        anom = max(0.0, min(1.0, float(anomaly_score)))
        beh = max(0.0, min(1.0, float(behavior_score)))
        grp = max(0.0, min(1.0, float(graph_score)))
        net = max(0.0, min(1.0, float(network_score)))
        rl = max(0.0, min(100.0, float(rule_score)))

        if supervised_prob is not None:
            raw_priority = (
                self.w_sup * sup
                + self.w_anom * anom
                + self.w_beh * beh
                + self.w_graph * grp
                + self.w_net * net
            ) * 100.0
        else:
            # Rebalance weights if supervised score is unavailable
            rem_tot = self.w_anom + self.w_beh + self.w_graph + self.w_net
            raw_priority = (
                (self.w_anom / rem_tot) * anom
                + (self.w_beh / rem_tot) * beh
                + (self.w_graph / rem_tot) * grp
                + (self.w_net / rem_tot) * net
            ) * 100.0

        # If custom investigator rules fired, factor them dynamically
        if rl > 0:
            raw_priority = 0.85 * raw_priority + 0.15 * rl

        priority_score = round(float(np.clip(raw_priority, 0.0, 100.0)), 2)
        tier = self.get_severity_tier(priority_score)

        # Build comprehensive Evidence Pack with separated streams
        evidence_pack = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "priority_score": priority_score,
            "severity_tier": tier,
            "supervised_score": round(sup * 100.0, 2),
            "unsupervised_score": round(anom * 100.0, 2),
            "graph_score": round(grp * 100.0, 2),
            "rule_score": round(rl, 2),
            "score_components": {
                "supervised_score": round(sup * 100.0, 2),
                "unsupervised_score": round(anom * 100.0, 2),
                "anomaly_score": round(anom * 100.0, 2),
                "behavior_score": round(beh * 100.0, 2),
                "graph_score": round(grp * 100.0, 2),
                "rule_score": round(rl, 2),
                "network_score": round(net * 100.0, 2),
            },
            "model_evidence": model_details or {},
            "rules_triggered": rules_triggered or [],
            "source_records": source_records or [],
            "investigation_recommendation": self._generate_recommendation(tier, rules_triggered, sup),
        }

        return evidence_pack

    @staticmethod
    def _generate_recommendation(tier: str, rules: Optional[List[str]], sup_prob: float) -> str:
        recs = []
        if tier == "CRITICAL":
            recs.append("Immediate forensic triage recommended.")
        elif tier == "HIGH":
            recs.append("Elevated risk profile; inspect counterparty flows.")
        elif tier == "MEDIUM":
            recs.append("Moderate anomalous behavior detected.")
        else:
            recs.append("Routine activity baseline.")

        if sup_prob >= 0.675:
            recs.append("Multi-brain neural stacker flagged high illicit probability (>67.5%).")
        if rules:
            recs.append(f"Deterministic rules triggered: {', '.join(rules[:3])}.")

        return " ".join(recs)
