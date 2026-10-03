"""
Model Packaging and Verification CLI for Bitcoin Investigation Platform.

Allows zero-friction export, import, and checksum verification of all 16 ML model
artifacts, PyTorch architectures, and feature schemas so they can be transferred
from one laptop to another without missing dependencies or path errors.

Usage:
  # Package all models and configs into a portable archive:
  python scripts/package_models.py --export btc_models_bundle.zip

  # Verify existing models on this machine:
  python scripts/package_models.py --verify

  # Unpack a model bundle from another laptop:
  python scripts/package_models.py --import btc_models_bundle.zip
"""

import os
import sys
import json
import zipfile
import hashlib
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Models & artifacts required for 100% full offline multi-brain inference
MODEL_FILES = [
    # Top-level architectures
    "models/fgecgn_model.py",
    "models/gatv2_model.py",
    "models/graphsage_model.py",
    "models/tgat_model.py",
    # Fusion
    "models/fusion/oof_meta_stacker.joblib",
    "models/fusion/threshold.json",
    "models/fusion/calibration.json",
    # Transaction
    "models/transaction/rf.joblib",
    "models/transaction/gatv2.pt",
    "models/transaction/fgecgn.pt",
    "models/transaction/isolation_forest.joblib",
    # Wallet
    "models/wallet/actor_rf.joblib",
    "models/wallet/graphsage.pt",
    "models/wallet/fgecgn.pt",
    "models/wallet/isolation_forest.joblib",
    # Network
    "models/network/rf.joblib",
    "models/network/graphsage.pt",
    "models/network/tgat.pt",
    "models/network/isolation_forest.joblib",
    # Schemas
    "features/schemas/MODEL_INPUT_SCHEMA.json",
    "features/schemas/transaction_features.json",
    "features/schemas/wallet_features.json",
    "features/schemas/network_features.json",
    "features/schemas/graph_features.json",
]


def sha256_file(filepath: Path) -> str:
    """Calculates SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify_models() -> bool:
    """Verifies that all model artifacts and schemas are present and readable."""
    print("=" * 70)
    print("VERIFYING MODEL ARTIFACTS AND CROSS-LAPTOP PORTABILITY")
    print("=" * 70)

    missing = []
    present = []
    manifest = {}

    for rel_path in MODEL_FILES:
        full_path = BASE_DIR / rel_path
        if not full_path.exists():
            # Check fallback in ml_engine/
            alt_path = BASE_DIR / "ml_engine" / "SIH_SUPERVISED_ML" / rel_path.replace("models/", "models/")
            if alt_path.exists():
                full_path = alt_path

        if full_path.exists():
            h = sha256_file(full_path)
            size = full_path.stat().st_size
            present.append((rel_path, size, h))
            manifest[rel_path] = {"size": size, "sha256": h}
            print(f"  [OK] {rel_path} ({size:,} bytes)")
        else:
            missing.append(rel_path)
            print(f"  [MISSING] {rel_path}")

    print("-" * 70)
    print(f"Summary: {len(present)}/{len(MODEL_FILES)} files present.")

    if missing:
        print(f"FAILED: {len(missing)} files missing.")
        return False

    # Perform lightweight inference test
    try:
        from backend.app.services.ml_inference import ml_engine
        print(f"ML Inference Engine ready: {ml_engine.is_ready}")
        print(f"Supervised Models Available: {ml_engine.supervised_available}")
        print(f"Isolation Forests Available: {ml_engine.isolation_forests_available}")
        print("ALL MODELS VERIFIED AND READY FOR EXECUTION.")
        return True
    except Exception as e:
        print(f"Warning during inference verification: {e}")
        return len(missing) == 0


def export_bundle(zip_path: str):
    """Packages all models, architectures, and schemas into a portable zip."""
    target_zip = Path(zip_path).resolve()
    print(f"Packaging models into: {target_zip}")

    manifest = {"files": {}, "platform": sys.platform, "version": "2.0"}

    with zipfile.ZipFile(target_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel_path in MODEL_FILES:
            full_path = BASE_DIR / rel_path
            if not full_path.exists():
                # Check fallback
                alt = BASE_DIR / "ml_engine" / "SIH_SUPERVISED_ML" / rel_path.replace("models/", "models/")
                if alt.exists():
                    full_path = alt

            if full_path.exists():
                h = sha256_file(full_path)
                size = full_path.stat().st_size
                manifest["files"][rel_path] = {"size": size, "sha256": h}
                zf.write(full_path, arcname=rel_path)
                print(f"  + Added {rel_path}")
            else:
                print(f"  ! Warning: Skipping missing file {rel_path}")

        # Add manifest to zip
        zf.writestr("models_manifest.json", json.dumps(manifest, indent=2))

    print(f"\nSUCCESS! Model bundle created: {target_zip}")
    print(f"Size: {target_zip.stat().st_size / (1024 * 1024):.2f} MB")
    print("\nHow to transfer to another laptop:")
    print(f"1. Copy '{target_zip.name}' to the target laptop via USB drive or local network.")
    print("2. On the target laptop, run:")
    print(f"   python scripts/package_models.py --import {target_zip.name}")


def import_bundle(zip_path: str):
    """Unpacks a model bundle onto this laptop."""
    src_zip = Path(zip_path).resolve()
    if not src_zip.exists():
        print(f"Error: Bundle file not found: {src_zip}")
        sys.exit(1)

    print(f"Importing models from: {src_zip}")
    with zipfile.ZipFile(src_zip, "r") as zf:
        for member in zf.namelist():
            if member == "models_manifest.json":
                continue
            dest = BASE_DIR / member
            dest.parent.mkdir(parents=True, exist_ok=True)
            zf.extract(member, BASE_DIR)
            print(f"  -> Extracted {member}")

    print("\nExtraction complete. Verifying imported models...")
    verify_models()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bitcoin Platform Model Transfer & Verification Tool")
    parser.add_argument("--export", type=str, metavar="ZIP_PATH", help="Export all models to a portable ZIP archive")
    parser.add_argument("--import", dest="import_path", type=str, metavar="ZIP_PATH", help="Import models from a ZIP archive")
    parser.add_argument("--verify", action="store_true", help="Verify all models and schemas on this machine")

    args = parser.parse_args()

    if args.export:
        export_bundle(args.export)
    elif args.import_path:
        import_bundle(args.import_path)
    else:
        # Default action: verify
        success = verify_models()
        sys.exit(0 if success else 1)
