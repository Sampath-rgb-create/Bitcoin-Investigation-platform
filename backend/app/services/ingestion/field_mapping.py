"""
Field mapping and column aliasing dictionary for Bitcoin Investigation Platform.
Maps diverse SIH column names and aliases to canonical schema fields.
"""
from typing import Dict, Any, List, Optional
import json


# Minimum required aliases per PROTOTYPE.md Section 5.6.1
CANONICAL_FIELD_ALIASES: Dict[str, List[str]] = {
    "timestamp": ["timestamp", "time", "ts", "ts_generation", "date", "datetime"],
    "src_ip": ["src_ip", "source_ip", "src", "client_ip", "ip_src", "source_address"],
    "dst_ip": ["dst_ip", "destination_ip", "dst", "server_ip", "ip_dst", "dest_ip", "destination_address"],
    "src_port": ["src_port", "source_port", "port_src", "client_port"],
    "dst_port": ["dst_port", "destination_port", "port_dst", "dest_port", "server_port"],
    "txid": ["txid", "transaction_id", "transaction_hash", "tx_hash", "hash", "tx_id"],
    "input_addresses": ["input_addresses", "inputs", "input", "vin_addresses", "from_addresses", "senders"],
    "output_addresses": ["output_addresses", "outputs", "output", "vout_addresses", "to_addresses", "recipients"],
    "input_amounts": ["input_amounts", "input_values", "vin_amounts", "from_amounts", "input_value", "vin_values"],
    "output_amounts": ["output_amounts", "output_values", "vout_amounts", "to_amounts", "output_value", "vout_values"],
    "fee": ["fee", "transaction_fee", "tx_fee", "fees"],
    "script_type": ["script_type", "script", "type", "tx_type"],
    "geo_country": ["geo_country", "country", "country_code", "src_country", "dst_country"],
    "asn": ["asn", "autonomous_system", "as_number", "asn_number", "src_asn", "dst_asn"],
}


def build_alias_lookup() -> Dict[str, str]:
    """
    Builds a normalized lookup table mapping lowercase alias string -> canonical field name.
    """
    lookup: Dict[str, str] = {}
    for canonical_name, aliases in CANONICAL_FIELD_ALIASES.items():
        lookup[canonical_name.lower()] = canonical_name
        for alias in aliases:
            lookup[alias.lower()] = canonical_name
    return lookup


ALIAS_LOOKUP = build_alias_lookup()


def map_raw_keys(raw_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms a dictionary of raw keys to canonical keys using ALIAS_LOOKUP.
    Preserves 'record_id' if present, or retains unmapped keys if they are not aliases.
    """
    mapped: Dict[str, Any] = {}
    for key, value in raw_record.items():
        clean_key = str(key).strip().lower()
        canonical_key = ALIAS_LOOKUP.get(clean_key, key)
        mapped[canonical_key] = value
    return mapped


def parse_list_field(val: Any) -> List[Any]:
    """
    Parses a string or iterable into a list.
    Supports JSON strings (e.g. '["W1", "W2"]'), comma-separated strings ('W1, W2'),
    pipe-separated strings ('W1|W2'), or returns the list if already list/tuple.
    """
    if val is None:
        return []
    if isinstance(val, (list, tuple)):
        return list(val)
    if isinstance(val, (int, float)):
        return [val]
    
    val_str = str(val).strip()
    if not val_str or val_str.lower() in ("none", "null", "[]"):
        return []
    
    # Try parsing as JSON array
    if (val_str.startswith("[") and val_str.endswith("]")) or (val_str.startswith("{") and val_str.endswith("}")):
        try:
            parsed = json.loads(val_str)
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict):
                return list(parsed.values())
        except Exception:
            pass
            
    # Try pipe separated, semicolon separated, or comma separated
    if "|" in val_str:
        return [part.strip() for part in val_str.split("|") if part.strip()]
    if ";" in val_str:
        return [part.strip() for part in val_str.split(";") if part.strip()]
    if "," in val_str:
        return [part.strip() for part in val_str.split(",") if part.strip()]
    
    # Single item
    return [val_str]
