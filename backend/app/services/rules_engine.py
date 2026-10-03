"""
Dynamic Investigator Rules Engine for Bitcoin Investigation Platform.

Allows investigators to define, store, and execute custom heuristic forensic rules
directly from raw and canonical data (transaction & wallet records) without code redeployment.

Supported operators:
- '>', '>=', '<', '<=', '==', '!=', 'contains'

Supported target entities:
- 'wallet' (e.g. transaction_count, fan_out, fan_in, transaction_rate, total_sent, etc.)
- 'transaction' (e.g. fee, amount, input_count, output_count, fee_ratio)

Outputs:
- rule hits with observed values and descriptions
- normalized rule_score (0.0 to 100.0) based on investigator rule severity and weights
"""

from typing import List, Dict, Any, Optional
import operator
import logging

logger = logging.getLogger(__name__)

OPERATORS = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}

SEVERITY_WEIGHTS = {
    "critical": 35.0,
    "high": 25.0,
    "medium": 15.0,
    "low": 5.0,
}


class DynamicRulesEngine:
    """
    Evaluates dynamic investigator-defined rules against wallet and transaction records.
    """

    def __init__(self, custom_rules: Optional[List[Dict[str, Any]]] = None):
        self.rules = custom_rules or []

    def evaluate_wallet(
        self,
        wallet_record: Dict[str, Any],
        entity_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Evaluates wallet-targeted dynamic rules against a wallet record.
        """
        results = []
        ent_id = entity_id or wallet_record.get("entity_id", f"wallet:{wallet_record.get('wallet_address', 'unknown')}")

        for rule in self.rules:
            if not rule.get("enabled", 1):
                continue
            if rule.get("target_entity", "wallet") != "wallet":
                continue

            field = rule.get("field")
            op_str = rule.get("operator")
            threshold = float(rule.get("threshold", 0.0))
            rule_name = rule.get("name", "Custom Rule")
            severity = rule.get("severity", "medium").lower()
            weight = float(rule.get("weight", 1.0))
            rule_id = rule.get("id", f"custom_{field}_{op_str}")

            val = wallet_record.get(field)
            if val is None:
                continue

            try:
                numeric_val = float(val)
            except (ValueError, TypeError):
                continue

            op_fn = OPERATORS.get(op_str)
            if not op_fn:
                continue

            try:
                is_hit = op_fn(numeric_val, threshold)
            except Exception:
                is_hit = False

            if is_hit:
                results.append({
                    "rule_id": rule_id,
                    "rule_name": rule_name,
                    "code": "CUSTOM",
                    "entity_id": ent_id,
                    "triggered": True,
                    "severity": severity,
                    "weight": weight,
                    "observed_value": round(numeric_val, 4),
                    "threshold": threshold,
                    "operator": op_str,
                    "field": field,
                    "description": (
                        f"Custom Rule [{rule_name}]: Observed {field}={numeric_val:.4f} "
                        f"satisfies condition ({op_str} {threshold})."
                    ),
                })

        return results

    def evaluate_transaction(
        self,
        tx_record: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Evaluates transaction-targeted dynamic rules.
        """
        results = []
        txid = tx_record.get("txid", "unknown")
        ent_id = f"transaction:{txid}"

        for rule in self.rules:
            if not rule.get("enabled", 1):
                continue
            if rule.get("target_entity") != "transaction":
                continue

            field = rule.get("field")
            op_str = rule.get("operator")
            threshold = float(rule.get("threshold", 0.0))
            rule_name = rule.get("name", "Custom Rule")
            severity = rule.get("severity", "medium").lower()
            weight = float(rule.get("weight", 1.0))
            rule_id = rule.get("id", f"custom_tx_{field}_{op_str}")

            val = tx_record.get(field)
            if val is None:
                continue

            try:
                numeric_val = float(val)
            except (ValueError, TypeError):
                continue

            op_fn = OPERATORS.get(op_str)
            if not op_fn:
                continue

            try:
                is_hit = op_fn(numeric_val, threshold)
            except Exception:
                is_hit = False

            if is_hit:
                results.append({
                    "rule_id": rule_id,
                    "rule_name": rule_name,
                    "code": "CUSTOM_TX",
                    "entity_id": ent_id,
                    "triggered": True,
                    "severity": severity,
                    "weight": weight,
                    "observed_value": round(numeric_val, 4),
                    "threshold": threshold,
                    "operator": op_str,
                    "field": field,
                    "description": (
                        f"Custom Rule [{rule_name}]: Observed tx {field}={numeric_val:.4f} "
                        f"satisfies condition ({op_str} {threshold})."
                    ),
                })

        return results

    @staticmethod
    def compute_rule_score(triggered_rules: List[Dict[str, Any]]) -> float:
        """
        Computes a normalized rule score (0.0 to 100.0) from triggered custom rules.
        """
        if not triggered_rules:
            return 0.0

        total_pts = 0.0
        for r in triggered_rules:
            sev = r.get("severity", "medium").lower()
            base_pts = SEVERITY_WEIGHTS.get(sev, 15.0)
            weight = float(r.get("weight", 1.0))
            total_pts += base_pts * weight

        # Clamped at 100.0
        return round(min(total_pts, 100.0), 2)
