#!/usr/bin/env python3
"""
Synthetic Forensic Dataset Generator for Bitcoin Investigation Platform.

Generates:
1. Canonical Multi-File Schema (strictly validated by InputValidator & Canonicalizer):
   - transactions.csv: [txid, timestamp, fee, size]
   - inputs.csv:       [txid, prev_txid, prev_vout, address, amount]
   - outputs.csv:      [txid, output_index, address, amount]
   - network.csv:      [txid, timestamp, src_ip, src_port, dst_ip, dst_port, geo_country, asn]
2. Legacy Combined & Single CSVs for backward compatibility:
   - combined_1000.csv, transactions_1000.csv, network_telemetry_1000.csv
3. Ground Truth Report:
   - ground_truth.json & ground_truth.md: Explicit catalog of all licit vs illicit transactions,
     primary illicit wallet addresses, and suspicious network IPs.
"""

import csv
import json
import random
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Tuple

DEFAULT_OUTPUT_DIR = str(Path(__file__).resolve().parent.parent / "data" / "samples")


def random_btc_address(prefix: str = "bc1q") -> str:
    chars = "023456789acdefghjklmnpqrstuvwxyz"
    return prefix + "".join(random.choices(chars, k=34))


def random_ip() -> str:
    return f"{random.randint(11, 190)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"


