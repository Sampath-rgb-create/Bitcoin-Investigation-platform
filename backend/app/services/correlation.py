"""
Correlation Engine.
Correlates Bitcoin blockchain transaction records with P2P/network telemetry records.
Strategies supported:
1. TXID_EXACT: Exact match on shared txid. Recorded with method='exact_txid', basis='shared_txid'.
2. TIME_WINDOW: Temporal heuristic match when txid is missing from network observation.
                 Only active when allow_temporal=True.
                 Recorded with method='temporal_window', basis='heuristic'.

Computes:
- time_delta_ms between network observation and transaction timestamp.
- Correlation status per transaction: 'exactly_correlated', 'partially_correlated', 'uncorrelated'.
- Correlation strength coverage ratio.
"""
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from backend.app.core.config import settings


class CorrelationEngine:
    """
    Correlates network observations with transaction records.
    Every generated link maintains explicit provenance:
    - method: 'exact_txid' | 'temporal_window'
    - basis: 'shared_txid' | 'heuristic'
    - time_delta_ms: Milliseconds between network and tx events.
    """

    def __init__(
        self,
        allow_temporal: bool = settings.ALLOW_TEMPORAL_CORRELATION,
        window_seconds: int = settings.CORRELATION_WINDOW_SECONDS
    ):
        self.allow_temporal = allow_temporal
        self.window_seconds = window_seconds

    def correlate(
        self,
        transactions: List[Dict[str, Any]],
        network_observations: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """
        Executes correlation across transactions and network observations.
        
        Returns:
            links: List of correlation link objects matching Section 5.7:
                {
                    "network_record_id": ...,
                    "txid": ...,
                    "transaction_record_id": ...,
                    "method": "exact_txid" | "temporal_window",
                    "time_delta_ms": ...,
                    "basis": "shared_txid" | "heuristic",
                    "src_ip": ...,
                    "dst_ip": ...
                }
            tx_status_map: Dict mapping txid -> 'exactly_correlated' | 'partially_correlated' | 'uncorrelated'
        """
        links: List[Dict[str, Any]] = []

        # Index transactions by txid
        tx_by_id: Dict[str, List[Dict[str, Any]]] = {}
        for tx in transactions:
            txid = tx.get("txid")
            if txid:
                tx_by_id.setdefault(txid, []).append(tx)

        # Track which transactions got correlated
        tx_exact_matches: Dict[str, int] = {}
        tx_temporal_matches: Dict[str, int] = {}

        unmatched_observations: List[Dict[str, Any]] = []

        # Strategy 1: Exact TXID match
        for net_rec in network_observations:
            net_txid = net_rec.get("txid")
            net_rec_id = net_rec.get("record_id", "net-unknown")
            net_ts = net_rec.get("timestamp")

            matched = False
            if net_txid and net_txid in tx_by_id:
                for tx in tx_by_id[net_txid]:
                    tx_ts = tx.get("timestamp")
                    delta_ms = 0
                    if isinstance(net_ts, datetime) and isinstance(tx_ts, datetime):
                        delta_ms = int(abs((net_ts - tx_ts).total_seconds() * 1000))

                    links.append({
                        "network_record_id": net_rec_id,
                        "txid": net_txid,
                        "transaction_record_id": tx.get("record_id", "tx-unknown"),
                        "method": "exact_txid",
                        "time_delta_ms": delta_ms,
                        "basis": "shared_txid",
                        "src_ip": net_rec.get("src_ip"),
                        "dst_ip": net_rec.get("dst_ip"),
                    })
                    tx_exact_matches[net_txid] = tx_exact_matches.get(net_txid, 0) + 1
                    matched = True

            if not matched:
                unmatched_observations.append(net_rec)

        # Strategy 2: Temporal Window Heuristic (if enabled)
        if self.allow_temporal and unmatched_observations and transactions:
            for net_rec in unmatched_observations:
                net_ts = net_rec.get("timestamp")
                if not isinstance(net_ts, datetime):
                    continue

                net_rec_id = net_rec.get("record_id", "net-unknown")

                # Candidate search
                for tx in transactions:
                    tx_ts = tx.get("timestamp")
                    if not isinstance(tx_ts, datetime):
                        continue

                    diff_sec = abs((net_ts - tx_ts).total_seconds())
                    if diff_sec <= self.window_seconds:
                        txid = tx.get("txid", "unknown")
                        delta_ms = int(diff_sec * 1000)

                        links.append({
                            "network_record_id": net_rec_id,
                            "txid": txid,
                            "transaction_record_id": tx.get("record_id", "tx-unknown"),
                            "method": "temporal_window",
                            "time_delta_ms": delta_ms,
                            "basis": "heuristic",
                            "src_ip": net_rec.get("src_ip"),
                            "dst_ip": net_rec.get("dst_ip"),
                        })
                        tx_temporal_matches[txid] = tx_temporal_matches.get(txid, 0) + 1

        # Determine transaction correlation status
        tx_status_map: Dict[str, str] = {}
        for tx in transactions:
            txid = tx.get("txid")
            if not txid:
                continue
            if tx_exact_matches.get(txid, 0) > 0:
                tx_status_map[txid] = "exactly_correlated"
            elif tx_temporal_matches.get(txid, 0) > 0:
                tx_status_map[txid] = "partially_correlated"
            else:
                tx_status_map[txid] = "uncorrelated"

        return links, tx_status_map

    @staticmethod
    def calculate_correlation_strength(matched_observations: int, transaction_count: int) -> float:
        """
        Calculates correlation strength coverage ratio in [0.0, 1.0].
        Section 5.14: correlation_strength = matched_network_observations / max(transaction_count, 1)
        """
        if transaction_count <= 0:
            return 0.0
        ratio = matched_observations / float(transaction_count)
        return min(1.0, max(0.0, ratio))
