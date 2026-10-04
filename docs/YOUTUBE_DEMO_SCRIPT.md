# YouTube Video Presentation Script: Bitcoin Forensic Investigation Platform

**Target Duration:** 5 to 7 Minutes  
**Tone:** Confident, Authoritative, Cyber Forensics & Engineering Focused  
**Target Audience:** Hackathon Evaluators, Law Enforcement / AML Analysts, Technical Judges  

---

## [0:00 - 0:45] Scene 1: The Hook & The Problem Statement
**Visual on Screen:**  
- Full screen title card or cinematic screen capture showing cryptocurrency laundering headlines (Ransomware, Mixer services, Darknet markets).  
- Cut to the **Active Dashboard** (`http://127.0.0.1:8000`) with the dark cyber-forensics theme visible.

**Voiceover (Speaker):**  
> *"Bitcoin’s pseudonymous, decentralized architecture makes it the transaction rail of choice for cybercrime — from ransomware syndicates and darknet narcotics to high-velocity capital flight. Traditional forensic tools often treat the Bitcoin blockchain as an isolated ledger, ignoring the critical network-layer telemetry — IP addresses, autonomous system numbers, and P2P propagation timing — that actually connects digital signatures to physical actors.*
>
> *Today, we present **CipherTrace AML Forensics**, an end-to-end, completely air-gapped, offline investigative intelligence platform that bridges on-chain transaction flows with network-layer telemetry, powered by graph analytics, behavioral heuristics, and multi-domain Machine Learning."*

---

## [0:45 - 1:45] Scene 2: The Architecture & 100% Offline Capability
**Visual on Screen:**  
- Zoom in on the top-right banner showing **`AIR-GAPPED`** and **`HEURISTIC ENGINE READY`**.  
- Click on the **Dataset Ingestion** tab. Show the 4 canonical file dropzones: `transactions.csv`, `inputs.csv`, `outputs.csv`, and `network.csv`.

**Voiceover (Speaker):**  
> *"Our platform was engineered with strict operational security in mind. It runs **100% offline** on Linux or Windows environments with zero third-party cloud dependencies or external API calls.*
>
> *Here in the **Dataset Ingestion Suite**, investigators ingest bulk canonical metadata:
> 1. On-chain transactions with block timestamps and fees.
> 2. Inputs (`vin`) and Outputs (`vout`) with addresses and satoshi values.
> 3. Network telemetry logs containing peer IP addresses, ports, and relay timestamps.
>
> Rather than relying on cloud lookups, our ingestion pipeline embeds a local MaxMind GeoLite2 reader, resolving autonomous systems and geographic regions directly on disk with zero external data leakage."*

---

## [1:45 - 2:45] Scene 3: Multi-Modal Correlation & Entity Graph
**Visual on Screen:**  
- Click on the **Graph Canvas** tab.  
- Show the React Flow directed graph canvas (`@xyflow/react`).  
- Pan across wallets connected to transactions and IP nodes. Click on a node to open the **Node Inspector Drawer**.

**Voiceover (Speaker):**  
> *"Once ingested, the system executes two core analytical stages:
>
> First is **Multi-Modal Correlation**. The engine reconciles network observations against Bitcoin transactions using two strategies: exact TXID matching and microsecond-level temporal window proximity correlation. Every single link maintains cryptographic provenance with recorded `time_delta` values.
>
> Second, our engine builds a **Multi-Layer Directed Entity Graph** using NetworkX. As you see on the screen, wallets, transactions, IPs, and ASNs are interconnected through typed edges like `SPENT_FROM`, `SENT_TO`, and `RELAYED_BY`.
>
> Investigators can visually trace money movement, identify high-degree hub nodes, and inspect PageRank centrality directly from this interactive canvas."*

---

## [2:45 - 4:00] Scene 4: Detection Engine (ML + Deterministic AML Rules)
**Visual on Screen:**  
- Click on the **Alerts & Evidence** tab.  
- Hover over the 5 **Heuristic Stream Switcher Pills**:
  `[🎯 Composite Ensemble | 🧠 Supervised ML | 🔍 Unsupervised (IF) | 🕸️ Graph Flow | ⚖️ Custom Rules]`  
