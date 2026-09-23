"""
Unit tests for storage layers: case_store, file_store, parquet_store.
"""
import os
import shutil
import tempfile
import pandas as pd
from backend.app.storage.case_store import CaseStore
from backend.app.storage.file_store import FileStore
from backend.app.storage.parquet_store import ParquetStore


def test_case_store():
    # Use temporary test dir under d:/Bitcoin-Investigation-platform/data/test_cases
    test_dir = "d:/Bitcoin-Investigation-platform/data/test_cases"
    store = CaseStore(base_data_dir=test_dir)
    case_id = "test_case_001"

    try:
        paths = store.init_case_directory(case_id)
        assert store.case_exists(case_id) is True
        for sub in CaseStore.SUBDIRS:
            assert sub in paths
            assert os.path.isdir(paths[sub])

        assert case_id in store.list_cases()
    finally:
        store.delete_case(case_id)
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir, ignore_errors=True)


def test_file_store():
    test_dir = "d:/Bitcoin-Investigation-platform/data/test_filestore"
    cs = CaseStore(base_data_dir=test_dir)
    fs = FileStore()
    fs.case_store = cs
    case_id = "test_fs_01"

    try:
        cs.init_case_directory(case_id)
        raw_content = b"header1,header2\nval1,val2"
        fpath, sha, size = fs.save_raw_upload(case_id, "data.csv", raw_content)

        assert os.path.exists(fpath)
        assert size == len(raw_content)
        assert len(sha) == 64
        assert fs.read_file_bytes(fpath) == raw_content
    finally:
        cs.delete_case(case_id)
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir, ignore_errors=True)


def test_parquet_store():
    test_path = "d:/Bitcoin-Investigation-platform/data/test_parquet/sample.parquet"
    data = [
        {"txid": "tx1", "inputs": ["W1"], "outputs": ["W2", "W3"], "amount": 1.5},
        {"txid": "tx2", "inputs": ["W2"], "outputs": ["W4"], "amount": 0.5},
    ]

    try:
        count = ParquetStore.write_records(data, test_path)
        assert count == 2
        assert os.path.exists(test_path)

        loaded = ParquetStore.read_records(test_path)
        assert len(loaded) == 2
        assert loaded[0]["txid"] == "tx1"
        assert loaded[0]["outputs"] == ["W2", "W3"]
        assert loaded[0]["amount"] == 1.5
    finally:
        if os.path.exists(os.path.dirname(test_path)):
            shutil.rmtree(os.path.dirname(test_path), ignore_errors=True)


def test_artifact_provenance_and_manifest():
    test_dir = "d:/Bitcoin-Investigation-platform/data/test_provenance"
    store = CaseStore(base_data_dir=test_dir)
    case_id = "test_case_prov_01"

    try:
        store.init_case_directory(case_id)
        sample_data = b"{\"event\": \"transaction\", \"txid\": \"12345\"}"
        meta = store.save_artifact(case_id, "reports", "test_report.json", sample_data)

        assert meta["filename"] == "test_report.json"
        assert meta["size_bytes"] == len(sample_data)
        assert len(meta["sha256"]) == 64

        # Verify integrity
        assert store.verify_artifact(meta["path"], meta["sha256"]) is True
        assert store.verify_artifact(meta["path"], "invalidhash" + "0" * 53) is False

        # Verify manifest
        manifest = store.get_case_manifest(case_id)
        assert manifest["exists"] is True
        assert manifest["artifact_count"] >= 1
        rel_paths = [a["relative_path"] for a in manifest["artifacts"]]
        assert any("reports/test_report.json" in p or "reports\\test_report.json" in p for p in rel_paths)
    finally:
        store.delete_case(case_id)
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir, ignore_errors=True)

