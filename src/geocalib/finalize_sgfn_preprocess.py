#!/usr/bin/env python3
"""Create the point-only SGFN eval index and audit official preprocessing."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import h5py
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--preprocessed", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--official-scans", type=Path)
    parser.add_argument("--expected-scans", type=int, default=157)
    parser.add_argument("--ready-status", default="sgfn_preprocess_ready")
    parser.add_argument("--docker-service", default="sgfn_preprocess_finalize")
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    pre = resolve(root, args.preprocessed)
    out = resolve(root, args.out)
    required = [pre / name for name in ("relationships.h5", "args.json", "classes.txt", "relationships.txt", "scan_ids.txt")]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing_preprocessed_inputs:{missing}")
    source_h5 = pre / "relationships.h5"
    filtered_h5 = pre / "filtered_scans_detection.h5"
    scan_nodes: dict[str, int] = {}
    scan_relations: dict[str, int] = {}
    with h5py.File(source_h5, "r") as source, h5py.File(filtered_h5, "w") as target:
        for scan_id in sorted(source.keys()):
            raw = source[scan_id][0].decode()
            data = ast.literal_eval(raw)
            nodes = sorted(int(key) for key in data["nodes"].keys())
            payload = {"kf_indices": [], "obj_indices": nodes}
            target.create_dataset(
                scan_id,
                data=np.array([str(payload)], dtype="S"),
                compression="gzip",
            )
            scan_nodes[scan_id] = len(nodes)
            scan_relations[scan_id] = len(data["relationships"])
    official_scans_path = resolve(root, args.official_scans) if args.official_scans else (
        root / "local_dataset/SceneGraphFusion_code/3DSSG/files/cvpr/test_scans.txt"
    )
    official_scans = {
        line.strip()
        for line in official_scans_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    generated = set(scan_nodes)
    validations = {
        "generated_scan_count_expected": len(generated) == args.expected_scans,
        "generated_scans_equal_frozen_scope": generated == official_scans,
        "all_scans_have_at_least_two_nodes": all(count >= 2 for count in scan_nodes.values()),
        "class_count_160": len((pre / "classes.txt").read_text(encoding="utf-8").splitlines()) == 160,
        "relation_file_contains_27_entries_including_none": len((pre / "relationships.txt").read_text(encoding="utf-8").splitlines()) == 27,
    }
    manifest = {
        "schema_version": "h001_sgfn_preprocess_audit_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": args.ready_status if all(validations.values()) else "blocked_sgfn_preprocess_audit",
        "counts": {
            "scans": len(generated),
            "nodes": sum(scan_nodes.values()),
            "source_relationship_rows": sum(scan_relations.values()),
            "min_nodes_per_scan": min(scan_nodes.values()),
            "max_nodes_per_scan": max(scan_nodes.values()),
        },
        "validations": validations,
        "inputs": {"relationships_h5": relpath(root, source_h5), "sha256": sha256_file(source_h5)},
        "outputs": {"filtered_h5": relpath(root, filtered_h5), "sha256": sha256_file(filtered_h5)},
        "compatibility_note": "official point-only SGFN loader incorrectly requires proposals.h5 while building its filter; this index preserves every generated 3D node and is used only because load_images=false",
        "official_scans": {"path": relpath(root, official_scans_path), "sha256": sha256_file(official_scans_path)},
        "docker_command": f"UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm {args.docker_service}",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "counts": manifest["counts"], "out": relpath(root, out)}))
    return 0 if manifest["status"] == args.ready_status else 2


if __name__ == "__main__":
    raise SystemExit(main())
