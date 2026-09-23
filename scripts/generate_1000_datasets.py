"""
Script to generate large-scale synthetic Bitcoin transactions and network telemetry CSV files.
Generates:
1. transactions.csv (1000 records)
2. network_telemetry.csv (1000 records)

Includes realistic Bitcoin topologies and forensic anomalies:
- Normal P2P transfers
- Peeling chain patterns
- Rapid dispersal / fan-out
- Dust floods (< 546 satoshis)
- High fee structuring anomalies
- Tor / Proxy relay bursts
"""

import csv
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


def random_btc_address(prefix: str = "bc1q") -> str:
    chars = "023456789acdefghjklmnpqrstuvwxyz"
    return prefix + "".join(random.choices(chars, k=38))


def random_ip() -> str:
    # Public IPv4 generator avoiding private ranges
    return f"{random.randint(11, 190)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"


DEFAULT_OUTPUT_DIR = str(Path(__file__).resolve().parent.parent / "data" / "samples")


def generate_1000_datasets(
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
    network_observations = []
    ground_truth = []

    # -------------------------------------------------------------------------
    # 1. Planted Anomaly 1: Peeling Chain (50 hops)
    # -------------------------------------------------------------------------
    peel_source = random_btc_address("bc1qpeel")
    peel_destinations = [random_btc_address("bc1qpeelhop") for _ in range(50)]
    peel_balance = 50.0

    gt_peel = {
        "scenario": "Peeling Chain",
        "description": "Sequential small peel amounts from single funding source",
        "txids": [],
    }

    for hop_idx in range(50):
        current_time += timedelta(seconds=random.randint(30, 90))
        peel_amt = round(random.uniform(0.05, 0.25), 6)
        fee = 0.0001
        change_amt = round(peel_balance - peel_amt - fee, 6)
        if change_amt <= 0:
            break

        tx_id = f"tx_peel_{hop_idx:04d}"
        gt_peel["txids"].append(tx_id)

        recipient = peel_destinations[hop_idx]
        next_change_wallet = random_btc_address("bc1qpeel")

        tx_record = {
            "record_id": f"tx-rec-{len(transactions):06d}",
            "timestamp": current_time.isoformat(),
            "txid": tx_id,
            "input_addresses": [peel_source],
            "output_addresses": [recipient, next_change_wallet],
            "input_amounts": [peel_balance],
            "output_amounts": [peel_amt, change_amt],
            "fee": fee,
            "script_type": "P2WPKH",
        }
        transactions.append(tx_record)

        net_record = {
            "record_id": f"net-rec-{len(network_observations):06d}",
            "timestamp": current_time.isoformat(),
            "txid": tx_id,
            "src_ip": "198.51.100.42",
            "dst_ip": random.choice(ip_pool),
            "src_port": random.randint(40000, 60000),
            "dst_port": 8333,
            "geo_country": "CH",
            "asn": "AS13335",
        }
        network_observations.append(net_record)

        peel_source = next_change_wallet
        peel_balance = change_amt

    ground_truth.append(gt_peel)

    # -------------------------------------------------------------------------
    # 2. Planted Anomaly 2: Rapid Fan-Out Dispersal (1 input to 40 outputs)
    # -------------------------------------------------------------------------
    disp_sender = random_btc_address("bc1qfanout")
    disp_txid = "tx_fanout_dispersal_001"
    disp_recipients = [random_btc_address("bc1qmule") for _ in range(40)]
    disp_amts = [0.25] * 40
    disp_tot = sum(disp_amts)
    disp_fee = 0.002

    current_time += timedelta(minutes=5)
    tx_fanout = {
        "record_id": f"tx-rec-{len(transactions):06d}",
        "timestamp": current_time.isoformat(),
        "txid": disp_txid,
        "input_addresses": [disp_sender],
        "output_addresses": disp_recipients,
        "input_amounts": [disp_tot + disp_fee],
        "output_amounts": disp_amts,
        "fee": disp_fee,
        "script_type": "P2WSH",
    }
    transactions.append(tx_fanout)

    # Correlated Tor relay observation
    net_fanout = {
        "record_id": f"net-rec-{len(network_observations):06d}",
        "timestamp": current_time.isoformat(),
        "txid": disp_txid,
        "src_ip": "185.220.101.5",
        "dst_ip": random.choice(ip_pool),
        "src_port": 9050,  # Tor socks port
        "dst_port": 8333,
        "geo_country": "DE",
        "asn": "AS24940",
    }
    network_observations.append(net_fanout)
    ground_truth.append({
        "scenario": "Rapid Fan-Out Dispersal",
        "description": "1 input split into 40 recipient addresses simultaneously via Tor relay",
        "txids": [disp_txid],
    })

    # -------------------------------------------------------------------------
    # 3. Planted Anomaly 3: Dust Flood (60 micro-transfers)
    # -------------------------------------------------------------------------
    dust_victim = random_btc_address("bc1qdusttarget")
    dust_attacker = random_btc_address("bc1qattacker")

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

        tx_d = {
            "record_id": f"tx-rec-{len(transactions):06d}",
            "timestamp": current_time.isoformat(),
            "txid": d_txid,
            "input_addresses": [dust_attacker],
            "output_addresses": [dust_victim],
            "input_amounts": [d_amt + 0.00005],
            "output_amounts": [d_amt],
            "fee": 0.00005,
            "script_type": "P2PKH",
        }
        transactions.append(tx_d)

        net_d = {
            "record_id": f"net-rec-{len(network_observations):06d}",
            "timestamp": current_time.isoformat(),
            "txid": d_txid,
            "src_ip": "203.0.113.88",
            "dst_ip": random.choice(ip_pool),
            "src_port": random.randint(50000, 60000),
            "dst_port": 8333,
            "geo_country": "NL",
            "asn": "AS16509",
        }
        network_observations.append(net_d)

    ground_truth.append(gt_dust)

    # -------------------------------------------------------------------------
    # 4. Planted Anomaly 4: Excessive Fee Anomaly (20 transactions)
    # -------------------------------------------------------------------------
    for f_idx in range(20):
        current_time += timedelta(minutes=random.randint(1, 4))
        f_txid = f"tx_fee_anomaly_{f_idx:04d}"
        in_amt = round(random.uniform(0.5, 2.0), 4)
        fee = round(in_amt * random.uniform(0.40, 0.65), 4)  # 40-65% fee
        out_amt = round(in_amt - fee, 4)

        tx_f = {
            "record_id": f"tx-rec-{len(transactions):06d}",
            "timestamp": current_time.isoformat(),
            "txid": f_txid,
            "input_addresses": [random.choice(wallet_pool)],
            "output_addresses": [random.choice(wallet_pool)],
            "input_amounts": [in_amt],
            "output_amounts": [out_amt],
            "fee": fee,
            "script_type": "P2WPKH",
        }
        transactions.append(tx_f)

        net_f = {
            "record_id": f"net-rec-{len(network_observations):06d}",
            "timestamp": current_time.isoformat(),
            "txid": f_txid,
            "src_ip": random.choice(ip_pool),
            "dst_ip": random.choice(ip_pool),
            "src_port": random.randint(30000, 50000),
            "dst_port": 8333,
            "geo_country": random.choice(countries),
            "asn": random.choice(asns),
        }
        network_observations.append(net_f)

    # -------------------------------------------------------------------------
    # 5. Populate Remaining to reach exactly 1000 Transactions & Telemetry
    # -------------------------------------------------------------------------
    remaining_txs = target_count - len(transactions)
    for i in range(remaining_txs):
        current_time += timedelta(seconds=random.randint(5, 60))
        tx_id = f"tx_norm_{len(transactions):06d}"

        sender = random.choice(wallet_pool)
        receiver = random.choice([w for w in wallet_pool if w != sender])
        amt = round(random.uniform(0.005, 3.85), 6)
        fee = 0.00012

        # 30% of transactions have change outputs
        if random.random() < 0.30:
            change_addr = random.choice([w for w in wallet_pool if w not in (sender, receiver)])
            total_input = round(amt + random.uniform(0.1, 1.5) + fee, 6)
            change_amt = round(total_input - amt - fee, 6)
            in_addrs = [sender]
            in_amts = [total_input]
            out_addrs = [receiver, change_addr]
            out_amts = [amt, change_amt]
        else:
            in_addrs = [sender]
            in_amts = [round(amt + fee, 6)]
            out_addrs = [receiver]
            out_amts = [amt]

        tx_record = {
            "record_id": f"tx-rec-{len(transactions):06d}",
            "timestamp": current_time.isoformat(),
            "txid": tx_id,
            "input_addresses": in_addrs,
            "output_addresses": out_addrs,
            "input_amounts": in_amts,
            "output_amounts": out_amts,
            "fee": fee,
            "script_type": random.choice(["P2PKH", "P2SH", "P2WPKH", "P2TR"]),
        }
        transactions.append(tx_record)

    remaining_net = target_count - len(network_observations)
    tx_list = [t["txid"] for t in transactions]

    for i in range(remaining_net):
        current_time += timedelta(seconds=random.randint(3, 45))
        # 85% correlated with known txid, 15% temporal broadcast telemetry
        associated_txid = random.choice(tx_list) if random.random() < 0.85 else ""

        src_ip = random.choice(ip_pool)
        # 5% VPN / Proxy port anomalies
        src_port = random.choice([1194, 9050, 443, 8080]) if random.random() < 0.05 else random.randint(20000, 60000)

        net_record = {
            "record_id": f"net-rec-{len(network_observations):06d}",
            "timestamp": current_time.isoformat(),
            "txid": associated_txid,
            "src_ip": src_ip,
            "dst_ip": random.choice(ip_pool),
            "src_port": src_port,
            "dst_port": 8333,
            "geo_country": random.choice(countries),
            "asn": random.choice(asns),
        }
        network_observations.append(net_record)

    # -------------------------------------------------------------------------
    # Write CSV Output Files
    # -------------------------------------------------------------------------
    tx_csv = out_path / "transactions_1000.csv"
    net_csv = out_path / "network_telemetry_1000.csv"
    combined_csv = out_path / "combined_1000.csv"
    gt_json = out_path / "ground_truth_1000.json"

    # 1. transactions.csv
    with open(tx_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "record_id",
            "timestamp",
            "txid",
            "input_addresses",
            "output_addresses",
            "input_amounts",
            "output_amounts",
            "fee",
            "script_type",
        ])
        for tx in transactions:
            writer.writerow([
                tx["record_id"],
                tx["timestamp"],
                tx["txid"],
                json.dumps(tx["input_addresses"]),
                json.dumps(tx["output_addresses"]),
                json.dumps(tx["input_amounts"]),
                json.dumps(tx["output_amounts"]),
                tx["fee"],
                tx["script_type"],
            ])

    # 2. network_telemetry.csv
    with open(net_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "record_id",
            "timestamp",
            "txid",
            "src_ip",
            "dst_ip",
            "src_port",
            "dst_port",
            "geo_country",
            "asn",
        ])
        for net in network_observations:
            writer.writerow([
                net["record_id"],
                net["timestamp"],
                net["txid"],
                net["src_ip"],
                net["dst_ip"],
                net["src_port"],
                net["dst_port"],
                net["geo_country"],
                net["asn"],
            ])

    # 3. combined_1000.csv
    net_by_txid = {n["txid"]: n for n in network_observations if n["txid"]}
    with open(combined_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "record_id",
            "timestamp",
            "txid",
            "input_addresses",
            "output_addresses",
            "input_amounts",
            "output_amounts",
            "fee",
            "script_type",
            "src_ip",
            "dst_ip",
            "src_port",
            "dst_port",
            "geo_country",
            "asn",
        ])
        for tx in transactions:
            net = net_by_txid.get(tx["txid"], {})
            writer.writerow([
                tx["record_id"],
                tx["timestamp"],
                tx["txid"],
                json.dumps(tx["input_addresses"]),
                json.dumps(tx["output_addresses"]),
                json.dumps(tx["input_amounts"]),
                json.dumps(tx["output_amounts"]),
                tx["fee"],
                tx["script_type"],
                net.get("src_ip", ""),
                net.get("dst_ip", ""),
                net.get("src_port", ""),
                net.get("dst_port", ""),
                net.get("geo_country", ""),
                net.get("asn", ""),
            ])

    # 4. ground_truth_1000.json
    with open(gt_json, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)

    print(f"Generated {len(transactions)} transactions -> {tx_csv}")
    print(f"Generated {len(network_observations)} network telemetry records -> {net_csv}")
    print(f"Generated combined CSV -> {combined_csv}")
    print(f"Generated ground truth anomalies -> {gt_json}")

    return str(tx_csv), str(net_csv)


if __name__ == "__main__":
    generate_1000_datasets()

