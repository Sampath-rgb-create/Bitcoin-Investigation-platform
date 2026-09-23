import json
import os
import urllib.parse
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.db.models import Alert, AnalysisRun, Case, User
from backend.app.api.deps import get_current_user
from backend.app.storage.parquet_store import parquet_store

router = APIRouter()


@router.get("/cases/{case_id}/wallets/{wallet_id}")
def get_wallet_profile(
    case_id: str,
    wallet_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve forensic profile for an address/entity.
    Wallet IDs are unquoted if URL-encoded.
    """
    decoded_wallet = urllib.parse.unquote(wallet_id)
    entity_key = decoded_wallet if decoded_wallet.startswith("wallet:") else f"wallet:{decoded_wallet}"
    clean_addr = decoded_wallet.replace("wallet:", "")

    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' was not found",
        )

    # Check for any alerts on this entity in this case
    latest_alert = (
        db.query(Alert)
        .join(AnalysisRun, Alert.run_id == AnalysisRun.id)
        .filter(AnalysisRun.case_id == case_id, Alert.entity_id == entity_key)
        .order_by(Alert.priority_score.desc())
        .first()
    )

    alert_reasons = []
    score_components = {}
    if latest_alert:
        try:
            alert_reasons = json.loads(latest_alert.reasons_json) if latest_alert.reasons_json else []
        except Exception:
            alert_reasons = []
        score_components = {
            "anomaly_score": latest_alert.anomaly_score,
            "behavior_score": latest_alert.behavior_score,
            "graph_score": latest_alert.graph_score,
            "network_score": latest_alert.network_score,
        }

    features = {
        "transaction_count": 0,
        "total_incoming": 0.0,
        "total_outgoing": 0.0,
        "balance": 0.0,
        "unique_counterparties": 0,
        "fan_in": 0,
        "fan_out": 0,
        "connected_ip_count": 0,
    }

    feat_file = os.path.join(settings.DATA_DIR, "cases", case_id, "features", "wallet_features.parquet")
    if os.path.exists(feat_file):
        try:
            df = parquet_store.read_dataframe(feat_file)
            match = df[(df.get("wallet_address") == clean_addr) | (df.get("entity_id") == entity_key)]
            if not match.empty:
                row = match.iloc[0].to_dict()
                for k in features:
                    if k in row and row[k] is not None:
                        features[k] = row[k]
                features["balance"] = round(features["total_incoming"] - features["total_outgoing"], 8)
        except Exception:
            pass

    return {
        "case_id": case_id,
        "entity_id": entity_key,
        "address": clean_addr,
        "type": "wallet",
        "latest_alert_id": latest_alert.id if latest_alert else None,
        "priority_score": latest_alert.priority_score if latest_alert else 0.0,
        "severity": latest_alert.severity if latest_alert else "LOW",
        "reasons": alert_reasons,
        "score_components": score_components,
        "features": features,
    }


@router.get("/cases/{case_id}/wallets/{wallet_id}/transactions")
def get_wallet_transactions(
    case_id: str,
    wallet_id: str,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve transactions involving this wallet address."""
    decoded_wallet = urllib.parse.unquote(wallet_id)
    clean_addr = decoded_wallet.replace("wallet:", "")

    tx_file = os.path.join(settings.DATA_DIR, "cases", case_id, "normalized", "transactions.parquet")
    matching_txs = []

    if os.path.exists(tx_file):
        try:
            df_tx = parquet_store.read_dataframe(tx_file)
            for _, row in df_tx.iterrows():
                in_addrs = list(row["input_addresses"]) if hasattr(row.get("input_addresses"), "__iter__") else []
                out_addrs = list(row["output_addresses"]) if hasattr(row.get("output_addresses"), "__iter__") else []

                is_input = clean_addr in in_addrs
                is_output = clean_addr in out_addrs

                if is_input or is_output:
                    matching_txs.append({
                        "txid": row.get("txid"),
                        "timestamp": row.get("timestamp"),
                        "fee": float(row.get("fee", 0.0) or 0.0),
                        "direction": "OUTGOING" if is_input else "INCOMING",
                        "script_type": row.get("script_type", "P2WPKH"),
                        "inputs_count": len(in_addrs),
                        "outputs_count": len(out_addrs),
                    })
                    if len(matching_txs) >= limit:
                        break
        except Exception:
            pass

    return {
        "case_id": case_id,
        "wallet_id": clean_addr,
        "transactions": matching_txs,
        "total": len(matching_txs),
    }


@router.get("/cases/{case_id}/wallets/{wallet_id}/network")
def get_wallet_network_observations(
    case_id: str,
    wallet_id: str,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Correlated IP and ASN observations for this entity."""
    decoded_wallet = urllib.parse.unquote(wallet_id)
    clean_addr = decoded_wallet.replace("wallet:", "")

    net_file = os.path.join(settings.DATA_DIR, "cases", case_id, "normalized", "network.parquet")
    corr_file = os.path.join(settings.DATA_DIR, "cases", case_id, "correlated", "network_transaction_links.parquet")
    obs = []

    if os.path.exists(net_file):
        try:
            df_net = parquet_store.read_dataframe(net_file)
            # Sample or take first rows
            for _, r in df_net.head(limit).iterrows():
                obs.append({
                    "ip": r.get("src_ip") or r.get("client_ip") or r.get("ip"),
                    "port": r.get("src_port") or r.get("port"),
                    "asn": r.get("asn"),
                    "country": r.get("country") or r.get("geo_country"),
                    "timestamp": r.get("timestamp"),
                    "txid": r.get("txid"),
                })
        except Exception:
            pass

    return {
        "case_id": case_id,
        "wallet_id": clean_addr,
        "network_observations": obs,
        "total": len(obs),
    }


@router.get("/cases/{case_id}/entities/{entity_id:path}")
def get_entity_details(
    case_id: str,
    entity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Unified inspector endpoint for ANY entity type (wallet, transaction, ip, asn, country).
    Returns rich metadata, transaction counts, balances, or relay details.
    """
    decoded_id = urllib.parse.unquote(entity_id)

    # Determine type accurately
    entity_type = "unknown"
    if (
        decoded_id.startswith("wallet:")
        or decoded_id.startswith("bc1")
        or decoded_id.startswith("tb1")
        or (len(decoded_id) >= 25 and (decoded_id.startswith("1") or decoded_id.startswith("3")))
    ):
        entity_type = "wallet"
    elif (
        decoded_id.startswith("transaction:")
        or decoded_id.startswith("tx_")
        or (len(decoded_id) == 64 and all(c in "0123456789abcdefABCDEF" for c in decoded_id))
    ):
        entity_type = "transaction"
    elif decoded_id.startswith("ip:") or ("." in decoded_id and any(c.isdigit() for c in decoded_id)):
        entity_type = "ip"
    elif decoded_id.startswith("asn:") or decoded_id.startswith("AS"):
        entity_type = "asn"
    elif decoded_id.startswith("country:"):
        entity_type = "country"
    else:
        # Fallback: check if wallet or tx
        entity_type = "wallet"

    # If wallet: delegate to get_wallet_profile
    if entity_type == "wallet":
        return get_wallet_profile(case_id, decoded_id, db=db, current_user=current_user)

    # If transaction: look up transaction
    if entity_type == "transaction":
        clean_txid = decoded_id.replace("transaction:", "")
        tx_file = os.path.join(settings.DATA_DIR, "cases", case_id, "normalized", "transactions.parquet")
        net_file = os.path.join(settings.DATA_DIR, "cases", case_id, "normalized", "network.parquet")

        tx_data = {
            "case_id": case_id,
            "entity_id": f"transaction:{clean_txid}",
            "txid": clean_txid,
            "type": "transaction",
            "timestamp": None,
            "fee": 0.0,
            "total_input": 0.0,
            "total_output": 0.0,
            "script_type": "P2WPKH",
            "inputs": [],
            "outputs": [],
            "relayed_by_ips": [],
        }

        if os.path.exists(tx_file):
            try:
                df_tx = parquet_store.read_dataframe(tx_file)
                match = df_tx[df_tx["txid"] == clean_txid]
                if not match.empty:
                    row = match.iloc[0]
                    tx_data["timestamp"] = row.get("timestamp")
                    tx_data["fee"] = float(row.get("fee", 0.0) or 0.0)
                    tx_data["script_type"] = row.get("script_type", "P2WPKH")

                    in_addrs = list(row["input_addresses"]) if hasattr(row.get("input_addresses"), "__iter__") else []
                    in_amts = list(row["input_amounts"]) if hasattr(row.get("input_amounts"), "__iter__") else []
                    out_addrs = list(row["output_addresses"]) if hasattr(row.get("output_addresses"), "__iter__") else []
                    out_amts = list(row["output_amounts"]) if hasattr(row.get("output_amounts"), "__iter__") else []

                    tx_data["total_input"] = sum(in_amts) if in_amts else 0.0
                    tx_data["total_output"] = sum(out_amts) if out_amts else 0.0

                    for addr, amt in zip(in_addrs[:10], in_amts[:10]):
                        tx_data["inputs"].append({"address": str(addr), "amount": float(amt)})
                    for addr, amt in zip(out_addrs[:10], out_amts[:10]):
                        tx_data["outputs"].append({"address": str(addr), "amount": float(amt)})
            except Exception:
                pass

        if os.path.exists(net_file):
            try:
                df_net = parquet_store.read_dataframe(net_file)
                net_match = df_net[df_net["txid"] == clean_txid]
                for _, nr in net_match.head(10).iterrows():
                    tx_data["relayed_by_ips"].append({
                        "ip": nr.get("src_ip") or nr.get("ip"),
                        "port": nr.get("src_port") or nr.get("port"),
                        "asn": nr.get("asn"),
                        "country": nr.get("country"),
                    })
            except Exception:
                pass

        return tx_data

    # If IP:
    if entity_type == "ip":
        clean_ip = decoded_id.replace("ip:", "")
        net_file = os.path.join(settings.DATA_DIR, "cases", case_id, "normalized", "network.parquet")
        ip_data = {
            "case_id": case_id,
            "entity_id": f"ip:{clean_ip}",
            "ip": clean_ip,
            "type": "ip",
            "country": None,
            "asn": None,
            "relayed_tx_count": 0,
            "sample_txids": [],
            "ports": [],
        }

        if os.path.exists(net_file):
            try:
                df_net = parquet_store.read_dataframe(net_file)
                match = df_net[(df_net.get("src_ip") == clean_ip) | (df_net.get("ip") == clean_ip)]
                if not match.empty:
                    ip_data["relayed_tx_count"] = len(match)
                    ip_data["country"] = match.iloc[0].get("country")
                    ip_data["asn"] = match.iloc[0].get("asn")
                    ip_data["sample_txids"] = list(match["txid"].dropna().unique()[:10])
                    ip_data["ports"] = list(match["src_port"].dropna().unique()[:5]) if "src_port" in match.columns else []
            except Exception:
                pass

        return ip_data

    return {
        "case_id": case_id,
        "entity_id": decoded_id,
        "type": entity_type,
        "label": decoded_id,
    }
