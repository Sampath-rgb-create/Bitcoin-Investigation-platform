"""
Deterministic Behavioral Rules Detector for Bitcoin Investigation Platform.

Implements typologies and heuristics defined in PROTOTYPE.md & PLAN.md:
- RULE_BURST_ACTIVITY (R01): Rapid burst of transactions above rate/count threshold.
- RULE_HIGH_FAN_OUT (R02): Extreme number of outgoing outputs/counterparties.
- RULE_HIGH_FAN_IN (R03): Extreme number of incoming inputs/counterparties.
- RULE_RAPID_TRANSFER_CHAIN / RULE_RAPID_DISPERSAL (R04): Very low median time gap between transactions.
- RULE_REPEATED_VALUE (R05): Repeated identical rounded transfer amounts.
- RULE_SHORT_CYCLE (R06): Participation in circular transactions (2-4 hops).
- RULE_PEELING_CHAIN: Successive peeling transfers leaving small peel and forward change.
- RULE_DUST_ATTACK: Inflow of hundreds/thousands of sub-dust threshold outputs.
- RULE_FEE_ANOMALY: Transactions with zero fee or fee exceeding 20% of transaction value.

Every triggered rule provides:
- rule_id, rule_name
- triggered (bool)
- severity ('low', 'medium', 'high', 'critical')
- observed_value, threshold, unit
- source_record_ids (for audit provenance)
- description (deterministic explanation)
"""

from typing import Dict, List, Any, Optional
import pandas as pd


