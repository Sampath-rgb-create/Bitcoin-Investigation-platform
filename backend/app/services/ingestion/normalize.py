"""
Normalization service:
- Normalizes timestamps to timezone-aware UTC datetime strings (ISO-8601).
- Normalizes IP addresses to canonical lowercase string format.
- Normalizes ports and numeric values to standard integer / float types.
- Computes SHA-256 fingerprint for records and dataset content.
"""
import hashlib
import ipaddress
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List


def compute_sha256_bytes(data: bytes) -> str:
    """Computes SHA-256 hex digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def compute_sha256_string(text: str) -> str:
    """Computes SHA-256 hex digest of string text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_timestamp(ts_val: Any) -> Optional[datetime]:
    """
    Converts various timestamp formats into a UTC datetime object.
    Supports ISO-8601 strings, UNIX epoch integers/floats, and existing datetime objects.
    """
    if ts_val is None or ts_val == "":
        return None
    if isinstance(ts_val, datetime):
        if ts_val.tzinfo is None:
            return ts_val.replace(tzinfo=timezone.utc)
        return ts_val.astimezone(timezone.utc)
    
    # Try numeric epoch
    try:
        num = float(ts_val)
        # Handle millisecond vs second timestamps
        if num > 1e11:  # likely milliseconds
            num = num / 1000.0
        return datetime.fromtimestamp(num, tz=timezone.utc)
    except (ValueError, TypeError):
        pass

    # Try ISO string parsing
    s = str(ts_val).strip()
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        # Fallback formats
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y/%m/%d %H:%M:%S"):
            try:
                dt = datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue

    return None


def normalize_ip(ip_val: Optional[str]) -> Optional[str]:
    """
    Normalizes IPv4 or IPv6 address string into canonical lowercase representation.
    """
    if not ip_val or not isinstance(ip_val, str):
        return None
    clean = ip_val.strip()
    if not clean or clean.lower() in ("none", "null"):
        return None
    try:
        obj = ipaddress.ip_address(clean)
        return str(obj).lower()
    except ValueError:
        return clean.lower()


def normalize_port(port_val: Optional[Any]) -> Optional[int]:
    """Normalizes port value to integer or None."""
    if port_val is None or port_val == "" or (isinstance(port_val, str) and port_val.lower() in ("none", "null")):
        return None
    try:
        p = int(port_val)
        if 0 <= p <= 65535:
            return p
        return None
    except (ValueError, TypeError):
        return None


def normalize_amounts(amounts: List[Any]) -> List[float]:
    """Ensures all amounts in list are valid floats."""
    result: List[float] = []
    for a in amounts:
        try:
            result.append(float(a))
        except (ValueError, TypeError):
            continue
    return result


def normalize_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Applies comprehensive normalization to a mapped record dictionary.
    """
    norm = dict(raw)
    
    # 1. Normalize timestamp
    dt = normalize_timestamp(norm.get("timestamp"))
    if dt:
        norm["timestamp"] = dt
    
    # 2. Normalize IPs
    if "src_ip" in norm:
        norm["src_ip"] = normalize_ip(norm["src_ip"])
    if "dst_ip" in norm:
        norm["dst_ip"] = normalize_ip(norm["dst_ip"])

    # 3. Normalize ports
    if "src_port" in norm:
        norm["src_port"] = normalize_port(norm["src_port"])
    if "dst_port" in norm:
        norm["dst_port"] = normalize_port(norm["dst_port"])

    # 4. Normalize amounts and fee
    if "input_amounts" in norm and isinstance(norm["input_amounts"], list):
        norm["input_amounts"] = normalize_amounts(norm["input_amounts"])
    if "output_amounts" in norm and isinstance(norm["output_amounts"], list):
        norm["output_amounts"] = normalize_amounts(norm["output_amounts"])
    if "fee" in norm and norm["fee"] is not None:
        try:
            norm["fee"] = float(norm["fee"])
        except (ValueError, TypeError):
            norm["fee"] = 0.0

    # 5. Normalize country & ASN
    if "geo_country" in norm and norm["geo_country"]:
        norm["geo_country"] = str(norm["geo_country"]).strip().upper()
    if "asn" in norm and norm["asn"]:
        norm["asn"] = str(norm["asn"]).strip()

    # 6. Ensure clean txid string
    if "txid" in norm and norm["txid"] is not None:
        norm["txid"] = str(norm["txid"]).strip()

    return norm
