"""
Integration test for AnalysisPipeline and JobManager.
Verifies the full end-to-end execution:
- Dataset ingestion
- Normalization into Parquet
- Multi-modal correlation
- Graph building (graph.json)
- Feature extraction
- Detectors & scoring
- Report generation (JSON and Markdown)
- Persistence into SQLite ORM
"""

import json
import os
import shutil
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.base import Base
from backend.app.db.models import User, Case, Dataset, AnalysisRun, Alert
from backend.app.services.pipeline import AnalysisPipeline
from backend.app.services.job_manager import JobManager
from backend.app.storage.case_store import case_store
from backend.app.storage.parquet_store import parquet_store


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


def test_pipeline_end_to_end(test_db):
    case_id = "test_pipe_case_01"
    run_id = "test_pipe_run_01"

    # Setup directories
    case_paths = case_store.init_case_directory(case_id)

    try:
        # Create user and case in DB
        user = User(username="analyst_test", password_hash="dummy", role="analyst")
        test_db.add(user)
        test_db.commit()

        case = Case(id=case_id, name="Test Case Pipe", created_by=user.id)
        test_db.add(case)
        test_db.commit()

        # Create raw sample transaction CSV
        tx_csv_path = os.path.join(case_paths["raw"], "transactions.csv")
        with open(tx_csv_path, "w", encoding="utf-8") as f:
            f.write(
                "record_id,timestamp,txid,input_addresses,output_addresses,input_amounts,output_amounts,fee\n"
                "tx-1,2026-01-01T12:00:00Z,tx100,W_SRC,W_DST1;W_DST2,5.0,3.0;1.99,0.01\n"
                "tx-2,2026-01-01T12:00:05Z,tx101,W_DST1,W_DST3,3.0,2.99,0.01\n"
                "tx-3,2026-01-01T12:00:10Z,tx102,W_FAN,W_1;W_2;W_3;W_4;W_5;W_6;W_7;W_8;W_9;W_10;W_11,10.0,0.9;0.9;0.9;0.9;0.9;0.9;0.9;0.9;0.9;0.9;0.9,0.1\n"
            )

        # Create raw sample network observations JSON
        net_json_path = os.path.join(case_paths["raw"], "network.json")
        with open(net_json_path, "w", encoding="utf-8") as f:
            json.dump([
                {
                    "record_id": "net-1",
                    "timestamp": "2026-01-01T12:00:01Z",
                    "txid": "tx100",
                    "src_ip": "198.51.100.10",
                    "dst_ip": "192.0.2.1",
                    "src_port": 45000,
                    "dst_port": 8333,
                    "geo_country": "US",
                    "asn": "AS15169",
                },
                {
                    "record_id": "net-2",
                    "timestamp": "2026-01-01T12:00:11Z",
                    "txid": "tx102",
                    "src_ip": "203.0.113.5",
                    "dst_ip": "192.0.2.2",
                    "src_port": 50000,
                    "dst_port": 9050,  # Tor port
                    "geo_country": "RU",
                    "asn": "AS12345",
                },
            ], f)

        # Add datasets into DB
        ds1 = Dataset(case_id=case_id, name="transactions.csv", kind="transaction", format="csv", source_path=tx_csv_path, sha256="dummy1")
        ds2 = Dataset(case_id=case_id, name="network.json", kind="network", format="json", source_path=net_json_path, sha256="dummy2")
        test_db.add_all([ds1, ds2])
        test_db.commit()

        # Add analysis run
        run = AnalysisRun(id=run_id, case_id=case_id, status="queued", stage="queued", progress=0)
        test_db.add(run)
        test_db.commit()

        # Execute Pipeline
        pipeline = AnalysisPipeline(
            case_id=case_id,
            run_id=run_id,
            db_session=test_db,
        )
        result = pipeline.execute()

        assert result["status"] == "completed"
        assert result["alert_count"] > 0

        # Verify Parquet outputs
        norm_tx = parquet_store.read_records(os.path.join(case_paths["normalized"], "transactions.parquet"))
        assert len(norm_tx) == 3
        norm_net = parquet_store.read_records(os.path.join(case_paths["normalized"], "network.parquet"))
        assert len(norm_net) == 2

        # Verify features Parquet
        w_feats = parquet_store.read_dataframe(os.path.join(case_paths["features"], "wallet_features.parquet"))
        assert not w_feats.empty

        # Verify graph.json exists
        graph_file = os.path.join(case_paths["graph"], "graph.json")
        assert os.path.exists(graph_file)
        with open(graph_file, "r", encoding="utf-8") as gf:
            graph_data = json.load(gf)
            assert "elements" in graph_data

        # Verify report generation
        json_report_file = os.path.join(case_paths["reports"], f"run_{run_id}.json")
        md_report_file = os.path.join(case_paths["reports"], f"run_{run_id}.md")
        assert os.path.exists(json_report_file)
        assert os.path.exists(md_report_file)

        # Verify DB updates
        updated_run = test_db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        assert updated_run.status == "completed"
        assert updated_run.progress == 100

        db_alerts = test_db.query(Alert).filter(Alert.run_id == run_id).all()
        assert len(db_alerts) > 0
        for alert in db_alerts:
            assert alert.severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
            assert 0.0 <= alert.priority_score <= 100.0

    finally:
        case_store.delete_case(case_id)


def test_job_manager_execution():
    case_id = "test_jm_case_02"
    run_id = "test_jm_run_02"

    case_paths = case_store.init_case_directory(case_id)
    try:
        # Create a small dataset directly in raw/
        tx_csv = os.path.join(case_paths["raw"], "txs.csv")
        with open(tx_csv, "w", encoding="utf-8") as f:
            f.write(
                "record_id,timestamp,txid,input_addresses,output_addresses,input_amounts,output_amounts,fee\n"
                "r-1,2026-01-01T10:00:00Z,tx-simple,W_A,W_B,1.0,0.99,0.01\n"
            )

        jm = JobManager(max_workers=1)
        # Verify job submission
        submitted = jm.submit_job(case_id=case_id, run_id=run_id)
        assert submitted is True

        # Wait for thread pool to finish
        jm.executor.shutdown(wait=True)
        assert not jm.is_running(run_id)

        # Verify output files generated
        report_json = os.path.join(case_paths["reports"], f"run_{run_id}.json")
        assert os.path.exists(report_json)
    finally:
        case_store.delete_case(case_id)

