"""
Network Signals Detector for Bitcoin Investigation Platform.

Detects network-layer anomalies and telemetry patterns:
- network_activity_percentile: Observation frequency
- unique_ip_percentile: Multi-IP relay burst indicator
- unique_country_percentile: Geographic dispersion
- port_anomaly_signal: Relays on unexpected non-P2P ports (standard BTC port is 8333 / testnet 18333)
- correlation_strength: Matched network observations per transaction count clamped to [0, 1]

Formula from PROTOTYPE.md Section 5.14:
network_score = weighted mean of available network signals
"""

from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd


class NetworkSignalsDetector:
    """
    Computes network telemetry signals and correlation metrics.
    """

    DEFAULT_P2P_PORTS = {8333, 18333, 8332, 18332, 28332, 28333}
    TOR_VPN_PORTS = {9050, 9051, 9150, 1194, 4433, 8080, 1080}

    def __init__(self):
        pass

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
        network_features: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Calculates network signals, network_score, and correlation_strength for wallets.
        """
        if wallet_features.empty:
            result = wallet_features.copy()
            result["network_score"] = 0.0
            result["correlation_strength"] = 0.0
            return result

        res_df = wallet_features.copy()

        ip_cnt = res_df.get("connected_ip_count", pd.Series(0, index=res_df.index)).astype(float)
        country_cnt = res_df.get("unique_country_count", pd.Series(0, index=res_df.index)).astype(float)
        asn_cnt = res_df.get("unique_asn_count", pd.Series(0, index=res_df.index)).astype(float)
        tx_cnt = res_df.get("transaction_count", pd.Series(1, index=res_df.index)).astype(float)

        # Percentile ranks
        ip_p = self._percentile_rank(ip_cnt)
        country_p = self._percentile_rank(country_cnt)
        asn_p = self._percentile_rank(asn_cnt)

        # Multi-IP relay burst: if wallet has >= 3 distinct IPs
        relay_burst = ip_cnt.apply(lambda x: 1.0 if x >= 3 else (x / 3.0))

        # Weighted network score [0.0, 1.0]
        net_score = 0.35 * ip_p + 0.25 * country_p + 0.20 * asn_p + 0.20 * relay_burst

        # Correlation strength: matched network observations / max(tx_cnt, 1)
        # In wallet_features, connected_ip_count gives linked observations
        corr_strength = (ip_cnt / tx_cnt.apply(lambda x: max(x, 1.0))).clip(0.0, 1.0)

        res_df["unique_ip_percentile"] = np.round(ip_p.values, 4)
        res_df["unique_country_percentile"] = np.round(country_p.values, 4)
        res_df["relay_burst_signal"] = np.round(relay_burst.values, 4)
        res_df["network_score"] = np.round(net_score.values, 4)
        res_df["correlation_strength"] = np.round(corr_strength.values, 4)

        return res_df

    def detect_network_port_anomalies(
        self,
        network_observations: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Flag network observations communicating over suspicious, non-standard, or Tor/VPN ports.
        """
        anomalies = []
        for obs in network_observations:
            dst_port = obs.get("dst_port")
            src_port = obs.get("src_port")
            rec_id = obs.get("record_id")
            src_ip = obs.get("src_ip", "")
            txid = obs.get("txid", "")

            # Check for Tor / VPN port usage
            if (dst_port in self.TOR_VPN_PORTS) or (src_port in self.TOR_VPN_PORTS):
                port_used = dst_port if dst_port in self.TOR_VPN_PORTS else src_port
                anomalies.append(
                    {
                        "rule_id": "RULE_TOR_VPN_PORT",
                        "src_ip": src_ip,
                        "port": port_used,
                        "txid": txid,
                        "severity": "high",
                        "source_record_ids": [rec_id] if rec_id else [],
                        "description": (
                            f"Suspected Tor/VPN relay port {port_used} detected for IP {src_ip}."
                        ),
                    }
                )
            elif dst_port is not None and dst_port not in self.DEFAULT_P2P_PORTS:
                # Non-standard Bitcoin P2P port
                anomalies.append(
                    {
                        "rule_id": "RULE_PORT_ANOMALY",
                        "src_ip": src_ip,
                        "dst_port": dst_port,
                        "txid": txid,
                        "severity": "medium",
                        "source_record_ids": [rec_id] if rec_id else [],
                        "description": (
                            f"Non-standard Bitcoin port {dst_port} utilized by relay IP {src_ip} "
                            f"(expected standard P2P ports: 8333, 18333)."
                        ),
                    }
                )
        return anomalies

    def detect_relay_bursts(
        self,
        transactions: List[Dict[str, Any]],
        network_observations: List[Dict[str, Any]],
        burst_threshold: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Detect transactions broadcasted/relayed almost simultaneously from multiple distinct IPs.
        """
        tx_ips: Dict[str, Set[str]] = {}
        tx_records: Dict[str, Set[str]] = {}

        for obs in network_observations:
            txid = obs.get("txid")
            src_ip = obs.get("src_ip")
            rec_id = obs.get("record_id")
            if txid and src_ip:
                tx_ips.setdefault(txid, set()).add(src_ip)
                if rec_id:
                    tx_records.setdefault(txid, set()).add(rec_id)

        bursts = []
        for txid, ips in tx_ips.items():
            if len(ips) >= burst_threshold:
                bursts.append({
                    "rule_id": "RULE_MULTI_IP_RELAY_BURST",
                    "txid": txid,
                    "entity_id": f"transaction:{txid}",
                    "unique_ip_count": len(ips),
                    "ips": sorted(list(ips)),
                    "severity": "high",
                    "source_record_ids": sorted(list(tx_records.get(txid, set()))),
                    "description": (
                        f"Multi-IP relay burst detected: Transaction {txid[:10]} was relayed across "
                        f"{len(ips)} distinct IP addresses."
                    ),
                })
        return bursts
