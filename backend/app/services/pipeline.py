"""
Forensic Analysis Pipeline for Bitcoin Investigation Platform.

Executes complete forensic lifecycle:
1. Ingestion: Reads raw files (CSV, JSON, XML) via appropriate adapters.
2. Validation & Normalization: Applies parity, conservation, schema rules, and saves Parquet records.
3. Multi-Modal Correlation: Correlates network observations with Bitcoin transactions (exact TXID and time window).
4. GeoIP Enrichment: Offline geolocation using local MaxMind DB or fallback.
5. Entity Graph: Constructs multi-layer NetworkX graph (wallets, txs, IPs, ASNs) and serializes to graph.json.
6. Feature Extraction: Extracts transaction, wallet, network, and graph topological features.
7. Detectors:
   - Unsupervised Isolation Forest on normalized wallet feature matrix.
   - Deterministic AML behavior rules (burst, fan-out, fan-in, repeated values, dust, etc.).
   - Graph signals (degree, cycles, communities, betweenness).
   - Network signals (dispersion, port anomalies, relay bursts).
8. Priority Fusion Scoring: Weighted combination producing priority score (0-100) and severity tiers.
9. Evidence & Explanation: Compiles immutable evidence packs and deterministic explanations.
10. Persistence: Writes analytical Parquet tables, JSON & Markdown reports, and populates SQLite ORM.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.models import Alert, AnalysisRun, Dataset
from backend.app.schemas.dataset import ValidationReport
from backend.app.services.correlation import CorrelationEngine
from backend.app.services.detectors.behavior_rules import BehaviorRulesDetector
from backend.app.services.detectors.graph_signals import GraphSignalsDetector
from backend.app.services.detectors.isolation_forest import IsolationForestDetector
from backend.app.services.detectors.network_signals import NetworkSignalsDetector
from backend.app.services.evidence import EvidenceManager
from backend.app.services.explain import DeterministicExplainer
from backend.app.services.features import FeatureEngine
from backend.app.services.geoip import GeoIPService
from backend.app.services.graph_builder import EntityGraphBuilder
from backend.app.services.ingestion import get_adapter_for_format
from backend.app.services.report import ReportGenerator
from backend.app.storage.case_store import case_store
from backend.app.storage.parquet_store import parquet_store

logger = logging.getLogger(__name__)


class AnalysisPipeline:
    """
    End-to-end analytical pipeline orchestrator.
    Runs synchronously or as a background worker target.
    """

    def __init__(
        self,
        case_id: str,
        run_id: str,
        config: Optional[Dict[str, Any]] = None,
        db_session: Optional[Session] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ):
        self.case_id = case_id
        self.run_id = run_id
        self.config = config or {}
        self.db = db_session
        self.progress_callback = progress_callback
        self.case_paths = case_store.init_case_directory(case_id)

    def _update_progress(self, stage: str, progress: int):
        """Updates internal run state and calls optional callback."""
        logger.info(f"Run {self.run_id} - Stage: {stage} ({progress}%)")
        if self.progress_callback:
            try:
                self.progress_callback(stage, progress)
            except Exception as e:
                logger.warning(f"Error in progress callback: {e}")

        if self.db:
            try:
                run = self.db.query(AnalysisRun).filter(AnalysisRun.id == self.run_id).first()
                if run:
                    run.stage = stage
                    run.progress = progress
                    self.db.commit()
            except Exception as e:
                logger.warning(f"Error updating run stage in DB: {e}")

    def execute(self) -> Dict[str, Any]:
        """
        Executes all pipeline phases in strict forensic sequence.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        if self.db:
            try:
                run = self.db.query(AnalysisRun).filter(AnalysisRun.id == self.run_id).first()
                if run:
                    run.status = "running"
                    run.started_at = now_iso
                    self.db.commit()
            except Exception as e:
                logger.warning(f"Could not update initial run status in DB: {e}")

        try:
            # -------------------------------------------------------------
            # Stage 1: Ingestion & Validation
            # -------------------------------------------------------------
            self._update_progress("ingestion", 10)
            transactions, network_observations = self._ingest_case_datasets()

            # -------------------------------------------------------------
            # Stage 2: Normalization & Storage in Parquet
            # -------------------------------------------------------------
            self._update_progress("normalization", 25)
            self._persist_normalized_records(transactions, network_observations)

            # -------------------------------------------------------------
            # Stage 3: Multi-Modal Correlation & GeoIP Enrichment
            # -------------------------------------------------------------
            self._update_progress("correlation", 40)
            correlations, tx_status = self._correlate_and_enrich(transactions, network_observations)

            # -------------------------------------------------------------
            # Stage 4: Entity Graph Construction
            # -------------------------------------------------------------
            self._update_progress("graph_construction", 55)
            graph_builder, graph = self._build_entity_graph(transactions, network_observations, correlations)

            # -------------------------------------------------------------
            # Stage 5: Feature Extraction
            # -------------------------------------------------------------
            self._update_progress("feature_extraction", 70)
            features = self._extract_features(transactions, network_observations, graph)

            # -------------------------------------------------------------
            # Stage 6: Detection, Scoring & Evidence Synthesis
            # -------------------------------------------------------------
            self._update_progress("detection_and_scoring", 85)
            scored_alerts, graph_stats = self._run_detection_and_scoring(features, graph_builder, transactions)

            # -------------------------------------------------------------
            # Stage 7: Report Generation & Final Persistence
            # -------------------------------------------------------------
            self._update_progress("reporting_and_persistence", 95)
            reports = self._generate_reports_and_persist(scored_alerts, graph_stats)

            # Mark run completed
            self._update_progress("completed", 100)
            if self.db:
                try:
                    run = self.db.query(AnalysisRun).filter(AnalysisRun.id == self.run_id).first()
                    if run:
                        run.status = "completed"
                        run.completed_at = datetime.now(timezone.utc).isoformat()
                        self.db.commit()
                except Exception as e:
                    logger.warning(f"Could not update final run status in DB: {e}")

            return {
                "case_id": self.case_id,
                "run_id": self.run_id,
                "status": "completed",
                "alert_count": len(scored_alerts),
                "reports": reports,
            }

        except Exception as exc:
            logger.exception(f"Pipeline failed for case {self.case_id}, run {self.run_id}: {exc}")
            if self.db:
                try:
                    run = self.db.query(AnalysisRun).filter(AnalysisRun.id == self.run_id).first()
                    if run:
                        run.status = "failed"
                        run.stage = "failed"
                        run.error_code = type(exc).__name__
                        run.error_message = str(exc)
                        run.completed_at = datetime.now(timezone.utc).isoformat()
                        self.db.commit()
                except Exception as db_e:
                    logger.error(f"Failed to record failure in DB: {db_e}")
            raise exc

    def _ingest_case_datasets(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Reads all datasets associated with this case from the DB (or raw/ directory).
        Validates, normalizes, and classifies them into transactions and network records.
        """
        transactions: List[Dict[str, Any]] = []
        network_observations: List[Dict[str, Any]] = []

        raw_files = []
        if self.db:
            try:
                ds_records = self.db.query(Dataset).filter(Dataset.case_id == self.case_id).all()
                for ds in ds_records:
                    if os.path.exists(ds.source_path):
                        raw_files.append((ds.source_path, ds.kind, ds.format, ds))
            except Exception as e:
                logger.warning(f"Could not query datasets from DB: {e}")
        
        # If no DB records found, inspect raw/ directory directly
        if not raw_files:
            raw_dir = self.case_paths["raw"]
            if os.path.exists(raw_dir):
                for f in os.listdir(raw_dir):
                    fp = os.path.join(raw_dir, f)
                    if os.path.isfile(fp):
                        ext = Path(f).suffix.lstrip(".").lower()
                        raw_files.append((fp, "auto", ext, None))

        for file_path, kind, fmt, ds_model in raw_files:
            adapter = get_adapter_for_format(fmt)
            accepted, rejected, issues = adapter.validate_and_parse(file_path, kind=kind)

            # Update dataset row counts in SQLite if dataset record exists
            if ds_model and self.db:
                try:
                    ds_model.row_count = len(accepted) + len(rejected)
                    ds_model.accepted_rows = len(accepted)
                    ds_model.rejected_rows = len(rejected)
                    ds_model.warning_count = sum(1 for i in issues if i.issue_type == "warning")
                    self.db.commit()
                except Exception as e:
                    logger.warning(f"Could not update dataset stats: {e}")

            for rec in accepted:
                # Classify transaction vs network record
                if "txid" in rec and ("input_addresses" in rec or "output_addresses" in rec or "input_amounts" in rec):
                    transactions.append(rec)
                elif "src_ip" in rec or "dst_ip" in rec or "src_port" in rec:
                    network_observations.append(rec)
                elif "txid" in rec and not ("src_ip" in rec):
                    transactions.append(rec)
                else:
                    transactions.append(rec)

        return transactions, network_observations

    def _persist_normalized_records(
        self,
        transactions: List[Dict[str, Any]],
        network_observations: List[Dict[str, Any]],
    ):
        """
        Stores canonical, normalized records into case-level Parquet tables.
        """
        norm_dir = self.case_paths["normalized"]
        tx_path = os.path.join(norm_dir, "transactions.parquet")
        net_path = os.path.join(norm_dir, "network.parquet")

        # Serializing timestamps for parquet safety
        clean_txs = []
        for t in transactions:
            row = dict(t)
            if isinstance(row.get("timestamp"), datetime):
                row["timestamp"] = row["timestamp"].isoformat()
            clean_txs.append(row)

        clean_nets = []
        for n in network_observations:
            row = dict(n)
            if isinstance(row.get("timestamp"), datetime):
                row["timestamp"] = row["timestamp"].isoformat()
            clean_nets.append(row)

        parquet_store.write_records(clean_txs, tx_path)
        parquet_store.write_records(clean_nets, net_path)

    def _correlate_and_enrich(
        self,
        transactions: List[Dict[str, Any]],
        network_observations: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """
        Correlates transactions and network observations and applies GeoIP enrichment.
        """
        # 1. Offline GeoIP enrichment
        geoip = GeoIPService()
        for net in network_observations:
            src_ip = net.get("src_ip")
            if src_ip and not net.get("geo_country"):
                geo = geoip.lookup(src_ip)
                if geo.get("country"):
                    net["geo_country"] = geo["country"]
                if geo.get("asn"):
                    net["asn"] = geo["asn"]
        geoip.close()

        # 2. Multi-modal correlation
        corr_cfg = self.config.get("correlation", {})
        allow_temporal = corr_cfg.get("allow_temporal", settings.ALLOW_TEMPORAL_CORRELATION)
        window_seconds = corr_cfg.get("window_seconds", settings.CORRELATION_WINDOW_SECONDS)

        engine = CorrelationEngine(allow_temporal=allow_temporal, window_seconds=window_seconds)
        links, tx_status = engine.correlate(transactions, network_observations)

        # Persist correlation links to Parquet
        corr_dir = self.case_paths["correlated"]
        links_path = os.path.join(corr_dir, "network_transaction_links.parquet")
        parquet_store.write_records(links, links_path)

        return links, tx_status

    def _build_entity_graph(
        self,
        transactions: List[Dict[str, Any]],
        network_observations: List[Dict[str, Any]],
        correlations: List[Dict[str, Any]],
    ) -> Tuple[EntityGraphBuilder, Any]:
        """
        Constructs multi-layer NetworkX graph and exports graph.json and graph_stats.json.
        """
        builder = EntityGraphBuilder()
        graph = builder.build_from_records(transactions, network_observations, correlations)
        builder.export_files(self.case_paths["graph"])
        return builder, graph

    def _extract_features(
        self,
        transactions: List[Dict[str, Any]],
        network_observations: List[Dict[str, Any]],
        graph: Any,
    ) -> Dict[str, pd.DataFrame]:
        """
        Extracts transaction, wallet, network, and graph features,
        then writes them into features/*.parquet.
        """
        tx_df = FeatureEngine.compute_transaction_features(transactions)
        wallet_df = FeatureEngine.compute_wallet_features(transactions, network_observations)
        net_df = FeatureEngine.compute_network_features(network_observations)
        graph_df = FeatureEngine.compute_graph_features(graph)

        feat_dir = self.case_paths["features"]
        parquet_store.write_dataframe(tx_df, os.path.join(feat_dir, "transaction_features.parquet"))
        parquet_store.write_dataframe(wallet_df, os.path.join(feat_dir, "wallet_features.parquet"))
        parquet_store.write_dataframe(net_df, os.path.join(feat_dir, "network_features.parquet"))
        parquet_store.write_dataframe(graph_df, os.path.join(feat_dir, "graph_features.parquet"))

        return {
            "transactions": tx_df,
            "wallets": wallet_df,
            "network": net_df,
            "graph": graph_df,
        }

    def _run_detection_and_scoring(
        self,
        features: Dict[str, pd.DataFrame],
        graph_builder: EntityGraphBuilder,
        transactions: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Executes all 4 detectors, performs score fusion, builds deterministic explanations & evidence packs.
        """
        wallet_df = features["wallets"]
        graph_df = features["graph"]
        net_df = features["network"]
        graph_stats = graph_builder.get_stats()

        if wallet_df.empty:
            return [], graph_stats

        # 1. Unsupervised Anomaly Detection (Isolation Forest)
        ml_matrix, cols = FeatureEngine.build_ml_feature_matrix(wallet_df, graph_df)
        iso_cfg = self.config.get("isolation_forest", {})
        n_est = iso_cfg.get("n_estimators", 300)
        random_st = iso_cfg.get("random_state", 42)

        iso_detector = IsolationForestDetector(n_estimators=n_est, random_state=random_st)
        scored_iso = iso_detector.fit_predict(ml_matrix, cols)
        entity_deviations = iso_detector.get_feature_importances(scored_iso, cols)

        # 2. Deterministic Behavioral Rules
        rules_detector = BehaviorRulesDetector()

        # 3. Graph Signals
        graph_detector = GraphSignalsDetector()
        scored_graph = graph_detector.evaluate(wallet_df, graph_df)

        # 4. Network Signals
        net_detector = NetworkSignalsDetector()
        scored_net = net_detector.evaluate(wallet_df, net_df)

        # 5. Composite Scoring Fusion
        from backend.app.services.scoring import PriorityFusionScorer
        scorer = PriorityFusionScorer()

        # Calculate case medians for evidence comparisons
        case_medians = {}
        for col in cols:
            if col in scored_iso.columns:
                case_medians[col] = float(scored_iso[col].median())

        ev_manager = EvidenceManager()
        explainer = DeterministicExplainer()

        alerts: List[Dict[str, Any]] = []

        # Merge detector outputs by entity_id
        for _, w_row in wallet_df.iterrows():
            entity_id = w_row["entity_id"]
            addr = w_row["wallet_address"]

            # Anomaly score
            iso_match = scored_iso[scored_iso["entity_id"] == entity_id]
            a_score = float(iso_match.iloc[0]["anomaly_score"]) if not iso_match.empty else 0.0

            # Behavior rules & score
            rule_results = rules_detector.evaluate_wallet(w_row, transactions)
            b_score = rules_detector.compute_behavior_score(rule_results)
            triggered_rules = [r for r in rule_results if r.get("triggered")]

            # Graph score
            g_match = scored_graph[scored_graph["entity_id"] == entity_id]
            g_score = float(g_match.iloc[0]["graph_score"]) if not g_match.empty else 0.0

            # Network score & correlation strength
            n_match = scored_net[scored_net["entity_id"] == entity_id]
            n_score = float(n_match.iloc[0]["network_score"]) if not n_match.empty else 0.0
            corr_strength = float(n_match.iloc[0]["correlation_strength"]) if not n_match.empty else 0.0

            # Priority score & severity tier
            p_score, tier, components = scorer.compute_priority(
                anomaly_score=a_score,
                behavior_score=b_score,
                graph_score=g_score,
                network_score=n_score,
            )

            # Compile Evidence Pack
            top_devs = entity_deviations.get(entity_id, [])
            src_records = w_row.get("source_record_ids", [])
            if isinstance(src_records, set):
                src_records = list(src_records)

            evidence_pack = ev_manager.compile_evidence_pack(
                entity_id=entity_id,
                wallet_features=w_row.to_dict(),
                case_medians=case_medians,
                triggered_rules=triggered_rules,
                top_deviations=top_devs,
                source_record_ids=src_records,
            )

            # Generate Deterministic Explanation
            explanation_data = explainer.explain(
                entity_id=entity_id,
                priority_score=p_score,
                severity=tier,
                score_components=components,
                triggered_rules=triggered_rules,
                evidence_pack=evidence_pack,
                top_deviations=top_devs,
            )
            raw_reasons = explanation_data.get("top_reasons", []) or explanation_data.get("reasons", [])
            top_reasons_texts = [r.get("text", str(r)) for r in raw_reasons if isinstance(r, dict)]

            alerts.append(
                {
                    "run_id": self.run_id,
                    "entity_id": entity_id,
                    "wallet_address": addr,
                    "severity": tier,
                    "priority_score": p_score,
                    "anomaly_score": a_score,
                    "behavior_score": b_score,
                    "graph_score": g_score,
                    "network_score": n_score,
                    "correlation_strength": corr_strength,
                    "evidence_coverage": min(1.0, len(evidence_pack) / 5.0),
                    "reasons": top_reasons_texts,
                    "explanation": explanation_data,
                    "evidence_pack": evidence_pack,
                }
            )

        # Sort alerts descending by priority score
        alerts.sort(key=lambda x: x["priority_score"], reverse=True)
        return alerts, graph_stats

    def _generate_reports_and_persist(
        self,
        alerts: List[Dict[str, Any]],
        graph_stats: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Compiles JSON and Markdown reports into reports/ and persists Alert records to SQLite ORM.
        """
        report_dir = self.case_paths["reports"]

        # 1. Generate JSON Report
        json_report = ReportGenerator.generate_json_report(
            case_id=self.case_id,
            run_id=self.run_id,
            alerts=alerts,
            graph_stats=graph_stats,
            config=self.config,
        )
        json_path = os.path.join(report_dir, f"run_{self.run_id}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_report, f, indent=2)

        # 2. Generate Markdown Report
        md_text = ReportGenerator.generate_markdown_report(json_report)
        md_path = os.path.join(report_dir, f"run_{self.run_id}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_text)

        # 3. Persist Alert entities into SQLite DB
        if self.db:
            try:
                # Delete any existing alerts for this run to avoid duplicates
                self.db.query(Alert).filter(Alert.run_id == self.run_id).delete()

                alert_models = []
                for a in alerts:
                    am = Alert(
                        run_id=self.run_id,
                        entity_id=a["entity_id"],
                        severity=a["severity"],
                        priority_score=a["priority_score"],
                        anomaly_score=a["anomaly_score"],
                        behavior_score=a["behavior_score"],
                        graph_score=a["graph_score"],
                        network_score=a["network_score"],
                        correlation_strength=a.get("correlation_strength", 0.0),
                        evidence_coverage=a.get("evidence_coverage", 0.0),
                        reasons_json=json.dumps(a.get("reasons", [])),
                        explanation_json=json.dumps(a.get("explanation", {})),
                    )
                    alert_models.append(am)

                self.db.add_all(alert_models)
                self.db.commit()
            except Exception as e:
                logger.warning(f"Could not persist alerts to DB: {e}")
                self.db.rollback()

        return {
            "json_report": json_path,
            "markdown_report": md_path,
        }

