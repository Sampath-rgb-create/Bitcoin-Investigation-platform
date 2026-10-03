"""
Forensic Canonicalization Service for Bitcoin Investigation Platform.

Normalizes raw validated data into standardized canonical formats:
- Timestamps -> UTC ISO-8601 strings & epoch seconds
- Addresses -> trimmed, consistent casing
- Amounts -> float64 BTC values
- Transaction IDs -> lowercase hexadecimal strings
- IP addresses -> standardized IPv4/IPv6 strings
- Script types -> standardized lowercase string tokens

Outputs canonical Parquet files into data/cases/<case_id>/canonical/.
"""

import os
import ipaddress
import logging
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class Canonicalizer:
    """
    Standardizes valid forensic case files into canonical formats.
    """

    def __init__(self, raw_dir: str, canonical_dir: str):
        self.raw_dir = raw_dir
        self.canonical_dir = canonical_dir
        os.makedirs(self.canonical_dir, exist_ok=True)

    def canonicalize(self) -> Dict[str, str]:
        """
        Processes transactions.csv, inputs.csv, outputs.csv, network.csv
        and persists them as canonical Parquet tables.
        Returns paths to generated canonical files.
        """
        paths = {}
        paths["transactions"] = self._canonicalize_transactions()
        paths["inputs"] = self._canonicalize_inputs()
        paths["outputs"] = self._canonicalize_outputs()
        paths["network"] = self._canonicalize_network()
        return paths

    def _canonicalize_transactions(self) -> str:
        in_path = os.path.join(self.raw_dir, "transactions.csv")
        df = pd.read_csv(in_path)

        # Standardize txid
        df["txid"] = df["txid"].astype(str).str.strip().str.lower()

        # Standardize timestamps
        dt_series = pd.to_datetime(df["timestamp"], utc=True)
        df["timestamp_iso"] = dt_series.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        df["timestamp_epoch"] = dt_series.astype("int64") // 10**9

        # Standardize numerics
        df["fee"] = pd.to_numeric(df["fee"], errors="coerce").fillna(0.0).astype(np.float64)
        df["size"] = pd.to_numeric(df["size"], errors="coerce").fillna(0).astype(np.int64)
        if "version" in df.columns:
            df["version"] = pd.to_numeric(df["version"], errors="coerce").fillna(1).astype(np.int32)
        else:
            df["version"] = 1
        if "locktime" in df.columns:
            df["locktime"] = pd.to_numeric(df["locktime"], errors="coerce").fillna(0).astype(np.int64)
        else:
            df["locktime"] = 0

        # Sort chronologically
        df = df.sort_values(by="timestamp_epoch").reset_index(drop=True)

        out_path = os.path.join(self.canonical_dir, "transactions.parquet")
        df.to_parquet(out_path, index=False)
        return out_path

    def _canonicalize_inputs(self) -> str:
        in_path = os.path.join(self.raw_dir, "inputs.csv")
        df = pd.read_csv(in_path)

        df["txid"] = df["txid"].astype(str).str.strip().str.lower()
        df["prev_txid"] = df["prev_txid"].astype(str).str.strip().str.lower()
        df["prev_vout"] = pd.to_numeric(df["prev_vout"], errors="coerce").fillna(0).astype(np.int32)
        df["address"] = df["address"].astype(str).str.strip()
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0).astype(np.float64)

        if "script_type" in df.columns:
            df["script_type"] = df["script_type"].astype(str).str.strip().str.lower()
        else:
            df["script_type"] = "unknown"

        out_path = os.path.join(self.canonical_dir, "inputs.parquet")
        df.to_parquet(out_path, index=False)
        return out_path

    def _canonicalize_outputs(self) -> str:
        in_path = os.path.join(self.raw_dir, "outputs.csv")
        df = pd.read_csv(in_path)

        df["txid"] = df["txid"].astype(str).str.strip().str.lower()
        df["output_index"] = pd.to_numeric(df["output_index"], errors="coerce").fillna(0).astype(np.int32)
        df["address"] = df["address"].astype(str).str.strip()
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0).astype(np.float64)

        if "script_type" in df.columns:
            df["script_type"] = df["script_type"].astype(str).str.strip().str.lower()
        else:
            df["script_type"] = "unknown"

        out_path = os.path.join(self.canonical_dir, "outputs.parquet")
        df.to_parquet(out_path, index=False)
        return out_path

    def _canonicalize_network(self) -> str:
        in_path = os.path.join(self.raw_dir, "network.csv")
        df = pd.read_csv(in_path)

        df["txid"] = df["txid"].astype(str).str.strip().str.lower()
        dt_series = pd.to_datetime(df["timestamp"], utc=True)
        df["timestamp_iso"] = dt_series.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        df["timestamp_epoch"] = dt_series.astype("int64") // 10**9

        df["src_ip"] = df["src_ip"].astype(str).str.strip().apply(self._clean_ip)
        df["dst_ip"] = df["dst_ip"].astype(str).str.strip().apply(self._clean_ip)
        df["src_port"] = pd.to_numeric(df["src_port"], errors="coerce").fillna(0).astype(np.int32)
        df["dst_port"] = pd.to_numeric(df["dst_port"], errors="coerce").fillna(0).astype(np.int32)

        if "asn" in df.columns:
            df["asn"] = df["asn"].astype(str).str.strip().str.upper()
        else:
            df["asn"] = "UNKNOWN"

        if "country" in df.columns:
            df["country"] = df["country"].astype(str).str.strip().str.upper()
        else:
            df["country"] = "UNKNOWN"

        out_path = os.path.join(self.canonical_dir, "network.parquet")
        df.to_parquet(out_path, index=False)
        return out_path

    @staticmethod
    def _clean_ip(ip_str: str) -> str:
        if not ip_str or ip_str.lower() in ("nan", "none", "null"):
            return "0.0.0.0"
        try:
            # Strip port if present in ip:port format
            if ":" in ip_str and not ip_str.startswith("["):
                parts = ip_str.split(":")
                if len(parts) == 2 and parts[1].isdigit():
                    ip_str = parts[0]
            parsed = ipaddress.ip_address(ip_str)
            return str(parsed)
        except ValueError:
            return "0.0.0.0"