class BehaviorRulesDetector:
    """
    Evaluates rule sets against wallet and transaction records.
    """

    def __init__(
        self,
        burst_min_tx: int = 10,
        burst_min_rate: float = 0.1,  # tx/sec
        high_fan_out_threshold: int = 10,
        high_fan_in_threshold: int = 10,
        rapid_chain_max_gap: float = 30.0,  # seconds
        repeated_value_min_count: int = 5,
        dust_threshold_btc: float = 0.00000546,  # 546 satoshis standard Bitcoin dust threshold
        dust_min_count: int = 5,
        fee_anomaly_ratio: float = 0.20,
    ):
        self.burst_min_tx = burst_min_tx
        self.burst_min_rate = burst_min_rate
        self.high_fan_out_threshold = high_fan_out_threshold
        self.high_fan_in_threshold = high_fan_in_threshold
        self.rapid_chain_max_gap = rapid_chain_max_gap
        self.repeated_value_min_count = repeated_value_min_count
        self.dust_threshold_btc = dust_threshold_btc
        self.dust_min_count = dust_min_count
        self.fee_anomaly_ratio = fee_anomaly_ratio

    def evaluate_wallet(
        self,
        wallet_row: pd.Series,
        transactions: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Evaluate all behavioral rules for a single wallet entity.
        Returns a list of rule result objects.
        """
        results: List[Dict[str, Any]] = []
        entity_id = wallet_row.get("entity_id", f"wallet:{wallet_row.get('wallet_address')}")
        src_ids = wallet_row.get("source_record_ids", [])
        if isinstance(src_ids, set):
            src_ids = sorted(list(src_ids))
        elif not isinstance(src_ids, list):
            src_ids = []

        tx_count = int(wallet_row.get("transaction_count", 0))
        tx_rate = float(wallet_row.get("transaction_rate", 0.0))
        fan_out = int(wallet_row.get("fan_out", 0))
        fan_in = int(wallet_row.get("fan_in", 0))
        med_gap = float(wallet_row.get("median_time_gap", 0.0))
        rep_val_cnt = int(wallet_row.get("max_repeated_value_count", 0))
        dust_cnt = int(wallet_row.get("dust_incoming_count", 0))
        short_cycles = int(wallet_row.get("short_cycle_count", 0))

        # 1. R01: Burst Activity
        if tx_count >= self.burst_min_tx and tx_rate >= self.burst_min_rate:
            results.append(
                {
                    "rule_id": "RULE_BURST_ACTIVITY",
                    "code": "R01",
                    "entity_id": entity_id,
                    "triggered": True,
                    "confidence": min(1.0, round(tx_rate / (self.burst_min_rate * 2), 2)),
                    "severity": "medium",
                    "observed_value": round(tx_rate, 3),
                    "threshold": self.burst_min_rate,
                    "unit": "tx/sec",
                    "source_record_ids": src_ids[:20],
                    "description": (
                        f"Burst activity detected: {tx_count} transactions occurred at "
                        f"{tx_rate:.2f} tx/sec (threshold: {self.burst_min_rate} tx/sec)."
                    ),
                }
            )

        # 2. R02: High Fan-Out
        if fan_out >= self.high_fan_out_threshold:
            results.append(
                {
                    "rule_id": "RULE_HIGH_FAN_OUT",
                    "code": "R02",
                    "entity_id": entity_id,
                    "triggered": True,
                    "confidence": min(1.0, round(fan_out / (self.high_fan_out_threshold * 2), 2)),
                    "severity": "high" if fan_out >= self.high_fan_out_threshold * 2 else "medium",
                    "observed_value": fan_out,
                    "threshold": self.high_fan_out_threshold,
                    "unit": "outputs",
                    "source_record_ids": src_ids[:20],
                    "description": (
                        f"High fan-out dispersal detected: {fan_out} outgoing transfer paths "
                        f"(threshold: {self.high_fan_out_threshold})."
                    ),
                }
            )

        # 3. R03: High Fan-In
        if fan_in >= self.high_fan_in_threshold:
            results.append(
                {
                    "rule_id": "RULE_HIGH_FAN_IN",
                    "code": "R03",
                    "entity_id": entity_id,
                    "triggered": True,
                    "confidence": min(1.0, round(fan_in / (self.high_fan_in_threshold * 2), 2)),
                    "severity": "high" if fan_in >= self.high_fan_in_threshold * 2 else "medium",
                    "observed_value": fan_in,
                    "threshold": self.high_fan_in_threshold,
                    "unit": "inputs",
                    "source_record_ids": src_ids[:20],
                    "description": (
                        f"High fan-in consolidation detected: {fan_in} incoming transfer paths "
                        f"(threshold: {self.high_fan_in_threshold})."
                    ),
                }
            )

        # 4. R04: Rapid Transfer Chain / Rapid Dispersal
        if tx_count >= 5 and 0.0 < med_gap <= self.rapid_chain_max_gap:
            results.append(
                {
                    "rule_id": "RULE_RAPID_DISPERSAL",
                    "code": "R04",
                    "entity_id": entity_id,
                    "triggered": True,
                    "confidence": min(1.0, round(1.0 - (med_gap / self.rapid_chain_max_gap), 2)),
                    "severity": "high",
                    "observed_value": round(med_gap, 2),
                    "threshold": self.rapid_chain_max_gap,
                    "unit": "seconds",
                    "source_record_ids": src_ids[:20],
                    "description": (
                        f"Rapid transfer chain detected: Median time gap between transactions is "
                        f"{med_gap:.1f}s (threshold <= {self.rapid_chain_max_gap}s)."
                    ),
                }
            )

        # 5. R05: Repeated Value Structuring
        if rep_val_cnt >= self.repeated_value_min_count:
            results.append(
                {
                    "rule_id": "RULE_REPEATED_VALUE",
                    "code": "R05",
                    "entity_id": entity_id,
                    "triggered": True,
                    "confidence": min(1.0, round(rep_val_cnt / (self.repeated_value_min_count * 2), 2)),
                    "severity": "medium",
                    "observed_value": rep_val_cnt,
                    "threshold": self.repeated_value_min_count,
                    "unit": "occurrences",
                    "source_record_ids": src_ids[:20],
                    "description": (
                        f"Repeated-value transfer pattern: Wallet sent identical amount {rep_val_cnt} times "
                        f"(threshold: {self.repeated_value_min_count})."
                    ),
                }
            )

        # 6. R06: Short Directed Cycle
        if short_cycles > 0:
            results.append(
                {
                    "rule_id": "RULE_SHORT_CYCLE",
                    "code": "R06",
                    "entity_id": entity_id,
                    "triggered": True,
                    "confidence": 0.85,
                    "severity": "high",
                    "observed_value": short_cycles,
                    "threshold": 1,
                    "unit": "cycles",
                    "source_record_ids": src_ids[:20],
                    "description": (
                        f"Short circular fund movement: Wallet participates in {short_cycles} directed "
                        f"loop(s) of 2-4 hops."
                    ),
                }
            )

        # 7. Dust Attack / Flood
        if dust_cnt >= self.dust_min_count:
            results.append(
                {
                    "rule_id": "RULE_DUST_ATTACK",
                    "code": "R07",
                    "entity_id": entity_id,
                    "triggered": True,
                    "confidence": min(1.0, round(dust_cnt / (self.dust_min_count * 2), 2)),
                    "severity": "medium",
                    "observed_value": dust_cnt,
                    "threshold": self.dust_min_count,
                    "unit": "dust_inputs",
                    "source_record_ids": src_ids[:20],
                    "description": (
                        f"Dust attack / flood detected: Wallet received {dust_cnt} micro-transfers below "
                        f"{self.dust_threshold_btc} BTC."
                    ),
                }
            )

        # 8. Peeling Chain Check
        # Peeling chain heuristic: 1 input, 2 outputs where 1 is small (peeled) and 1 is large (change)
        # repeated over several consecutive transactions
        if tx_count >= 3 and fan_out >= 3:
            avg_val = float(wallet_row.get("average_transaction_value", 0.0))
            med_val = float(wallet_row.get("median_transaction_value", 0.0))
            if avg_val > 0 and (med_val / avg_val) < 0.25 and tx_count >= 3:
                results.append(
                    {
                        "rule_id": "RULE_PEELING_CHAIN",
                        "code": "R08",
                        "entity_id": entity_id,
                        "triggered": True,
                        "confidence": 0.90,
                        "severity": "high",
                        "observed_value": round(avg_val, 4),
                        "threshold": round(med_val, 4),
                        "unit": "BTC",
                        "source_record_ids": src_ids[:20],
                        "description": (
                            f"Peeling chain pattern: Disproportionate ratio between median peeled transfer "
                            f"({med_val:.4f} BTC) and major change volume ({avg_val:.4f} BTC)."
                        ),
                    }
                )

        return results

    def evaluate_transactions(
        self,
        transactions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Evaluate transaction-specific behavioral rules like Fee Anomaly.
        """
        results: List[Dict[str, Any]] = []
        for tx in transactions:
            txid = tx.get("txid", "")
            rec_id = tx.get("record_id", "")
            fee = float(tx.get("fee", 0.0) or 0.0)
            in_amts = [float(x) for x in (tx.get("input_amounts") or []) if x is not None]
            tot_in = sum(in_amts) if in_amts else 0.0

            # Fee Anomaly: zero fee on non-coinbase or fee > 20% of total input
            if tot_in > 0:
                fee_ratio = fee / tot_in
                if fee_ratio >= self.fee_anomaly_ratio or (fee == 0.0 and tot_in > 0.1):
                    results.append(
                        {
                            "rule_id": "RULE_FEE_ANOMALY",
                            "code": "R09",
                            "entity_id": f"transaction:{txid}",
                            "triggered": True,
                            "confidence": 0.85 if fee == 0.0 else min(1.0, round(fee_ratio / self.fee_anomaly_ratio, 2)),
                            "severity": "high" if fee_ratio > 0.50 else "medium",
                            "observed_value": round(fee_ratio, 4),
                            "threshold": self.fee_anomaly_ratio,
                            "unit": "ratio",
                            "source_record_ids": [rec_id] if rec_id else [],
                            "description": (
                                f"Fee anomaly detected in tx {txid[:10]}: Fee is {fee:.6f} BTC "
                                f"({fee_ratio * 100:.1f}% of total inputs)."
                            ),
                        }
                    )
        return results

    def compute_behavior_score(self, triggered_rules: List[Dict[str, Any]]) -> float:
        """
        Map triggered rules into a normalized behavior score [0.0, 1.0].
        Weights by severity: critical=0.40, high=0.25, medium=0.15, low=0.05.
        Clamped at 1.0.
        """
        if not triggered_rules:
            return 0.0

        severity_weights = {
            "critical": 0.40,
            "high": 0.25,
            "medium": 0.15,
            "low": 0.05,
        }

        total = 0.0
        for r in triggered_rules:
            sev = r.get("severity", "medium").lower()
            total += severity_weights.get(sev, 0.15)

        return min(round(total, 4), 1.0)
