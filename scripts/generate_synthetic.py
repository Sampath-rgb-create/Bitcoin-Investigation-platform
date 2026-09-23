import csv
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Tuple


def random_btc_address(prefix: str = "bc1q") -> str:
    chars = "023456789acdefghjklmnpqrstuvwxyz"
    return prefix + "".join(random.choices(chars, k=38))


def random_ip() -> str:
    # Public IPv4 generator avoiding private ranges
    return f"{random.randint(11, 190)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"


def generate_synthetic_data(
    output_dir: str = "d:/Bitcoin-Investigation-platform/data/samples",
    total_normal_txs: int = 200,
    seed: int = 42,
) -> Tuple[str, str, str]:
    """
    Generates synthetic Bitcoin transactions and network observations.
    Plants known typologies with ground truth:
    1. Peeling Chain: Sequential small transfers with change address.
    2. Dust Flood: High-frequency sub-dust outputs sent to dozens of addresses.
    3. Rapid Dispersal: 1 input split into 20+ outputs within seconds.
    """
    random.seed(seed)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    start_time = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    current_time = start_time

    transactions: List[Dict] = []
    network_observations: List[Dict] = []
    ground_truth: List[Dict] = []

    wallet_pool = [random_btc_address() for _ in range(50)]
    ip_pool = [random_ip() for _ in range(25)]

    # 1. Normal Transactions
    for i in range(total_normal_txs):
        tx_id = f"tx_norm_{i:06d}"
        current_time += timedelta(seconds=random.randint(5, 120))
        sender = random.choice(wallet_pool)
        receiver = random.choice([w for w in wallet_pool if w != sender])
        amt = round(random.uniform(0.01, 2.5), 6)
        fee = 0.0001

        tx_record = {
            "record_id": f"tx-rec-{len(transactions):06d}",
            "timestamp": current_time.isoformat(),
            "txid": tx_id,
            "input_addresses": [sender],
            "output_addresses": [receiver],
            "input_amounts": [amt + fee],
            "output_amounts": [amt],
            "fee": fee,
            "script_type": "P2WPKH",
        }
        transactions.append(tx_record)

        # Correlated Network Observation
        if random.random() > 0.15:  # 85% network observation rate
            src_ip = random.choice(ip_pool)
            dst_ip = random.choice([ip for ip in ip_pool if ip != src_ip])
            net_record = {
                "record_id": f"net-rec-{len(network_observations):06d}",
                "timestamp": (current_time + timedelta(milliseconds=random.randint(100, 1500))).isoformat(),
                "txid": tx_id,
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "src_port": random.randint(40000, 60000),
                "dst_port": 8333,
                "geo_country": "US",
                "asn": "AS15169",
            }
            network_observations.append(net_record)

    # 2. Planted Typology: Peeling Chain (5 hops)
    peel_wallet = random_btc_address("bc1q_peel_")
    peel_ip = "198.51.100.42"
    remaining_balance = 10.0
    ground_truth.append({
        "typology": "peeling_chain",
        "primary_entity": f"wallet:{peel_wallet}",
        "description": "Sequential peel chain offloading 0.5 BTC each hop with change",
    })

    current_wallet = peel_wallet
    for step in range(5):
        tx_id = f"tx_peel_{step:03d}"
        current_time += timedelta(seconds=12)
        peel_amount = 0.5
        change_amount = round(remaining_balance - peel_amount - 0.0002, 6)
        next_change_wallet = random_btc_address("bc1q_peel_")
        recipient = random.choice(wallet_pool)

        tx_record = {
            "record_id": f"tx-rec-{len(transactions):06d}",
            "timestamp": current_time.isoformat(),
            "txid": tx_id,
            "input_addresses": [current_wallet],
            "output_addresses": [recipient, next_change_wallet],
            "input_amounts": [remaining_balance],
            "output_amounts": [peel_amount, change_amount],
            "fee": 0.0002,
            "script_type": "P2WPKH",
        }
        transactions.append(tx_record)

        net_record = {
            "record_id": f"net-rec-{len(network_observations):06d}",
            "timestamp": (current_time + timedelta(milliseconds=250)).isoformat(),
            "txid": tx_id,
            "src_ip": peel_ip,
            "dst_ip": random.choice(ip_pool),
            "src_port": 50123,
            "dst_port": 8333,
            "geo_country": "NL",
            "asn": "AS1103",
        }
        network_observations.append(net_record)

        remaining_balance = change_amount
        current_wallet = next_change_wallet

    # 3. Planted Typology: Dust Flood (25 rapid sub-dust transactions)
    dust_source = random_btc_address("bc1q_dust_source_")
    dust_ip = "203.0.113.99"
    ground_truth.append({
        "typology": "dust_flood",
        "primary_entity": f"wallet:{dust_source}",
        "description": "Burst of 25 sub-dust transactions at high rate",
    })

    for step in range(25):
        tx_id = f"tx_dust_{step:03d}"
        current_time += timedelta(milliseconds=400)  # ~2.5 tx/sec
        target_wallet = random_btc_address()

        tx_record = {
            "record_id": f"tx-rec-{len(transactions):06d}",
            "timestamp": current_time.isoformat(),
            "txid": tx_id,
            "input_addresses": [dust_source],
            "output_addresses": [target_wallet],
            "input_amounts": [0.00005500],
            "output_amounts": [0.00005460],
            "fee": 0.00000040,
            "script_type": "P2WPKH",
        }
        transactions.append(tx_record)

        net_record = {
            "record_id": f"net-rec-{len(network_observations):06d}",
            "timestamp": current_time.isoformat(),
            "txid": tx_id,
            "src_ip": dust_ip,
            "dst_ip": random.choice(ip_pool),
            "src_port": 49152,
            "dst_port": 8333,
            "geo_country": "RU",
            "asn": "AS12389",
        }
        network_observations.append(net_record)

    # 4. Planted Typology: Rapid Dispersal (1 input to 30 outputs)
    dispersal_source = random_btc_address("bc1q_dispersal_")
    ground_truth.append({
        "typology": "rapid_dispersal",
        "primary_entity": f"wallet:{dispersal_source}",
        "description": "High fan-out dispersal sending 1 input to 30 outputs simultaneously",
    })

    tx_id = "tx_dispersal_001"
    current_time += timedelta(minutes=5)
    disp_outputs = [random_btc_address() for _ in range(30)]
    disp_amounts = [0.1 for _ in range(30)]
    disp_total = sum(disp_amounts) + 0.0005

    tx_record = {
        "record_id": f"tx-rec-{len(transactions):06d}",
        "timestamp": current_time.isoformat(),
        "txid": tx_id,
        "input_addresses": [dispersal_source],
        "output_addresses": disp_outputs,
        "input_amounts": [round(disp_total, 6)],
        "output_amounts": disp_amounts,
        "fee": 0.0005,
        "script_type": "P2WPKH",
    }
    transactions.append(tx_record)

    net_record = {
        "record_id": f"net-rec-{len(network_observations):06d}",
        "timestamp": current_time.isoformat(),
        "txid": tx_id,
        "src_ip": "192.0.2.77",
        "dst_ip": random.choice(ip_pool),
        "src_port": 54321,
        "dst_port": 8333,
        "geo_country": "DE",
        "asn": "AS24940",
    }
    network_observations.append(net_record)

    # Write files
    tx_file = out_path / "synthetic_transactions.json"
    net_file = out_path / "synthetic_network.json"
    combined_csv_file = out_path / "synthetic_combined.csv"
    gt_file = out_path / "ground_truth.json"

    with open(tx_file, "w", encoding="utf-8") as f:
        json.dump(transactions, f, indent=2)

    with open(net_file, "w", encoding="utf-8") as f:
        json.dump(network_observations, f, indent=2)

    with open(gt_file, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)

    # Also export combined CSV
    # Map network observations by txid
    net_map = {n["txid"]: n for n in network_observations if n.get("txid")}
    with open(combined_csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "record_id", "timestamp", "txid", "input_addresses", "output_addresses",
            "input_amounts", "output_amounts", "fee", "script_type", "src_ip", "dst_ip",
            "src_port", "dst_port", "geo_country", "asn"
        ])
        for tx in transactions:
            net = net_map.get(tx["txid"], {})
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

    print(f"Generated {len(transactions)} transactions -> {tx_file}")
    print(f"Generated {len(network_observations)} network telemetry records -> {net_file}")
    print(f"Generated combined CSV -> {combined_csv_file}")
    print(f"Generated ground truth anomalies -> {gt_file}")

    return str(tx_file), str(net_file), str(gt_file)


if __name__ == "__main__":
    generate_synthetic_data()
