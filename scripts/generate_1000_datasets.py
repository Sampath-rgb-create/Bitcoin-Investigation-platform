"""
New Prototype Dataset Generator for Bitcoin Investigation Platform.

Outputs the 4 canonical forensic input files specified in ELLIPTIC_CASE_GENERATOR_CONTRACT.md:
1. transactions.csv: (txid, timestamp, fee, size, version, locktime)
2. inputs.csv: (txid, input_index, prev_txid, prev_vout, address, amount, script_type)
3. outputs.csv: (txid, output_index, address, amount, script_type)
4. network.csv: (txid, timestamp, src_ip, src_port, dst_ip, dst_port, asn, country)
5. ground_truth.json: Scenario metadata with planted illicit & licit breakdown.
"""

import csv
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Tuple


def random_btc_address(prefix: str = "bc1q") -> str:
    chars = "023456789acdefghjklmnpqrstuvwxyz"
    return prefix + "".join(random.choices(chars, k=38))


def random_ip() -> str:
    return f"{random.randint(11, 190)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"


DEFAULT_OUTPUT_DIR = str(Path(__file__).resolve().parent.parent / "data" / "samples")


def generate_new_prototype_datasets(
    output_dir: str = DEFAULT_OUTPUT_DIR,
    target_count: int = 1000,
    seed: int = 42,
):
    random.seed(seed)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    start_time = datetime(2026, 3, 1, 8, 0, 0, tzinfo=timezone.utc)
    current_time = start_time

    wallet_pool = [random_btc_address() for _ in range(120)]
    ip_pool = [random_ip() for _ in range(60)]
    countries = ["US", "DE", "SG", "NL", "IN", "GB", "CH", "JP", "CA", "FR"]
    asns = ["AS15169", "AS16509", "AS13335", "AS24940", "AS8075", "AS9009"]

    transactions = []
    inputs = []
    outputs = []
    network = []
    ground_truth = []

    # Map to track UTXOs created: (txid, vout) -> (address, amount)
    available_utxos: List[Tuple[str, int, str, float]] = []

    # Initial funding transactions for wallet pool
    for idx, w in enumerate(wallet_pool[:40]):
        f_txid = f"tx_genesis_{idx:04d}"
        f_amt = round(random.uniform(5.0, 50.0), 4)
        transactions.append({
            "txid": f_txid,
            "timestamp": (start_time - timedelta(hours=24)).isoformat(),
            "fee": 0.0,
            "size": 180,
            "version": 1,
            "locktime": 0,
        })
        outputs.append({
            "txid": f_txid,
            "output_index": 0,
            "address": w,
            "amount": f_amt,
            "script_type": "p2wpkh",
        })
        available_utxos.append((f_txid, 0, w, f_amt))

    # -------------------------------------------------------------------------
    # 1. Planted Anomaly 1: Peeling Chain (50 hops)
    # -------------------------------------------------------------------------
    peel_source_wallet = random_btc_address("bc1qpeelsrc")
    peel_fund_txid = "tx_peel_fund_0000"
    peel_initial_fund = 45.0
    transactions.append({
        "txid": peel_fund_txid,
        "timestamp": current_time.isoformat(),
        "fee": 0.0001,
        "size": 225,
        "version": 1,
        "locktime": 0,
    })
    outputs.append({
        "txid": peel_fund_txid,
        "output_index": 0,
        "address": peel_source_wallet,
        "amount": peel_initial_fund,
        "script_type": "p2wpkh",
    })
    prev_peel_txid = peel_fund_txid
    prev_peel_vout = 0
    cur_peel_addr = peel_source_wallet
    cur_peel_amt = peel_initial_fund

    gt_peel = {
        "scenario": "Peeling Chain",
        "description": "Sequential small peel amounts from single funding source",
        "txids": [],
    }

    for hop in range(50):
        current_time += timedelta(seconds=random.randint(45, 120))
        tx_id = f"tx_peel_{hop:04d}"
        gt_peel["txids"].append(tx_id)

        peel_out_amt = round(random.uniform(0.05, 0.25), 6)
        fee = 0.0001
        change_amt = round(cur_peel_amt - peel_out_amt - fee, 6)
        if change_amt <= 0:
            break

        next_change_addr = random_btc_address(f"bc1qchange{hop:02d}")
        peel_dest_addr = random_btc_address(f"bc1qpeeldest{hop:02d}")

        transactions.append({
            "txid": tx_id,
            "timestamp": current_time.isoformat(),
            "fee": fee,
            "size": 225,
            "version": 1,
            "locktime": 0,
        })
        inputs.append({
            "txid": tx_id,
            "input_index": 0,
            "prev_txid": prev_peel_txid,
            "prev_vout": prev_peel_vout,
            "address": cur_peel_addr,
            "amount": cur_peel_amt,
            "script_type": "p2wpkh",
        })
        outputs.append({
            "txid": tx_id,
            "output_index": 0,
            "address": peel_dest_addr,
            "amount": peel_out_amt,
            "script_type": "p2wpkh",
        })
        outputs.append({
            "txid": tx_id,
            "output_index": 1,
            "address": next_change_addr,
            "amount": change_amt,
            "script_type": "p2wpkh",
        })
        network.append({
            "txid": tx_id,
            "timestamp": (current_time + timedelta(milliseconds=200)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "src_ip": "185.220.101.5",  # Tor exit node
            "src_port": 9050,
            "dst_ip": random.choice(ip_pool),
            "dst_port": 8333,
            "asn": "AS24940",
            "country": "DE",
        })

        prev_peel_txid = tx_id
        prev_peel_vout = 1
        cur_peel_addr = next_change_addr
        cur_peel_amt = change_amt

    ground_truth.append(gt_peel)

    # -------------------------------------------------------------------------
    # 2. Planted Anomaly 2: Rapid Fan-Out Dispersal (1 tx -> 40 outputs)
    # -------------------------------------------------------------------------
    current_time += timedelta(minutes=5)
    fanout_txid = "tx_fanout_0000"
    gt_fanout = {
        "scenario": "Rapid Fan-Out Dispersal",
        "description": "1 input split into 40 recipient addresses simultaneously via Tor relay",
        "txids": [fanout_txid],
    }

    fan_in_amt = 10.0
    fan_fee = 0.002
    fan_out_amt = round((fan_in_amt - fan_fee) / 40, 6)

    transactions.append({
        "txid": fanout_txid,
        "timestamp": current_time.isoformat(),
        "fee": fan_fee,
        "size": 1420,
        "version": 1,
        "locktime": 0,
    })
    fan_src = random_btc_address("bc1qfansrc")
    inputs.append({
        "txid": fanout_txid,
        "input_index": 0,
        "prev_txid": "tx_genesis_0001",
        "prev_vout": 0,
        "address": fan_src,
        "amount": fan_in_amt,
        "script_type": "p2wpkh",
    })
    for vout_idx in range(40):
        outputs.append({
            "txid": fanout_txid,
            "output_index": vout_idx,
            "address": random_btc_address(f"bc1qfanout{vout_idx:02d}"),
            "amount": fan_out_amt,
            "script_type": "p2wpkh",
        })

    network.append({
        "txid": fanout_txid,
        "timestamp": current_time.isoformat(),
        "src_ip": "185.220.101.5",
        "src_port": 9050,
        "dst_ip": random.choice(ip_pool),
        "dst_port": 8333,
        "asn": "AS24940",
        "country": "DE",
    })
    ground_truth.append(gt_fanout)

    # -------------------------------------------------------------------------
    # 3. Planted Anomaly 3: Dust Flood (60 sub-dust transactions)
    # -------------------------------------------------------------------------
    dust_attacker = random_btc_address("bc1qdustatk")
    dust_victim = random_btc_address("bc1qdustvic")
    gt_dust = {
        "scenario": "Dust Attack Flood",
        "description": "Flood of sub-dust threshold transactions under 546 sats",
        "txids": [],
    }

    for d_idx in range(60):
        current_time += timedelta(seconds=random.randint(1, 3))
        d_txid = f"tx_dust_{d_idx:04d}"
        gt_dust["txids"].append(d_txid)
        d_amt = 0.00000300  # 300 satoshis (sub-dust)

        transactions.append({
            "txid": d_txid,
            "timestamp": current_time.isoformat(),
            "fee": 0.00005,
            "size": 192,
            "version": 1,
            "locktime": 0,
        })
        inputs.append({
            "txid": d_txid,
            "input_index": 0,
            "prev_txid": "tx_genesis_0002",
            "prev_vout": 0,
            "address": dust_attacker,
            "amount": d_amt + 0.00005,
            "script_type": "p2pkh",
        })
        outputs.append({
            "txid": d_txid,
            "output_index": 0,
            "address": dust_victim,
            "amount": d_amt,
            "script_type": "p2pkh",
        })
        network.append({
            "txid": d_txid,
            "timestamp": current_time.isoformat(),
            "src_ip": "203.0.113.88",
            "src_port": random.randint(50000, 60000),
            "dst_ip": random.choice(ip_pool),
            "dst_port": 8333,
            "asn": "AS16509",
            "country": "NL",
        })
    ground_truth.append(gt_dust)

    # -------------------------------------------------------------------------
    # 4. Planted Anomaly 4: High Fee Structuring (20 transactions)
    # -------------------------------------------------------------------------
    gt_fee = {
        "scenario": "Excessive Fee Structuring",
        "description": "Anomalously high mining fee ratio (40-65% of volume)",
        "txids": [],
    }
    for f_idx in range(20):
        current_time += timedelta(minutes=random.randint(1, 4))
        f_txid = f"tx_fee_struct_{f_idx:04d}"
        gt_fee["txids"].append(f_txid)
        in_amt = round(random.uniform(0.5, 2.0), 4)
        fee = round(in_amt * random.uniform(0.40, 0.65), 4)
        out_amt = round(in_amt - fee, 4)

        transactions.append({
            "txid": f_txid,
            "timestamp": current_time.isoformat(),
            "fee": fee,
            "size": 225,
            "version": 1,
            "locktime": 0,
        })
        inputs.append({
            "txid": f_txid,
            "input_index": 0,
            "prev_txid": "tx_genesis_0003",
            "prev_vout": 0,
            "address": random.choice(wallet_pool),
            "amount": in_amt,
            "script_type": "p2wpkh",
        })
        outputs.append({
            "txid": f_txid,
            "output_index": 0,
            "address": random.choice(wallet_pool),
            "amount": out_amt,
            "script_type": "p2wpkh",
        })
        network.append({
            "txid": f_txid,
            "timestamp": current_time.isoformat(),
            "src_ip": random.choice(ip_pool),
            "src_port": random.randint(30000, 50000),
            "dst_ip": random.choice(ip_pool),
            "dst_port": 8333,
            "asn": random.choice(asns),
            "country": random.choice(countries),
        })
    ground_truth.append(gt_fee)

    # -------------------------------------------------------------------------
    # 5. Populate Remaining to reach exactly 1000 Transactions (Licit transfers)
    # -------------------------------------------------------------------------
    existing_count = len(transactions)
    remaining_txs = target_count - existing_count

    for i in range(remaining_txs):
        current_time += timedelta(seconds=random.randint(10, 60))
        tx_id = f"tx_licit_{i:06d}"

        sender = random.choice(wallet_pool)
        receiver = random.choice([w for w in wallet_pool if w != sender])
        amt = round(random.uniform(0.01, 3.5), 6)
        fee = round(random.uniform(0.00005, 0.00025), 6)

        # Standard 1-in 2-out or 1-in 1-out transfer
        is_two_out = random.random() > 0.35
        change_addr = sender if is_two_out else None
        change_amt = round(random.uniform(0.005, 0.5), 6) if is_two_out else 0.0
        tot_in = amt + change_amt + fee

        transactions.append({
            "txid": tx_id,
            "timestamp": current_time.isoformat(),
            "fee": fee,
            "size": 225 if is_two_out else 192,
            "version": 1,
            "locktime": 0,
        })
        inputs.append({
            "txid": tx_id,
            "input_index": 0,
            "prev_txid": "tx_genesis_0000",
            "prev_vout": 0,
            "address": sender,
            "amount": tot_in,
            "script_type": "p2wpkh",
        })
        outputs.append({
            "txid": tx_id,
            "output_index": 0,
            "address": receiver,
            "amount": amt,
            "script_type": "p2wpkh",
        })
        if is_two_out and change_addr:
            outputs.append({
                "txid": tx_id,
                "output_index": 1,
                "address": change_addr,
                "amount": change_amt,
                "script_type": "p2wpkh",
            })

        network.append({
            "txid": tx_id,
            "timestamp": (current_time + timedelta(milliseconds=random.randint(50, 450))).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "src_ip": random.choice(ip_pool),
            "src_port": random.randint(1024, 65535),
            "dst_ip": random.choice(ip_pool),
            "dst_port": 8333,
            "asn": random.choice(asns),
            "country": random.choice(countries),
        })

    # -------------------------------------------------------------------------
    # Write New Prototype Canonical Files (transactions.csv, inputs.csv, outputs.csv, network.csv)
    # -------------------------------------------------------------------------
    tx_file = out_path / "transactions.csv"
    inp_file = out_path / "inputs.csv"
    out_file = out_path / "outputs.csv"
    net_file = out_path / "network.csv"
    gt_file = out_path / "ground_truth.json"

    # Also keep backward-compatible files for legacy single-dropzone testing
    comb_file = out_path / "combined_1000.csv"
    tx1000_file = out_path / "transactions_1000.csv"
    net1000_file = out_path / "network_telemetry_1000.csv"

    # 1. transactions.csv
    with open(tx_file, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["txid", "timestamp", "fee", "size", "version", "locktime"])
        for t in transactions:
            w.writerow([t["txid"], t["timestamp"], t["fee"], t["size"], t["version"], t["locktime"]])

    # 2. inputs.csv
    with open(inp_file, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["txid", "input_index", "prev_txid", "prev_vout", "address", "amount", "script_type"])
        for inp in inputs:
            w.writerow([inp["txid"], inp["input_index"], inp["prev_txid"], inp["prev_vout"], inp["address"], inp["amount"], inp["script_type"]])

    # 3. outputs.csv
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["txid", "output_index", "address", "amount", "script_type"])
        for o in outputs:
            w.writerow([o["txid"], o["output_index"], o["address"], o["amount"], o["script_type"]])

    # 4. network.csv
    with open(net_file, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["txid", "timestamp", "src_ip", "src_port", "dst_ip", "dst_port", "asn", "country"])
        for n in network:
            w.writerow([n["txid"], n["timestamp"], n["src_ip"], n["src_port"], n["dst_ip"], n["dst_port"], n["asn"], n["country"]])

    # 5. ground_truth.json
    with open(gt_file, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)

    # 6. Build combined_1000.csv, transactions_1000.csv, and network_telemetry_1000.csv for multi-format compatibility
    # Group inputs and outputs by txid
    tx_in_map = {}
    for inp in inputs:
        tx_in_map.setdefault(inp["txid"], []).append(inp)
    tx_out_map = {}
    for o in outputs:
        tx_out_map.setdefault(o["txid"], []).append(o)
    net_map = {n["txid"]: n for n in network}

    with open(comb_file, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "record_id", "timestamp", "txid",
            "input_addresses", "output_addresses", "input_amounts", "output_amounts",
            "fee", "script_type", "src_ip", "dst_ip", "src_port", "dst_port", "geo_country", "asn"
        ])
        for idx, t in enumerate(transactions):
            txid = t["txid"]
            in_list = tx_in_map.get(txid, [])
            out_list = tx_out_map.get(txid, [])
            net_item = net_map.get(txid, {})
            w.writerow([
                f"rec-{idx:06d}",
                t["timestamp"],
                txid,
                json.dumps([x["address"] for x in in_list]),
                json.dumps([x["address"] for x in out_list]),
                json.dumps([x["amount"] for x in in_list]),
                json.dumps([x["amount"] for x in out_list]),
                t["fee"],
                in_list[0]["script_type"] if in_list else "p2wpkh",
                net_item.get("src_ip", ""),
                net_item.get("dst_ip", ""),
                net_item.get("src_port", ""),
                net_item.get("dst_port", ""),
                net_item.get("country", ""),
                net_item.get("asn", ""),
            ])

    # Copy to transactions_1000.csv and network_telemetry_1000.csv
    import shutil
    shutil.copyfile(tx_file, tx1000_file)
    shutil.copyfile(net_file, net1000_file)
    shutil.copyfile(gt_file, out_path / "ground_truth_1000.json")

    print(f"Generated new prototype canonical datasets in {out_path}:")
    print(f"  - transactions.csv: {len(transactions)} records")
    print(f"  - inputs.csv:       {len(inputs)} records")
    print(f"  - outputs.csv:      {len(outputs)} records")
    print(f"  - network.csv:      {len(network)} records")
    print(f"  - ground_truth.json: {len(ground_truth)} scenarios")


if __name__ == "__main__":
    generate_new_prototype_datasets()
