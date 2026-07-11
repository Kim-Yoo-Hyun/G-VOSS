#!/usr/bin/env python3
"""Validate and merge one-scene FROSS shards into the frozen source artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_replicassg_fross_source_merge_v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--shard-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--weight-zip", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--docker-service", default="replicassg_merge_shards")
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    protocol_path = resolve(root, args.protocol)
    shard_dir = resolve(root, args.shard_dir)
    output = resolve(root, args.output)
    manifest_path = resolve(root, args.manifest)
    weight_zip = resolve(root, args.weight_zip)
    artifact_dir = resolve(root, args.artifact_dir)
    if output.exists() or manifest_path.exists():
        raise FileExistsError("merged_source_or_manifest_already_exists")
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol.get("status") != "frozen_before_source_prediction":
        raise ValueError("prospective_protocol_not_frozen")
    expected_output = resolve(root, Path(protocol["semantic_source"]["source_prediction_path"]))
    if output.resolve() != expected_output.resolve():
        raise ValueError("merged_output_differs_from_frozen_source_path")

    scans = list(protocol["dataset"]["test_scans"])
    expected_shards = {f"{scan}.pkl" for scan in scans}
    observed_shards = {path.name for path in shard_dir.glob("*.pkl")}
    if observed_shards != expected_shards:
        raise ValueError(
            f"shard_set_mismatch:missing={sorted(expected_shards-observed_shards)}:"
            f"extra={sorted(observed_shards-expected_shards)}"
        )
    merged: dict[str, Any] = {}
    shard_records = []
    for scan in scans:
        path = shard_dir / f"{scan}.pkl"
        with path.open("rb") as handle:
            payload = pickle.load(handle)
        if set(payload) != {scan}:
            raise ValueError(f"shard_payload_scan_mismatch:{scan}:{sorted(payload)}")
        prediction = payload[scan]
        required = {"pcd", "cls", "edge_index", "edge_cls"}
        if not required.issubset(prediction):
            raise ValueError(f"shard_schema_missing:{scan}:{sorted(required-set(prediction))}")
        merged[scan] = prediction
        shard_records.append({"scan_id": scan, "path": relpath(root, path), "sha256": sha256(path)})
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as handle:
        pickle.dump(merged, handle)
    artifact_names = (
        "config.json", "checkpoints/epoch=23-validation_loss=4.60.ckpt",
        "rt-detr.onnx", "egtr-head.onnx", "rt-detr.engine", "egtr-head.engine",
        "h001_engine_manifest.json",
    )
    runtime_artifacts = {}
    for name in artifact_names:
        path = artifact_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"missing_source_runtime_artifact:{path}")
        runtime_artifacts[name] = {
            "path": relpath(root, path), "sha256": sha256(path), "bytes": path.stat().st_size,
        }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": "frozen_source_prediction_ready",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "execution_equivalence": (
            "Each official test scene uses the identical frozen FROSS command and complete "
            "official trajectory; scene-wise execution changes storage scheduling only."
        ),
        "counts": {"scenes": len(scans), "shards": len(shard_records)},
        "shards": shard_records,
        "inputs": {
            "protocol": {"path": relpath(root, protocol_path), "sha256": sha256(protocol_path)},
            "weight_zip": {"path": relpath(root, weight_zip), "sha256": sha256(weight_zip)},
        },
        "runtime_artifacts": runtime_artifacts,
        "output": {"path": relpath(root, output), "sha256": sha256(output)},
        "docker_command": f"env UID=$(id -u) GID=$(id -g) docker compose -f configs/fross/compose.yaml run --rm {args.docker_service}",
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "counts": manifest["counts"], "output_sha256": manifest["output"]["sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
