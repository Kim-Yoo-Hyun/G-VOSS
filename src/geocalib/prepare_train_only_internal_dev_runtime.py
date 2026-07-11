#!/usr/bin/env python3
"""Stage the frozen 117-scan internal-dev runtime using symlinks only."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--scans", type=Path, required=True)
    parser.add_argument("--final-scans", type=Path, required=True)
    parser.add_argument("--stage-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def read_scans(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def link(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        if target.resolve() == source.resolve():
            return
        target.unlink()
    elif target.exists():
        raise FileExistsError(f"refusing_to_replace:{target}")
    target.symlink_to(source.resolve(), target_is_directory=source.is_dir())


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    protocol_path = resolve(root, args.protocol)
    scans_path = resolve(root, args.scans)
    final_path = resolve(root, args.final_scans)
    stage = resolve(root, args.stage_root)
    out = resolve(root, args.out)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    scans, final_scans = read_scans(scans_path), set(read_scans(final_path))
    source = root / "local_dataset/SceneGraphFusion_code/3DSSG"
    scan_root = root / "local_dataset/3RScan/scans"
    subset = root / "local_dataset/3DSSG_subset"
    metadata = root / "local_dataset/3RScan/files"
    official_dev = read_scans(source / "files/cvpr/validation_scans.txt")
    validations = {
        "protocol_pre_internal_dev": protocol.get("status") == "protocol_frozen_before_strict_calibration_and_internal_dev_inference",
        "internal_dev_count_117_unique": len(scans) == 117 and len(set(scans)) == 117,
        "matches_official_validation_scans": set(scans) == set(official_dev),
        "zero_final_validation_overlap": not (set(scans) & final_scans),
        "all_raw_scan_dirs_present": all((scan_root / scan).is_dir() for scan in scans),
        "all_required_raw_files_present": all(
            all((scan_root / scan / name).is_file() for name in (
                "labels.instances.align.annotated.v2.ply", "labels.instances.annotated.v2.ply",
                "mesh.refined.v2.obj", "semseg.v2.json",
            ))
            for scan in scans
        ),
    }
    if not all(validations.values()):
        raise ValueError(f"internal_dev_stage_validation_failed:{validations}")
    runtime = stage / "runtime"
    raw = runtime / "raw_dev"
    files = runtime / "files"
    for scan in scans:
        link(scan_root / scan, raw / scan)
    link(metadata / "relationships.json", raw / "relationships.json")
    link(source / "files/3RScan.v2 Semantic Classes - Mapping.csv", files / "3RScan.v2 Semantic Classes - Mapping.csv")
    link(subset / "classes.txt", files / "classes160.txt")
    link(subset / "relationships.txt", files / "relationships.txt")
    for split in ("train", "validation", "test"):
        link(source / f"files/cvpr/{split}_scans.txt", files / "cvpr" / f"{split}_scans.txt")
    link(source / "configs", runtime / "configs")
    manifest = {
        "schema_version": "h001_train_only_internal_dev_runtime_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "internal_dev_runtime_staged",
        "counts": {"scans": len(scans), "symlinked_scan_dirs": len(scans)},
        "validations": validations,
        "inputs": {
            "protocol": {"path": relpath(root, protocol_path), "sha256": sha256_file(protocol_path)},
            "internal_dev_scans": {"path": relpath(root, scans_path), "sha256": sha256_file(scans_path)},
            "final_validation_scans": {"path": relpath(root, final_path), "sha256": sha256_file(final_path)},
            "official_validation_scans": {"path": relpath(root, source / "files/cvpr/validation_scans.txt"), "sha256": sha256_file(source / "files/cvpr/validation_scans.txt")},
        },
        "stage_root": relpath(root, stage),
        "note": "The runtime contains symlinks only; no raw 3RScan payload was duplicated.",
        "docker_command": "env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm train_only_internal_dev_stage",
    }
    write_json(out, manifest)
    print(json.dumps({"status": manifest["status"], "counts": manifest["counts"], "out": relpath(root, out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
