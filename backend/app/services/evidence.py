"""
Evidence Compilation and Provenance Manager for Bitcoin Investigation Platform.

Assembles immutable Evidence Packs linking alerts and detector findings to:
- Exact source record IDs (CSV/JSON/XML line identifiers)
- Concrete feature values and baseline distributions
- Triggered heuristic rules
- Forensic provenance trails

Complies with PROTOTYPE.md Section 5.16 & 5.17:
- Evidence classes: 'observed', 'derived', 'detector', 'inferred'
"""

from typing import Dict, List, Any, Optional
import uuid


class EvidenceManager:
    """
    Constructs structured evidence items and audit provenance records.
    """

    def __init__(self):
        pass

    @staticmethod
    def create_evidence_item(
        evidence_class: str,
        entity_id: str,
        feature_or_signal: str,
        value: Any,
        baseline: Optional[Any] = None,
        unit: Optional[str] = None,
        source_record_ids: Optional[List[str]] = None,
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Create a single structured evidence item.
        evidence_class: 'observed', 'derived', 'detector', 'inferred'
        """
        return {
            "evidence_id": f"ev-{uuid.uuid4().hex[:8]}",
            "class": evidence_class,
            "entity_id": entity_id,
            "feature": feature_or_signal,
            "value": value,
            "baseline": baseline,
            "unit": unit,
            "source_record_ids": sorted(list(set(source_record_ids or []))),
            "description": description,
        }

    def compile_evidence_pack(
        self,
        entity_id: str,
        wallet_features: Dict[str, Any],
        case_medians: Dict[str, float],
        triggered_rules: List[Dict[str, Any]],
        top_deviations: List[Dict[str, Any]],
        source_record_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Compiles a comprehensive list of evidence items for an alert.
        """
        evidence_pack = []

        # 1. Observed source evidence
        if source_record_ids:
            evidence_pack.append(
                self.create_evidence_item(
                    evidence_class="observed",
                    entity_id=entity_id,
                    feature_or_signal="source_records",
                    value=len(source_record_ids),
                    unit="records",
                    source_record_ids=source_record_ids,
                    description=f"Entity is referenced across {len(source_record_ids)} source dataset record(s).",
                )
            )

        # 2. Detector rules triggered
        for rule in triggered_rules:
            evidence_pack.append(
                self.create_evidence_item(
                    evidence_class="detector",
                    entity_id=entity_id,
                    feature_or_signal=rule.get("rule_id", "UNKNOWN_RULE"),
                    value=rule.get("observed_value"),
                    baseline=rule.get("threshold"),
                    unit=rule.get("unit"),
                    source_record_ids=rule.get("source_record_ids") or source_record_ids[:5],
                    description=rule.get("description", ""),
                )
            )

        # 3. Derived deviant features from Isolation Forest feature attributions
        for dev in top_deviations:
            feat_name = dev.get("feature", "")
            val = dev.get("value")
            med = dev.get("baseline")
            evidence_pack.append(
                self.create_evidence_item(
                    evidence_class="derived",
                    entity_id=entity_id,
                    feature_or_signal=feat_name,
                    value=val,
                    baseline=med,
                    source_record_ids=source_record_ids[:5],
                    description=f"{feat_name} is {val} compared to case median {med}.",
                )
            )

        return evidence_pack