def generate_synthetic_data(
    output_dir: str = DEFAULT_OUTPUT_DIR,
    total_normal_txs: int = 150,
    seed: int = 42,
):
    random.seed(seed)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    start_time = datetime(2026, 3, 1, 8, 0, 0, tzinfo=timezone.utc)
    current_time = start_time

    # Primary data structures
    transactions_list: List[Dict] = []
    inputs_list: List[Dict] = []
    outputs_list: List[Dict] = []
    network_list: List[Dict] = []

    # Ground truth catalog
    ground_truth = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_transactions": 0,
            "total_licit_transactions": 0,
            "total_illicit_transactions": 0,
        },
        "illicit_entities": {
            "wallets": [],
            "ips": [],
            "transactions": [],
        },
        "licit_sample": {
            "wallets": [],
            "transactions": [],
        },
        "planted_typologies": [],
    }

    # Regular benign pools
    benign_wallets = [random_btc_address("bc1q_norm_") for _ in range(40)]
    benign_ips = [random_ip() for _ in range(20)]

    ground_truth["licit_sample"]["wallets"] = benign_wallets[:10]

    # ==========================================
    # 1. NORMAL / LICIT TRANSACTIONS
    # ==========================================
    for i in range(total_normal_txs):
        txid = f"tx_licit_{i:04d}"
        current_time += timedelta(seconds=random.randint(10, 90))
        sender = random.choice(benign_wallets)
        receiver = random.choice([w for w in benign_wallets if w != sender])
        change_addr = random.choice([w for w in benign_wallets if w not in (sender, receiver)])

        amt = round(random.uniform(0.05, 3.5), 6)
        fee = 0.0001
        in_amt = round(amt + fee + random.uniform(0.1, 1.0), 6)
        change_amt = round(in_amt - amt - fee, 6)
        size = random.randint(220, 260)

        # 1. transactions.csv
        transactions_list.append({
            "txid": txid,
            "timestamp": current_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "fee": fee,
            "size": size,
            "label": 0, # Licit
        })

        # 2. inputs.csv
        inputs_list.append({
            "txid": txid,
            "prev_txid": f"tx_prev_{random.randint(100, 999):04d}",
            "prev_vout": 0,
            "address": sender,
            "amount": in_amt,
        })

        # 3. outputs.csv
        outputs_list.append({
            "txid": txid,
            "output_index": 0,
            "address": receiver,
            "amount": amt,
        })
        outputs_list.append({
            "txid": txid,
            "output_index": 1,
            "address": change_addr,
            "amount": change_amt,
        })

        # 4. network.csv
        if random.random() > 0.10:
            src_ip = random.choice(benign_ips)
            dst_ip = random.choice([ip for ip in benign_ips if ip != src_ip])
            network_list.append({
                "txid": txid,
                "timestamp": (current_time + timedelta(milliseconds=random.randint(100, 800))).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "src_ip": src_ip,
                "src_port": random.randint(30000, 60000),
                "dst_ip": dst_ip,
                "dst_port": 8333,
                "geo_country": "US",
                "asn": "AS15169",
            })

    ground_truth["licit_sample"]["transactions"] = [t["txid"] for t in transactions_list[:15]]
    licit_tx_count = len(transactions_list)

    # ==========================================
    # 2. ILLICIT TYPOLOGY 1: PEELING CHAIN
    # Sequential hops peeling off funds with small change hops
    # ==========================================
    peel_wallet_source = "bc1q_peel_master_source_x99a7b1c3e4d"
    peel_ip = "198.51.100.42"
    peel_txids = []
    peel_wallets = [peel_wallet_source]

    ground_truth["illicit_entities"]["wallets"].append({
        "address": peel_wallet_source,
        "role": "Peeling Chain Master Originator",
        "typology": "peeling_chain",
    })
    ground_truth["illicit_entities"]["ips"].append({
        "ip": peel_ip,
        "description": "Bulletproof proxy originating sequential peeling hops",
        "country": "NL",
        "asn": "AS1103",
    })

    remaining_bal = 25.0
    current_peel_wallet = peel_wallet_source
    for step in range(8):
        txid = f"tx_illicit_peel_{step:03d}"
        peel_txids.append(txid)
        current_time += timedelta(seconds=15)
        peel_amt = 0.75
        fee = 0.0002
        change_amt = round(remaining_bal - peel_amt - fee, 6)
        next_peel_wallet = f"bc1q_peel_hop_{step:02d}_{random_btc_address()[-12:]}"
        peel_wallets.append(next_peel_wallet)
        sink_wallet = random.choice(benign_wallets)

        transactions_list.append({
            "txid": txid,
            "timestamp": current_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "fee": fee,
            "size": 225,
            "label": 1, # Illicit
        })
        inputs_list.append({
            "txid": txid,
            "prev_txid": f"tx_peel_init_{step}",
            "prev_vout": 1 if step > 0 else 0,
            "address": current_peel_wallet,
            "amount": remaining_bal,
        })
        outputs_list.append({
            "txid": txid,
            "output_index": 0,
            "address": sink_wallet,
            "amount": peel_amt,
        })
        outputs_list.append({
            "txid": txid,
            "output_index": 1,
            "address": next_peel_wallet,
            "amount": change_amt,
        })
        network_list.append({
            "txid": txid,
            "timestamp": (current_time + timedelta(milliseconds=180)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "src_ip": peel_ip,
            "src_port": 50123 + step,
            "dst_ip": random.choice(benign_ips),
            "dst_port": 8333,
            "geo_country": "NL",
            "asn": "AS1103",
        })

        remaining_bal = change_amt
        current_peel_wallet = next_peel_wallet

    ground_truth["planted_typologies"].append({
        "typology": "PEELING_CHAIN",
        "description": "Sequential rapid offloading of 0.75 BTC per hop across 8 continuous hops",
        "primary_wallet": peel_wallet_source,
        "associated_wallets": peel_wallets,
        "suspicious_ip": peel_ip,
        "txids": peel_txids,
        "count": len(peel_txids),
    })

    # ==========================================
    # 3. ILLICIT TYPOLOGY 2: DUST ATTACK / DUST FLOOD
    # Rapid sub-dust outputs sent to clutter addresses
    # ==========================================
    dust_source = "bc1q_dust_botnet_origin_f83b1a9c4e20"
    dust_ip = "203.0.113.99"
    dust_txids = []

    ground_truth["illicit_entities"]["wallets"].append({
        "address": dust_source,
        "role": "Dust Flood Controller",
        "typology": "dust_flood",
    })
    ground_truth["illicit_entities"]["ips"].append({
        "ip": dust_ip,
        "description": "Anomalous relay host issuing rapid sub-dust transactions",
        "country": "RU",
        "asn": "AS12389",
    })

    for step in range(20):
        txid = f"tx_illicit_dust_{step:03d}"
        dust_txids.append(txid)
        current_time += timedelta(milliseconds=350)
        victim_wallet = random.choice(benign_wallets)

        transactions_list.append({
            "txid": txid,
            "timestamp": current_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "fee": 0.00000040,
            "size": 180,
            "label": 1,
        })
        inputs_list.append({
            "txid": txid,
            "prev_txid": f"tx_dust_feed_{step}",
            "prev_vout": 0,
            "address": dust_source,
            "amount": 0.00005500,
        })
        outputs_list.append({
            "txid": txid,
            "output_index": 0,
            "address": victim_wallet,
            "amount": 0.00005460, # Sub-dust / dust threshold
        })
        network_list.append({
            "txid": txid,
            "timestamp": current_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "src_ip": dust_ip,
            "src_port": 49152,
            "dst_ip": random.choice(benign_ips),
            "dst_port": 8333,
            "geo_country": "RU",
            "asn": "AS12389",
        })

    ground_truth["planted_typologies"].append({
        "typology": "DUST_FLOOD",
        "description": "Burst of 20 rapid sub-dust transactions (< 546 sats) to trace UTXO clustering",
        "primary_wallet": dust_source,
        "associated_wallets": [dust_source],
        "suspicious_ip": dust_ip,
        "txids": dust_txids,
        "count": len(dust_txids),
    })

    # ==========================================
    # 4. ILLICIT TYPOLOGY 3: HIGH FAN-OUT RAPID DISPERSAL
    # 1 input dispersed to 25 recipients in 1 transaction
    # ==========================================
    dispersal_source = "bc1q_dispersal_launderer_w77d2f9a1b0c"
    dispersal_ip = "192.0.2.77"
    disp_txid = "tx_illicit_dispersal_001"

    ground_truth["illicit_entities"]["wallets"].append({
        "address": dispersal_source,
        "role": "High Fan-Out Dispersal Source",
        "typology": "rapid_dispersal",
    })
    ground_truth["illicit_entities"]["ips"].append({
        "ip": dispersal_ip,
        "description": "Originating IP for large fan-out tumbler dispersal",
        "country": "DE",
        "asn": "AS24940",
    })

    current_time += timedelta(minutes=2)
    disp_outputs_wallets = [f"bc1q_disp_sink_{i:02d}_{random_btc_address()[-10:]}" for i in range(25)]
    disp_amount = 0.20
    disp_fee = 0.0010
    total_in = round(len(disp_outputs_wallets) * disp_amount + disp_fee, 6)

    transactions_list.append({
        "txid": disp_txid,
        "timestamp": current_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fee": disp_fee,
        "size": 950,
        "label": 1,
    })
    inputs_list.append({
        "txid": disp_txid,
        "prev_txid": "tx_pre_dispersal_funding",
        "prev_vout": 0,
        "address": dispersal_source,
        "amount": total_in,
    })
    for vout_idx, out_addr in enumerate(disp_outputs_wallets):
        outputs_list.append({
            "txid": disp_txid,
            "output_index": vout_idx,
            "address": out_addr,
            "amount": disp_amount,
        })
    network_list.append({
        "txid": disp_txid,
        "timestamp": current_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "src_ip": dispersal_ip,
        "src_port": 54321,
        "dst_ip": random.choice(benign_ips),
        "dst_port": 8333,
        "geo_country": "DE",
        "asn": "AS24940",
    })

    ground_truth["planted_typologies"].append({
        "typology": "RAPID_DISPERSAL",
        "description": "1 input split into 25 simultaneous destination outputs (fan-out ratio 25:1)",
        "primary_wallet": dispersal_source,
        "associated_wallets": [dispersal_source] + disp_outputs_wallets,
        "suspicious_ip": dispersal_ip,
        "txids": [disp_txid],
        "count": 1,
    })

    # ==========================================
    # 5. ILLICIT TYPOLOGY 4: ZERO / ANOMALOUS FEE SIPHON
    # Unusually high volume transfer with 0 fee (miner collusion)
    # ==========================================
    zero_fee_source = "bc1q_miner_siphon_collusion_000000fee"
    zero_fee_sink = "bc1q_offshore_vault_destination_999999"
    zero_fee_ip = "185.220.101.5" # Tor Exit Node IP
    zero_fee_txid = "tx_illicit_zerofee_collusion_001"

    ground_truth["illicit_entities"]["wallets"].append({
        "address": zero_fee_source,
        "role": "Miner Collusion / Zero Fee Siphon",
        "typology": "fee_anomaly",
    })
    ground_truth["illicit_entities"]["ips"].append({
        "ip": zero_fee_ip,
        "description": "Known Tor Exit Node relaying zero-fee whale transfer",
        "country": "IS",
        "asn": "AS39351",
    })

    current_time += timedelta(minutes=5)
    transactions_list.append({
        "txid": zero_fee_txid,
        "timestamp": current_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fee": 0.0, # Zero fee anomaly
        "size": 225,
        "label": 1,
    })
    inputs_list.append({
        "txid": zero_fee_txid,
        "prev_txid": "tx_whale_vault_feed",
        "prev_vout": 0,
        "address": zero_fee_source,
        "amount": 50.0,
    })
    outputs_list.append({
        "txid": zero_fee_txid,
        "output_index": 0,
        "address": zero_fee_sink,
        "amount": 50.0,
    })
    network_list.append({
        "txid": zero_fee_txid,
        "timestamp": current_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "src_ip": zero_fee_ip,
        "src_port": 9050,
        "dst_ip": random.choice(benign_ips),
        "dst_port": 8333,
        "geo_country": "IS",
        "asn": "AS39351",
    })

    ground_truth["planted_typologies"].append({
        "typology": "FEE_ANOMALY_COLLUSION",
        "description": "Whale 50.0 BTC transfer with 0.0 fee routed via Tor exit relay",
        "primary_wallet": zero_fee_source,
        "associated_wallets": [zero_fee_source, zero_fee_sink],
        "suspicious_ip": zero_fee_ip,
        "txids": [zero_fee_txid],
        "count": 1,
    })

    # Summary calculation
    all_illicit_txids = []
    for typo in ground_truth["planted_typologies"]:
        all_illicit_txids.extend(typo["txids"])

    ground_truth["illicit_entities"]["transactions"] = all_illicit_txids
    ground_truth["metadata"]["total_transactions"] = len(transactions_list)
    ground_truth["metadata"]["total_licit_transactions"] = licit_tx_count
    ground_truth["metadata"]["total_illicit_transactions"] = len(all_illicit_txids)

    # ==========================================
    # WRITE CANONICAL 4 CSV FILES
    # ==========================================
    # 1. transactions.csv
    with open(out_path / "transactions.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["txid", "timestamp", "fee", "size"])
        writer.writeheader()
        for t in transactions_list:
            writer.writerow({
                "txid": t["txid"],
                "timestamp": t["timestamp"],
                "fee": t["fee"],
                "size": t["size"],
            })

    # 2. inputs.csv
    with open(out_path / "inputs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["txid", "prev_txid", "prev_vout", "address", "amount"])
        writer.writeheader()
        writer.writerows(inputs_list)

    # 3. outputs.csv
    with open(out_path / "outputs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["txid", "output_index", "address", "amount"])
        writer.writeheader()
        writer.writerows(outputs_list)

    # 4. network.csv
    with open(out_path / "network.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["txid", "timestamp", "src_ip", "src_port", "dst_ip", "dst_port", "geo_country", "asn"])
        writer.writeheader()
        writer.writerows(network_list)

    # ==========================================
    # WRITE LEGACY COMPATIBILITY FILES
    # ==========================================
    # Map inputs & outputs grouped by txid
    inp_map = {}
    for inp in inputs_list:
        inp_map.setdefault(inp["txid"], {"addrs": [], "amts": []})
        inp_map[inp["txid"]]["addrs"].append(inp["address"])
        inp_map[inp["txid"]]["amts"].append(inp["amount"])

    out_map = {}
    for out in outputs_list:
        out_map.setdefault(out["txid"], {"addrs": [], "amts": []})
        out_map[out["txid"]]["addrs"].append(out["address"])
        out_map[out["txid"]]["amts"].append(out["amount"])

    net_map = {n["txid"]: n for n in network_list}

    # combined_1000.csv / synthetic_combined.csv
    combined_rows = []
    for t in transactions_list:
        txid = t["txid"]
        inps = inp_map.get(txid, {"addrs": [], "amts": []})
        outs = out_map.get(txid, {"addrs": [], "amts": []})
        net = net_map.get(txid, {})
        combined_rows.append({
            "record_id": f"rec_{txid}",
            "timestamp": t["timestamp"],
            "txid": txid,
            "input_addresses": json.dumps(inps["addrs"]),
            "output_addresses": json.dumps(outs["addrs"]),
            "input_amounts": json.dumps(inps["amts"]),
            "output_amounts": json.dumps(outs["amts"]),
            "fee": t["fee"],
            "script_type": "P2WPKH",
            "src_ip": net.get("src_ip", ""),
            "dst_ip": net.get("dst_ip", ""),
            "src_port": net.get("src_port", ""),
            "dst_port": net.get("dst_port", ""),
            "geo_country": net.get("geo_country", ""),
            "asn": net.get("asn", ""),
        })

    for c_name in ["combined_1000.csv", "synthetic_combined.csv"]:
        with open(out_path / c_name, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "record_id", "timestamp", "txid", "input_addresses", "output_addresses",
                "input_amounts", "output_amounts", "fee", "script_type", "src_ip", "dst_ip",
                "src_port", "dst_port", "geo_country", "asn"
            ])
            writer.writeheader()
            writer.writerows(combined_rows)

    # transactions_1000.csv
    with open(out_path / "transactions_1000.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "record_id", "timestamp", "txid", "input_addresses", "output_addresses",
            "input_amounts", "output_amounts", "fee", "script_type"
        ])
        writer.writeheader()
        for r in combined_rows:
            writer.writerow({
                "record_id": r["record_id"],
                "timestamp": r["timestamp"],
                "txid": r["txid"],
                "input_addresses": r["input_addresses"],
                "output_addresses": r["output_addresses"],
                "input_amounts": r["input_amounts"],
                "output_amounts": r["output_amounts"],
                "fee": r["fee"],
                "script_type": r["script_type"],
            })

    # network_telemetry_1000.csv
    with open(out_path / "network_telemetry_1000.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "record_id", "timestamp", "txid", "src_ip", "dst_ip", "src_port", "dst_port", "geo_country", "asn"
        ])
        writer.writeheader()
        for n in network_list:
            writer.writerow({
                "record_id": f"net_{n['txid']}",
                "timestamp": n["timestamp"],
                "txid": n["txid"],
                "src_ip": n["src_ip"],
                "dst_ip": n["dst_ip"],
                "src_port": n["src_port"],
                "dst_port": n["dst_port"],
                "geo_country": n["geo_country"],
                "asn": n["asn"],
            })

    # ==========================================
    # WRITE GROUND TRUTH JSON & MARKDOWN
    # ==========================================
    gt_json_path = out_path / "ground_truth.json"
    with open(gt_json_path, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)

    gt_md_path = out_path / "ground_truth.md"
    with open(gt_md_path, "w", encoding="utf-8") as f:
        f.write("# Forensic Dataset Ground Truth & Anomaly Catalog\n\n")
        f.write(f"- **Generated At**: `{ground_truth['metadata']['generated_at']}`\n")
        f.write(f"- **Total Transactions**: `{ground_truth['metadata']['total_transactions']}`\n")
        f.write(f"- **Licit Transactions**: `{ground_truth['metadata']['total_licit_transactions']}` (Normal daily commerce)\n")
        f.write(f"- **Illicit Transactions**: `{ground_truth['metadata']['total_illicit_transactions']}` (Planted anomalies)\n\n")
        f.write("## 1. Planted Illicit Typologies\n\n")
        for typo in ground_truth["planted_typologies"]:
            f.write(f"### Typology: `{typo['typology']}`\n")
            f.write(f"- **Description**: {typo['description']}\n")
            f.write(f"- **Primary Wallet**: `{typo['primary_wallet']}`\n")
            f.write(f"- **Suspicious IP**: `{typo['suspicious_ip']}`\n")
            f.write(f"- **Transaction Count**: `{typo['count']}`\n")
            f.write(f"- **Transactions**: {', '.join(f'`{t}`' for t in typo['txids'])}\n\n")

        f.write("## 2. Illicit Entity Summary\n\n")
        f.write("### Target Suspicious Wallets:\n")
        for w in ground_truth["illicit_entities"]["wallets"]:
            f.write(f"- `{w['address']}` ({w['role']} - {w['typology']})\n")

        f.write("\n### Suspicious Network Originating IPs:\n")
        for ip in ground_truth["illicit_entities"]["ips"]:
            f.write(f"- `{ip['ip']}` ({ip['description']} [{ip['country']} / {ip['asn']}])\n")

        f.write("\n## 3. Sample Licit Transactions\n\n")
        f.write("First 15 normal transactions (should score LOW priority):\n")
        for t in ground_truth["licit_sample"]["transactions"]:
            f.write(f"- `{t}`\n")

    print(f"Generated {len(transactions_list)} transactions:")
    print(f"  - Licit:   {licit_tx_count}")
    print(f"  - Illicit: {len(all_illicit_txids)}")
    print(f"  - Inputs:  {len(inputs_list)}")
    print(f"  - Outputs: {len(outputs_list)}")
    print(f"  - Network: {len(network_list)}")
    print(f"Saved canonical files to {out_path}")
    print(f"Saved ground truth to {gt_json_path} and {gt_md_path}")


if __name__ == "__main__":
    generate_synthetic_data()

