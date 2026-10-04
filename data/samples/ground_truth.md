# Forensic Dataset Ground Truth & Anomaly Catalog

- **Generated At**: `2026-10-03T21:58:52.698836+00:00`
- **Total Transactions**: `180`
- **Licit Transactions**: `150` (Normal daily commerce)
- **Illicit Transactions**: `30` (Planted anomalies)

## 1. Planted Illicit Typologies

### Typology: `PEELING_CHAIN`
- **Description**: Sequential rapid offloading of 0.75 BTC per hop across 8 continuous hops
- **Primary Wallet**: `bc1q_peel_master_source_x99a7b1c3e4d`
- **Suspicious IP**: `198.51.100.42`
- **Transaction Count**: `8`
- **Transactions**: `tx_illicit_peel_000`, `tx_illicit_peel_001`, `tx_illicit_peel_002`, `tx_illicit_peel_003`, `tx_illicit_peel_004`, `tx_illicit_peel_005`, `tx_illicit_peel_006`, `tx_illicit_peel_007`

### Typology: `DUST_FLOOD`
- **Description**: Burst of 20 rapid sub-dust transactions (< 546 sats) to trace UTXO clustering
- **Primary Wallet**: `bc1q_dust_botnet_origin_f83b1a9c4e20`
- **Suspicious IP**: `203.0.113.99`
- **Transaction Count**: `20`
- **Transactions**: `tx_illicit_dust_000`, `tx_illicit_dust_001`, `tx_illicit_dust_002`, `tx_illicit_dust_003`, `tx_illicit_dust_004`, `tx_illicit_dust_005`, `tx_illicit_dust_006`, `tx_illicit_dust_007`, `tx_illicit_dust_008`, `tx_illicit_dust_009`, `tx_illicit_dust_010`, `tx_illicit_dust_011`, `tx_illicit_dust_012`, `tx_illicit_dust_013`, `tx_illicit_dust_014`, `tx_illicit_dust_015`, `tx_illicit_dust_016`, `tx_illicit_dust_017`, `tx_illicit_dust_018`, `tx_illicit_dust_019`

### Typology: `RAPID_DISPERSAL`
- **Description**: 1 input split into 25 simultaneous destination outputs (fan-out ratio 25:1)
- **Primary Wallet**: `bc1q_dispersal_launderer_w77d2f9a1b0c`
- **Suspicious IP**: `192.0.2.77`
- **Transaction Count**: `1`
- **Transactions**: `tx_illicit_dispersal_001`

### Typology: `FEE_ANOMALY_COLLUSION`
- **Description**: Whale 50.0 BTC transfer with 0.0 fee routed via Tor exit relay
- **Primary Wallet**: `bc1q_miner_siphon_collusion_000000fee`
- **Suspicious IP**: `185.220.101.5`
- **Transaction Count**: `1`
- **Transactions**: `tx_illicit_zerofee_collusion_001`

## 2. Illicit Entity Summary

### Target Suspicious Wallets:
- `bc1q_peel_master_source_x99a7b1c3e4d` (Peeling Chain Master Originator - peeling_chain)
- `bc1q_dust_botnet_origin_f83b1a9c4e20` (Dust Flood Controller - dust_flood)
- `bc1q_dispersal_launderer_w77d2f9a1b0c` (High Fan-Out Dispersal Source - rapid_dispersal)
- `bc1q_miner_siphon_collusion_000000fee` (Miner Collusion / Zero Fee Siphon - fee_anomaly)

### Suspicious Network Originating IPs:
- `198.51.100.42` (Bulletproof proxy originating sequential peeling hops [NL / AS1103])
- `203.0.113.99` (Anomalous relay host issuing rapid sub-dust transactions [RU / AS12389])
- `192.0.2.77` (Originating IP for large fan-out tumbler dispersal [DE / AS24940])
- `185.220.101.5` (Known Tor Exit Node relaying zero-fee whale transfer [IS / AS39351])

## 3. Sample Licit Transactions

First 15 normal transactions (should score LOW priority):
- `tx_licit_0000`
- `tx_licit_0001`
- `tx_licit_0002`
- `tx_licit_0003`
- `tx_licit_0004`
- `tx_licit_0005`
- `tx_licit_0006`
- `tx_licit_0007`
- `tx_licit_0008`
- `tx_licit_0009`
- `tx_licit_0010`
- `tx_licit_0011`
- `tx_licit_0012`
- `tx_licit_0013`
- `tx_licit_0014`
