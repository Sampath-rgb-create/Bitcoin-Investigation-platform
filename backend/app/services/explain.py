"""
Deterministic Human-Readable Explanation Generator for Bitcoin Investigation Platform.

Generates structured, evidence-backed explanations for every alert.
Guarantees determinism: Given the same inputs, generates exact identical reasons.
Never hallucinates, never relies on non-deterministic external LLMs for critical scoring.
"""

from typing import Dict, List, Any, Optional


class DeterministicExplainer:
    """
    Translates mathematical detector outputs, triggered rules, and evidence items
    into structured reasons and concise human-readable summaries.
    """

    def __init__(self):
        pass

    def explain(
        self,
        entity_id: str,
        priority_score: float,
        severity: str,
        score_components: Dict[str, float],
        triggered_rules: List[Dict[str, Any]],
        evidence_pack: List[Dict[str, Any]],
        top_deviations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Produce deterministic explanation payload with structured top reasons.
        """
        reasons: List[Dict[str, Any]] = []

        # 1. Triggered behavioral rules are highest priority reasons
        for idx, rule in enumerate(triggered_rules):
            rule_id = rule.get("rule_id", f"RULE_{idx+1}")
            desc = rule.get("description", "")
            reasons.append(
                {
                    "reason_id": f"reason-rule-{idx+1}",
                    "type": "rule",
                    "feature": rule_id,
                    "value": rule.get("observed_value"),
                    "threshold_or_baseline": rule.get("threshold"),
                    "unit": rule.get("unit"),
                    "source_evidence_ids": [
                        ev["evidence_id"]
                        for ev in evidence_pack
                        if ev.get("feature") == rule_id
                    ][:3],
                    "text": desc,
                }
            )

        # 2. Add top anomalous feature deviations
        for idx, dev in enumerate(top_deviations[:3]):
            feat = dev.get("feature", "")
            val = dev.get("value")
            base = dev.get("baseline")
            dev_val = dev.get("deviation", 0.0)
            if dev_val > 1.5:  # Noticeable anomaly
                reasons.append(
                    {
                        "reason_id": f"reason-feat-{idx+1}",
                        "type": "feature",
                        "feature": feat,
                        "value": val,
                        "threshold_or_baseline": base,
                        "unit": "value",
                        "source_evidence_ids": [
                            ev["evidence_id"]
                            for ev in evidence_pack
                            if ev.get("feature") == feat
                        ][:3],
                        "text": f"Unusual {feat.replace('_', ' ')}: observed {val}, compared to case baseline {base}.",
                    }
                )

        # 3. Graph topological reason if graph score is high
        if score_components.get("graph_score", 0.0) >= 0.70:
            reasons.append(
                {
                    "reason_id": f"reason-graph-1",
                    "type": "graph",
                    "feature": "graph_score",
                    "value": score_components.get("graph_score"),
                    "threshold_or_baseline": 0.70,
                    "unit": "score",
                    "source_evidence_ids": [],
                    "text": f"High graph centrality / community structural density (score: {score_components['graph_score']:.2f}).",
                }
            )

        # 4. Network relay reason if network score is high
        if score_components.get("network_score", 0.0) >= 0.70:
            reasons.append(
                {
                    "reason_id": f"reason-net-1",
                    "type": "network",
                    "feature": "network_score",
                    "value": score_components.get("network_score"),
                    "threshold_or_baseline": 0.70,
                    "unit": "score",
                    "source_evidence_ids": [],
                    "text": f"High network dispersion / multi-IP relay concurrency (score: {score_components['network_score']:.2f}).",
                }
            )

        # Build short narrative summary
        narrative_parts = [
            f"Entity {entity_id} flagged with {severity} priority (score: {priority_score:.1f}/100)."
        ]
        if triggered_rules:
            rule_names = [r.get("rule_id", "rule") for r in triggered_rules]
            narrative_parts.append(f"Triggered {len(triggered_rules)} rule(s): {', '.join(rule_names)}.")
        if score_components.get("anomaly_score", 0.0) >= 0.70:
            narrative_parts.append(
                f"Isolation Forest placed entity in top {int((1.0 - score_components['anomaly_score']) * 100)}% percentile of unusual behavior."
            )

        summary_text = " ".join(narrative_parts)

        return {
            "entity_id": entity_id,
            "severity": severity,
            "priority_score": priority_score,
            "summary_text": summary_text,
            "top_reasons": reasons,
            "rule_count": len(triggered_rules),
            "evidence_count": len(evidence_pack),
        }