- Click through each pill to show the table dynamically resort by that specific score component.

**Voiceover (Speaker):**  
> *"Now let's examine the intelligence engine. Our platform does not rely solely on simple if-else filters. It deploys a **4-Stream Composite Ensemble**:
>
> 1. **Unsupervised Anomaly Detection:** An offline scikit-learn Isolation Forest model trained across multidimensional feature matrices (velocity, fan-out ratios, and entropy) to catch zero-day laundering patterns without requiring pre-existing labels.
> 2. **Supervised Multi-Brain Stack:** A deep architecture including Random Forests, Graph Neural Networks (GATv2 and GraphSAGE), and a meta-stacker.
> 3. **Graph Topological Signals:** Detecting circular money hops, structural bridges, and community densities.
> 4. **Deterministic AML Typologies:** Hardened forensic rules targeting classic criminal behaviors:
>    - Peeling Chains: Stripping small payments while forwarding change across sequential hops.
>    - Dust Attacks: Micro-transfers below dust limits designed to de-anonymize wallet clusters.
>    - Rapid Dispersal: Sudden 1-to-many fan-out fund splits.
>    - And Zero-Fee Collusion: Direct miner-to-launderer agreements bypass standard mempool fees.
>
> The **Priority Fusion Scorer** synthesizes these streams into a transparent composite risk score from 0 to 100%, categorizing each lead into Critical, High, Medium, or Low severity."*

---

## [4:00 - 5:15] Scene 5: Evidence Drawer & Explainability (No Black Box)
**Visual on Screen:**  
- In the Alerts Table, click on the Action icon on the #1 ranked alert (`tx_illicit_zerofee_collusion_001` or the top wallet `bc1q_dust_botnet_origin_...`).  
- The **Evidence & Audit Drawer** slides out from the right.  
- Show the 5 separate score meters, the Natural Language Narrative, the **Top Deviation Reasons**, and the **Raw Source Records**.

**Voiceover (Speaker):**  
> *"In criminal investigations, a black-box model is legally inadmissible. An investigator must be able to justify *why* an entity was flagged in a court of law.
>
> When we open the **Evidence Drawer** for this flagged entity:
> - Notice the transparent score breakdown: We see exactly how much risk came from the Isolation Forest versus Behavioral Rules versus Graph Centrality.
> - Below that, our **Deterministic Explainer** produces an audit narrative with zero hallucinations: it compares the observed transaction value and rate against baseline case medians.
> - Finally, it cites the exact raw `source_record_ids` and transaction hashes, preserving an unbreakable chain of custody."*

---

## [5:15 - 5:45] Scene 6: Custom Investigator Rules & Court Reports
**Visual on Screen:**  
- Click the **Rules Heuristics** button at top right to open the **Rules Manager Modal**.  
- Show creating a rule (e.g. `fan_out > 10`).  
- Click on the **Forensic Reports** tab. Show the formatted Markdown report and click the **Export JSON / Markdown** buttons.

**Voiceover (Speaker):**  
> *"Investigators can also define their own custom operational rules on the fly using the **Rules Manager** — dynamically weighting thresholds for specific ongoing operations.
>
> And when the case is ready for prosecution, the **Forensic Reports** tab auto-compiles court-ready dossiers in both machine-readable JSON and human-readable Markdown with full case hash integrity."*

---

## [5:45 - 6:30] Scene 7: Conclusion & Wrap-Up
**Visual on Screen:**  
- Switch back to the main overview showing the metric cards and the graph canvas.  
- End screen showing project repository link, architecture summary, and team credits.

**Voiceover (Speaker):**  
> *"To summarize: Our prototype delivers a complete, air-gapped forensic solution:
> - Bulk ingestion across CSV, JSON, and XML.
> - Multi-modal network-to-blockchain correlation.
> - Interactive React Flow money-flow topology.
> - Hybrid ML and deterministic AML detection.
> - And 100% explainable, court-ready investigative leads.
>
> Thank you for watching. The source code, test suites, and sample datasets are available in our project repository."*

